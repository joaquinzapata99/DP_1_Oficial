import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from sqlalchemy import create_engine, text
import unicodedata

# Enhanced Database Configuration
DB_CONFIG = {
    "host": "postgres_container",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

def normalize_text(text):
    """
    Normalize text by removing accents and converting to lowercase
    """
    if isinstance(text, str):
        return unicodedata.normalize('NFKD', text.lower()).encode('ASCII', 'ignore').decode('ASCII')
    return text

def create_sqlalchemy_engine():
    """Create SQLAlchemy engine using pg8000 dialect"""
    connection_string = f"postgresql+pg8000://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(
        connection_string, 
        pool_size=10,  # Maximum number of connections in the pool
        max_overflow=20,  # Allow additional connections temporarily
        pool_timeout=30,  # Wait time for a connection to become available
        pool_recycle=1800  # Recycle connections after 30 minutes
    )

def fetch_data(table_name):
    """Fetch data from PostgreSQL with enhanced error handling"""
    try:
        # Use SQLAlchemy engine for connection
        engine = create_sqlalchemy_engine()

        # Get column names from the table
        with engine.connect() as conn:
            columns_query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
            result = conn.execute(columns_query)
            columns = result.fetchall()

        # Detect geometry columns
        geo_columns = [col[0] for col in columns if 'geo' in col[0].lower() or 'shape' in col[0].lower() or 'point' in col[0].lower()]

        if not geo_columns:
            st.error(f"No geometry column found in table {table_name}")
            return None

        # Read data with the detected geometry column
        geo_col = geo_columns[0]  # Use the first valid geometry column
        query = text(f"SELECT * FROM {table_name} LIMIT 500;")

        # Read data using GeoPandas
        with engine.connect() as conn:
            data = gpd.read_postgis(query, conn, geom_col=geo_col)
        
        # Normalize some columns for consistent filtering
        if 'regimen' in data.columns:
            data['regimen_normalized'] = data['regimen'].apply(normalize_text)
        
        st.success(f"Successfully read data using geometry column: {geo_col}")
        return data

    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return None

def filter_metro_within_barrios(metro_data, barrios_data):
    """Filter metro stations to only those within the selected barrios"""
    try:
        # Combine all polygons of selected districts
        combined_barrios_geometry = barrios_data.unary_union

        # Filter metro stations within the selected districts
        metro_data_filtered = metro_data[metro_data.geometry.within(combined_barrios_geometry)]
        return metro_data_filtered
    except Exception as e:
        st.error(f"Error filtering metro stations within barrios: {e}")
        return metro_data

def filter_centers_within_barrios(centers_data, barrios_data, metro_data=None, filter_metro_stations_only=False):
    """
    Filter educational centers based on barrios and optional metro station requirement
    """
    try:
        # Combine all polygons of selected districts
        combined_barrios_geometry = barrios_data.unary_union

        # Filter centers within the selected districts
        centers_in_barrios = centers_data[centers_data.geometry.within(combined_barrios_geometry)]

        # If metro station filtering is enabled
        if filter_metro_stations_only and metro_data is not None:
            # Filter districts that have metro stations
            barrios_with_metro = barrios_data[barrios_data.geometry.intersects(metro_data.geometry.unary_union)]
            
            # Further filter centers to only those in districts with metro stations
            centers_filtered = centers_in_barrios[
                centers_in_barrios.geometry.within(barrios_with_metro.unary_union)
            ]
            return centers_filtered
        
        return centers_in_barrios

    except Exception as e:
        st.error(f"Error filtering educational centers: {e}")
        return centers_data

