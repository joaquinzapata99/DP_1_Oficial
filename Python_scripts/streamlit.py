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

        geo_col = geo_columns[0]  # Use the first valid geometry column
        query = text(f"SELECT *, {geo_col} AS geometry FROM {table_name} LIMIT 500;")

        # Read data using GeoPandas
        with engine.connect() as conn:
            data = gpd.read_postgis(query, conn, geom_col='geometry')

        # Normalize columns for consistent filtering
        if 'regimen' in data.columns:
            data['regimen_normalized'] = data['regimen'].apply(normalize_text)

        # Check for valid geometries and drop invalid ones
        data = data[data.geometry.notnull()]
        data = data[data.geometry.is_valid]

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

        # Ensure geometries are valid before filtering
        metro_data = metro_data[metro_data.geometry.notnull()]
        metro_data = metro_data[metro_data.geometry.is_valid]

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

        # Ensure geometries are valid before filtering
        centers_data = centers_data[centers_data.geometry.notnull()]
        centers_data = centers_data[centers_data.geometry.is_valid]

        # Filter centers within the selected districts
        centers_in_barrios = centers_data[centers_data.geometry.within(combined_barrios_geometry)]

        # If metro station filtering is enabled
        if filter_metro_stations_only and metro_data is not None:
            barrios_with_metro = barrios_data[barrios_data.geometry.intersects(metro_data.geometry.unary_union)]
            centers_filtered = centers_in_barrios[
                centers_in_barrios.geometry.within(barrios_with_metro.unary_union)
            ]
            return centers_filtered

        return centers_in_barrios

    except Exception as e:
        st.error(f"Error filtering educational centers: {e}")
        return centers_data

