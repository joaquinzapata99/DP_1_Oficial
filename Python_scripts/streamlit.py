import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from sqlalchemy import create_engine, text


# Enhanced Database Configuration
DB_CONFIG = {
    "host": "postgres_container",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

def create_sqlalchemy_engine():
    """Create SQLAlchemy engine using pg8000 dialect"""
    connection_string = f"postgresql+pg8000://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(connection_string)

def fetch_data(table_name):
    """Fetch data from PostgreSQL with enhanced error handling"""
    try:
        # Use SQLAlchemy engine for connection
        engine = create_sqlalchemy_engine()

        # Obtener nombres de columnas desde la tabla
        with engine.connect() as conn:
            columns_query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
            result = conn.execute(columns_query)
            columns = result.fetchall()

        # Detectar columnas de geometría
        geo_columns = [col[0] for col in columns if 'geo' in col[0].lower() or 'shape' in col[0].lower()]

        if not geo_columns:
            st.error(f"No geometry column found in table {table_name}")
            return None

        # Leer datos con la columna de geometría detectada
        geo_col = geo_columns[0]  # Asumimos que usamos la primera columna válida
        query = text(f"SELECT * FROM {table_name} LIMIT 500;")

        # Leer datos usando GeoPandas
        with engine.connect() as conn:
            data = gpd.read_postgis(query, conn, geom_col=geo_col)
        
        st.success(f"Successfully read data using geometry column: {geo_col}")
        return data

    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return None

def filter_metro_within_barrios(metro_data, barrios_data):
    """Filter metro stations to only those within the selected barrios"""
    try:
        # Unir todos los polígonos de los barrios seleccionados
        combined_barrios_geometry = barrios_data.unary_union

        # Filtrar las paradas de metro que están dentro de los barrios seleccionados
        metro_data_filtered = metro_data[metro_data.geometry.within(combined_barrios_geometry)]
        return metro_data_filtered
    except Exception as e:
        st.error(f"Error filtering metro stations within barrios: {e}")
        return metro_data

def create_map(metro_data, barrios_data, filter_metro_stations_only, filtered_barrios_data, show_metro_stations):
    """Create an interactive Folium map"""
    m = folium.Map(location=[39.4699, -0.3763], zoom_start=12)  

    # Color schemes
    metro_color = 'red'
    barrios_color = 'blue'
    selected_color = 'green'

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

    # Plot barrios (districts) from filtered data
    for _, row in filtered_barrios_data.iterrows():
        try:
            geo_col = [col for col in row.index if 'geo' in col.lower() or 'shape' in col.lower()][0]
            geometry = row[geo_col]
            
            # Get the neighborhood name using 'nombre' column
            neighborhood_name = row.get("nombre", "Barrio sin nombre")
            
            # Filter neighborhoods that have metro stations inside them if filter is enabled
            if filter_metro_stations_only:
                metros_in_barrio = metro_data[metro_data.geometry.within(geometry)]
                if not metros_in_barrio.empty:
                    if geometry.geom_type in ['Polygon', 'MultiPolygon']:
                        folium.GeoJson(
                            geometry.__geo_interface__,
                            popup=row.get("nombre", "Barrio"),
                            tooltip=neighborhood_name,  # Add tooltip
                            style_function=lambda feature: {
                                'fillColor': selected_color,
                                'fillOpacity': 0.5,
                                'weight': 1,
                                'color': selected_color
                            }
                        ).add_to(m)
            else:
                if geometry.geom_type in ['Polygon', 'MultiPolygon']:
                    folium.GeoJson(
                        geometry.__geo_interface__,
                        popup=row.get("nombre", "Barrio"),
                        tooltip=neighborhood_name,  # Add tooltip
                        style_function=lambda feature: {
                            'fillColor': barrios_color,
                            'fillOpacity': 0.5,
                            'weight': 1,
                            'color': barrios_color
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

    if metro_data is not None and barrios_data is not None:
        st.sidebar.subheader("Personalize your map:")
        
        # Checkbox for showing/hiding metro stations
        show_metro_stations = st.sidebar.checkbox("Show Metro Stations", value=True)
        
        st.sidebar.markdown("### ¿Usas el metro frecuentemente 🚇?")
        response = st.sidebar.radio("Choose an option:", ("Yes", "No"))
        filter_metro_stations_only = response == "Yes"

        st.sidebar.markdown("### ¿Cuánto valoras la seguridad de tu barrio? 🚔")
        security_value = st.sidebar.slider("Select security value:", 0, 3, 0)
        
        # Filtrar barrios por nivel de seguridad
        filtered_barrios_data = barrios_data[barrios_data['criminalidad'] >= security_value]

        # Filtrar paradas de metro que están dentro de los barrios seleccionados
        metro_data_filtered = filter_metro_within_barrios(metro_data, filtered_barrios_data)

        tab1, tab2, tab3 = st.tabs(["Map", "Metro Stations", "Barrios"])

        with tab1:
            st.subheader("Interactive Map")
            m = create_map(metro_data_filtered, barrios_data, filter_metro_stations_only, filtered_barrios_data, show_metro_stations)
            st_folium(m, width=900, height=600)

        with tab2:
            st.subheader("Metro Stations Details")
            st.dataframe(metro_data_filtered)

        with tab3:
            st.subheader("Barrios Details")
            filtered_barrios_display = filtered_barrios_data.drop(columns=['geometry'], errors='ignore')
            st.dataframe(filtered_barrios_display)
    else:
        st.error("Failed to retrieve geographic data. Please check your database connection.")

if __name__ == "__main__":
    main()