def create_map(metro_data, barrios_data, centros_data, filter_metro_stations_only, filtered_barrios_data, show_metro_stations, selected_school_types):
    """Create an interactive Folium map"""
    m = folium.Map(location=[39.4699, -0.3763], zoom_start=12)  

    # Color schemes
    metro_color = 'red'
    barrios_color = 'blue'
    selected_color = 'green'
    
    # School type colors
    school_colors = {
        'publico': 'purple',
        'concertado': 'orange',
        'privado': 'blue'
    }

    # Normalize selected school types
    normalized_selected_types = [normalize_text(st) for st in selected_school_types]

    # Plot metro stations (only if the option is enabled)
    if show_metro_stations:
        for _, row in metro_data.iterrows():
            try:
                geo_col = [col for col in row.index if 'geo' in col.lower() or 'point' in col.lower()][0]
                point = row[geo_col]
                
                if not point.is_empty:
                    folium.CircleMarker(
                        location=[point.y, point.x],
                        radius=5,
                        popup=row.get("name", "Metro Station"),
                        color=metro_color,
                        fill=True,
                        fillColor=metro_color
                    ).add_to(m)
            except Exception as e:
                st.warning(f"Error plotting metro station: {e}")

    # Plot educational centers
    for _, row in centros_data.iterrows():
        try:
            # Use normalized comparison for school types
            if row['regimen_normalized'] in normalized_selected_types:
                point = row['geo_point']
                
                if not point.is_empty:
                    folium.CircleMarker(
                        location=[point.y, point.x],
                        radius=5,
                        popup=f"{row.get('nombre', 'Centro Educativo')} ({row['regimen']})",
                        color=school_colors.get(normalize_text(row['regimen']), 'gray'),
                        fill=True,
                        fillColor=school_colors.get(normalize_text(row['regimen']), 'gray')
                    ).add_to(m)
        except Exception as e:
            st.warning(f"Error plotting educational center: {e}")

    # Plot barrios (districts) from filtered data
    for _, row in filtered_barrios_data.iterrows():
        try:
            geo_col = [col for col in row.index if 'geo' in col.lower() or 'shape' in col.lower()][0]
            geometry = row[geo_col]
            
            # Get the neighborhood name using 'nombre' column
            neighborhood_name = row.get("nombre", "Barrio sin nombre")
            
            if geometry.geom_type in ['Polygon', 'MultiPolygon']:
                folium.GeoJson(
                    geometry.__geo_interface__,
                    popup=row.get("nombre", "Barrio"),
                    tooltip=neighborhood_name,
                    style_function=lambda feature: {
                        'fillColor': selected_color,
                        'fillOpacity': 0.5,
                        'weight': 1,
                        'color': selected_color
                    }
                ).add_to(m)
        except Exception as e:
            st.warning(f"Error plotting barrio: {e}")

    return m

def main():
    st.set_page_config(
        page_title="Tindralencia 🔥", 
        page_icon=":metro:", 
        layout="wide"
    )

    st.title("Haz match con tu nuevo hogar 🌇")
    st.markdown("""
    ### Mapa interactivo parguela
    Mira a ver cual es tu sitio, que te veo desubicado **pinpin**
    """)

    with st.spinner('Fetching geographic data...'):
        metro_data = fetch_data("paradas_metro")
        barrios_data = fetch_data("barrios_valencia")
        centros_data = fetch_data("centros_educativos")

    if metro_data is not None and barrios_data is not None and centros_data is not None:
        # Debug: Print unique school types before filtering
        print("Unique school types (normalized):")
        print(centros_data['regimen_normalized'].unique())

        st.sidebar.subheader("Personalize your map:")
        
        # Checkbox for showing/hiding metro stations
        show_metro_stations = st.sidebar.checkbox("Show Metro Stations", value=True)
        
        st.sidebar.markdown("### ¿Usas el metro frecuentemente 🚇?")
        response = st.sidebar.radio("Choose an option:", ("Yes", "No"))
        filter_metro_stations_only = response == "Yes"

        st.sidebar.markdown("### ¿Cuánto valoras la seguridad de tu barrio? 🚔")
        security_value = st.sidebar.slider("Select security value:", 0, 3, 0)
        
        # School type selection with normalization
        st.sidebar.markdown("### Tipos de Centros Educativos 🏫")
        selected_school_types = st.sidebar.multiselect(
            "Selecciona los tipos de centros:",
            ['publico', 'concertado', 'privado'],
            default=['publico', 'concertado', 'privado']
        )

        # Filtrar barrios por nivel de seguridad
        filtered_barrios_data = barrios_data[barrios_data['criminalidad'] >= security_value]

        # Filtrar paradas de metro que están dentro de los barrios seleccionados
        metro_data_filtered = filter_metro_within_barrios(metro_data, filtered_barrios_data)

        # Filtrar centros educativos 
        centros_data_filtered = filter_centers_within_barrios(
            centros_data, 
            filtered_barrios_data, 
            metro_data, 
            filter_metro_stations_only
        )

        tab1, tab2, tab3, tab4 = st.tabs(["Map", "Metro Stations", "Barrios", "Educational Centers"])

        with tab1:
            st.subheader("Interactive Map")
            m = create_map(metro_data_filtered, barrios_data, centros_data_filtered, 
                           filter_metro_stations_only, filtered_barrios_data, 
                           show_metro_stations, selected_school_types)
            st_folium(m, width=900, height=600)

        with tab2:
            st.subheader("Metro Stations Details")
            st.dataframe(metro_data_filtered)

        with tab3:
            st.subheader("Barrios Details")
            filtered_barrios_display = filtered_barrios_data.drop(columns=['geometry'], errors='ignore')
            st.dataframe(filtered_barrios_display)

        with tab4:
            st.subheader("Educational Centers Details")
            filtered_centros_display = centros_data_filtered.drop(columns=['geometry', 'geo_point'], errors='ignore')
            st.dataframe(filtered_centros_display)
    else:
        st.error("Failed to retrieve geographic data. Please check your database connection.")

if __name__ == "__main__":
    main()