def create_map(metro_data, barrios_data, centros_data, filter_metro_stations_only, filtered_barrios_data, show_metro_stations, selected_school_types):
    """Create an interactive Folium map with only the filtered barrios"""
    m = folium.Map(location=[39.4699, -0.3763], zoom_start=12)  

    # Color schemes
    metro_color = 'red'
    selected_color = 'green'
    school_colors = {'publico': 'purple', 'concertado': 'orange', 'privado': 'blue'}

    # Normalize selected school types
    normalized_selected_types = [normalize_text(st) for st in selected_school_types]

    # Plot metro stations
    if show_metro_stations:
        metro_data = metro_data[metro_data.geometry.notnull()]
        for _, row in metro_data.iterrows():
            point = row.geometry
            if point.is_empty:
                continue
            folium.CircleMarker(
                location=[point.y, point.x],
                radius=5,
                popup=row.get("name", "Parada de Metro"),
                color=metro_color,
                fill=True,
                fillColor=metro_color
            ).add_to(m)

    # Plot educational centers
    if len(centros_data) > 0:
        centros_data = centros_data[centros_data.geometry.notnull()]
        for _, row in centros_data.iterrows():
            if row['regimen_normalized'] in normalized_selected_types:
                point = row.geometry
                if point.is_empty:
                    continue
                folium.CircleMarker(
                    location=[point.y, point.x],
                    radius=5,
                    popup=f"{row.get('nombre', 'Centro Educativo')} ({row['regimen']})",
                    color=school_colors.get(row['regimen_normalized'], 'gray'),
                    fill=True,
                    fillColor=school_colors.get(row['regimen_normalized'], 'gray')
                ).add_to(m)

    # Plot filtered barrios
    filtered_barrios_data = filtered_barrios_data[filtered_barrios_data.geometry.notnull()]
    for _, row in filtered_barrios_data.iterrows():
        geometry = row.geometry
        if geometry.is_empty:
            continue
        folium.GeoJson(
            geometry.__geo_interface__,
            popup=row.get("nombre", "Barrio sin nombre"),
            tooltip=row.get("nombre", "Barrio sin nombre"),
            style_function=lambda _: {
                'fillColor': selected_color,
                'fillOpacity': 0.5,
                'weight': 1,
                'color': selected_color
            }
        ).add_to(m)

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
    Mira a ver cuál es tu sitio, que te veo desubicado **pinpin**
    """)

    with st.spinner('Fetching geographic data...'):
        metro_data = fetch_data("paradas_metro")
        barrios_data = fetch_data("barrios_valencia")
        centros_data = fetch_data("centros_educativos")

    if metro_data is not None and barrios_data is not None and centros_data is not None:
        # Sidebar options
        st.sidebar.subheader("Personaliza tu mapa:")
        
        #filtro de metro
        st.sidebar.markdown("### ¿Usas el metro frecuentemente 🚇?")
        response = st.sidebar.radio("¿Necesitas acceso al metro?", ("Sí", "No"))
        filter_metro_stations_only = response == "Sí"

        # Checkbox para mostrar paradas de metro (por defecto True)
        show_metro_stations = st.sidebar.checkbox("Mostrar paradas de metro", value=True)
        
        # Si el usuario necesita acceso al metro, forzamos a mostrar las paradas de metro.
        if filter_metro_stations_only:
            show_metro_stations = True

        st.sidebar.markdown("### ¿Cuánto valoras la seguridad de tu barrio? 🚔")
        security_value = st.sidebar.slider("Selecciona el nivel mínimo de seguridad:", 0, 3, 0)
        
        # Preguntar si se desean centros educativos
        st.sidebar.markdown("### ¿Necesitas centros educativos cerca? 🏫")
        need_educational_centers = st.sidebar.radio("¿Quieres filtrar por centros educativos?", ("No", "Sí"))

        selected_school_types = []
        # Si el usuario quiere centros educativos, mostrar el filtro por tipo
        if need_educational_centers == "Sí":
            selected_school_types = st.sidebar.multiselect(
                "Selecciona los tipos de centros:",
                ['publico', 'concertado', 'privado'],
                default=['publico', 'concertado', 'privado']
            )

        # Aplicar filtros de barrios según el nivel de seguridad
        filtered_barrios_data = barrios_data[barrios_data['criminalidad'] >= security_value]

        # Filtrar paradas de metro en función de los barrios seleccionados
        metro_data_filtered = filter_metro_within_barrios(metro_data, filtered_barrios_data)

        # Si se requieren barrios con metro
        if filter_metro_stations_only and show_metro_stations:
            filtered_barrios_data = filtered_barrios_data[
                filtered_barrios_data.geometry.intersects(metro_data_filtered.geometry.unary_union)
            ]

        # Filtrar centros educativos solo si el usuario quiere centros educativos cerca
        if need_educational_centers == "Sí":
            centros_data_filtered = filter_centers_within_barrios(
                centros_data, 
                filtered_barrios_data, 
                metro_data, 
                filter_metro_stations_only
            )
            # Filtrar por tipos seleccionados
            centros_data_filtered = centros_data_filtered[centros_data_filtered['regimen_normalized'].isin([normalize_text(t) for t in selected_school_types])]
        else:
            # El usuario no quiere filtrar centros, por lo que no se mostrarán
            centros_data_filtered = pd.DataFrame(columns=centros_data.columns)

        # Debug: Display the count of filtered results
        print(f"Filtered Barrios: {len(filtered_barrios_data)}")
        print(f"Filtered Metro Stations: {len(metro_data_filtered)}")
        print(f"Filtered Educational Centers: {len(centros_data_filtered)}")

        # Tabs for displaying data
        tab1, tab2, tab3, tab4 = st.tabs(["Mapa", "Paradas de Metro", "Barrios", "Centros Educativos"])

        with tab1:
            st.subheader("Mapa Interactivo")
            # Aquí pasamos barrios_data original como segundo parámetro, y filtered_barrios_data en el quinto.
            m = create_map(
                metro_data_filtered, 
                barrios_data, 
                centros_data_filtered, 
                filter_metro_stations_only, 
                filtered_barrios_data, 
                show_metro_stations, 
                selected_school_types
            )
            st_folium(m, width=900, height=600)

        with tab2:
            st.subheader("Detalles de las Paradas de Metro")
            st.dataframe(metro_data_filtered)

        with tab3:
            st.subheader("Detalles de los Barrios")
            filtered_barrios_display = filtered_barrios_data.drop(columns=['geometry'], errors='ignore')
            st.dataframe(filtered_barrios_display)

        with tab4:
            st.subheader("Detalles de los Centros Educativos")
            if need_educational_centers == "Sí":
                filtered_centros_display = centros_data_filtered.drop(columns=['geometry', 'geo_point'], errors='ignore')
                st.dataframe(filtered_centros_display)
            else:
                st.write("No se han filtrado centros educativos.")

    else:
        st.error("No se pudieron obtener los datos geográficos. Verifica la conexión con la base de datos.")

if __name__ == "__main__":
    main()
