import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium
import folium
from sqlalchemy import create_engine, text
import unicodedata
import numpy as np
from contextlib import contextmanager
from branca.element import Template, MacroElement

# Enhanced Database Configuration
DB_CONFIG = {
    "host": "postgres_container",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

# Create a single engine instance for the application
@st.cache_resource
def get_database_engine():
    connection_string = f"postgresql+pg8000://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(
        connection_string,
        pool_size=5,  # Reduced pool size
        max_overflow=10,  # Reduced max overflow
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True  # Enable connection health checks
    )

@contextmanager
def get_connection():
    """Context manager for database connections"""
    engine = get_database_engine()
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()

def normalize_text(text):
    if isinstance(text, str):
        return unicodedata.normalize('NFKD', text.lower()).encode('ASCII', 'ignore').decode('ASCII')
    return text

def fetch_data(table_name):
    try:
        # Get column information
        with get_connection() as conn:
            columns_query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
            result = conn.execute(columns_query)
            columns = result.fetchall()

        # Price data handling
        if table_name == 'precios_barrios':
            with get_connection() as conn:
                query = text(f"SELECT * FROM {table_name};")
                price_data = pd.read_sql(query, conn)
            return price_data

        # Geometry columns handling
        geo_columns = [col[0] for col in columns if 'geo' in col[0].lower() or 'shape' in col[0].lower() or 'point' in col[0].lower()]
        if not geo_columns:
            st.error(f"No geometry column found in table {table_name}")
            return None

        geo_col = geo_columns[0]
        query = text(f"SELECT *, {geo_col} AS geometry FROM {table_name} LIMIT 500;")

        with get_connection() as conn:
            data = gpd.read_postgis(query, conn, geom_col='geometry')

        if 'regimen' in data.columns:
            data['regimen_normalized'] = data['regimen'].apply(normalize_text)

        data = data[data.geometry.notnull()]
        data = data[data.geometry.is_valid]

        return data

    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return None

def filter_metro_within_barrios(metro_data, barrios_data):
    try:
        combined_barrios_geometry = barrios_data.unary_union
        metro_data = metro_data[metro_data.geometry.notnull()]
        metro_data = metro_data[metro_data.geometry.is_valid]
        metro_data_filtered = metro_data[metro_data.geometry.within(combined_barrios_geometry)]
        return metro_data_filtered
    except Exception as e:
        st.error(f"Error filtering metro stations within barrios: {e}")
        return metro_data

def filter_centers_within_barrios(centers_data, barrios_data, metro_data=None, filter_metro_stations_only=False):
    try:
        combined_barrios_geometry = barrios_data.unary_union
        centers_data = centers_data[centers_data.geometry.notnull()]
        centers_data = centers_data[centers_data.geometry.is_valid]

        centers_in_barrios = centers_data[centers_data.geometry.within(combined_barrios_geometry)]

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
    m = folium.Map(location=[39.4699, -0.3763], zoom_start=12)
    metro_color = 'red'
    selected_color = 'green'
    school_colors = {'publico': 'purple', 'concertado': 'orange', 'privado': 'blue'}

    normalized_selected_types = [normalize_text(st) for st in selected_school_types]

    # Create legend template with updated styling
    legend_template = """
    {% macro html(this, kwargs) %}
    <div id='maplegend' class='maplegend' 
        style='position: absolute; z-index: 9999; background-color: white;
         border-radius: 6px; padding: 10px; font-size: 12px; right: 100px; top: 20px;
         border: 2px solid gray; box-shadow: 0 0 15px rgba(0,0,0,0.2);
         color: black;'>
         
    <div class='legend-title' style='margin-bottom: 10px; font-weight: bold; color: black;'>Leyenda</div>
    <div class='legend-scale'>
      <ul class='legend-labels'>
        <li><span style='background: green; opacity: 0.5;'></span>Barrios seleccionados</li>
    """

    if show_metro_stations:
        legend_template += """
        <li><span style='background: red; border-radius: 50%;'></span>Paradas de metro</li>
        """

    for school_type in selected_school_types:
        color = school_colors.get(school_type)
        label = {
            'publico': 'Centros públicos',
            'concertado': 'Centros concertados',
            'privado': 'Centros privados'
        }.get(school_type)
        if color and label:
            legend_template += f"""
            <li><span style='background: {color}; border-radius: 50%;'></span>{label}</li>
            """

    legend_template += """
      </ul>
    </div>
    </div>
    <style type='text/css'>
      .maplegend {
        color: black;
      }
      .maplegend .legend-title {
        text-align: left;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 90%;
        }
      .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: left;
        list-style: none;
        }
      .maplegend .legend-scale ul li {
        font-size: 80%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 2px;
        color: black;
        }
      .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 16px;
        margin-right: 5px;
        margin-left: 0;
        border: 1px solid #999;
        }
    </style>
    {% endmacro %}
    """

    # Create MacroElement and add to map
    macro = MacroElement()
    macro._name = "legend"
    macro._template = Template(legend_template)
    m.get_root().add_child(macro)

    # Add map features
    if show_metro_stations:
        filtered_metro = metro_data[
            metro_data.geometry.apply(
                lambda point: any(point.within(barrio_geom) for barrio_geom in filtered_barrios_data.geometry)
            )
        ]
        
        filtered_metro = filtered_metro[filtered_metro.geometry.notnull()]
        for _, row in filtered_metro.iterrows():
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

def save_demanda(barrios, email, nombre, apellidos):
    try:
        with get_connection() as conn:
            # Create table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS demanda (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255),
                    nombre VARCHAR(255),
                    apellidos VARCHAR(255),
                    barrio VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Insert data
            for b in barrios:
                conn.execute(
                    text("INSERT INTO demanda (email, nombre, apellidos, barrio) VALUES (:email, :nombre, :apellidos, :barrio)"),
                    {"email": email, "nombre": nombre, "apellidos": apellidos, "barrio": b}
                )
            conn.commit()
    except Exception as e:
        st.error(f"Error saving demand data: {e}")

def reset_session():
    for key in st.session_state.keys():
        del st.session_state[key]

def main():
    st.set_page_config(
        page_title="Filtrado", 
        page_icon=":mag:", 
        layout="wide"
    )

    if "step" not in st.session_state:
        st.session_state.step = 1

    if st.button("Nueva Consulta"):
        reset_session()
        st.session_state.step = 1

    st.title("Haz match con tu nuevo hogar 🌇")

    if st.session_state.step == 1:
        # Paso 1: Solicitar datos del usuario
        st.header("Introduce tus datos")
        email = st.text_input("Email:")
        nombre = st.text_input("Nombre:")
        apellidos = st.text_input("Apellidos:")
        
        if st.button("Continuar"):
            if email and nombre and apellidos:
                st.session_state.email = email
                st.session_state.nombre = nombre
                st.session_state.apellidos = apellidos
                st.session_state.step = 2
            else:
                st.warning("Por favor, rellena todos los campos antes de continuar.")

    elif st.session_state.step == 2:
        # Paso 2: Aplicar filtros
        st.header(f"Hola {st.session_state.nombre}, personaliza tu mapa:")

        with st.spinner('Cargando datos geográficos...'):
            metro_data = fetch_data("paradas_metro")
            barrios_data = fetch_data("barrios_valencia")
            centros_data = fetch_data("centros_educativos")
            precios_data = fetch_data("precios_barrios")

        if metro_data is None or barrios_data is None or centros_data is None or precios_data is None:
            st.error("No se pudieron obtener los datos geográficos. Verifica la conexión con la base de datos.")
        else:
            st.sidebar.subheader("Filtros de Barrios:")
            response = st.sidebar.radio("¿Necesitas acceso al metro?", ("Sí", "No"))
            filter_metro_stations_only = (response == "Sí")

            show_metro_stations = st.sidebar.checkbox("Mostrar paradas de metro", value=True)
            if filter_metro_stations_only:
                show_metro_stations = True

            security_value = st.sidebar.slider("Nivel mínimo de seguridad (0 a 3):", 0, 3, 0)

            # Price Category Filter
            price_category = st.sidebar.radio(
                "Categoría de Precio:", 
                ("Todos", "Económico", "Medio", "Alto"),
                help="Filtra barrios según su categoría de precio"
            )

            need_educational_centers = st.sidebar.radio("¿Quieres filtrar por centros educativos?", ("No", "Sí"))
            selected_school_types = []
            if need_educational_centers == "Sí":
                selected_school_types = st.sidebar.multiselect(
                    "Tipos de centros:",
                    ['publico', 'concertado', 'privado'],
                    default=['publico', 'concertado', 'privado']
                )

            if "show_results" not in st.session_state:
                st.session_state.show_results = False

            if st.button("Aplicar filtros"):
                filtered_barrios_data = barrios_data[barrios_data['criminalidad'] >= security_value]

                # Price Filtering Logic
                if price_category != "Todos":
                    price_map = {"Económico": 1, "Medio": 2, "Alto": 3}
                    selected_price_category = price_map.get(price_category)
                    
                    price_merged = filtered_barrios_data.merge(
                        precios_data, 
                        left_on='nombre',
                        right_on='barrio',
                        how='inner'
                    )
                    
                    filtered_barrios_data = price_merged[
                        price_merged['categoria_precio'] == selected_price_category
                    ]

                metro_data_filtered = filter_metro_within_barrios(metro_data, filtered_barrios_data)
                if filter_metro_stations_only and show_metro_stations:
                    filtered_barrios_data = filtered_barrios_data[
                        filtered_barrios_data.geometry.intersects(metro_data_filtered.geometry.unary_union)
                    ]

                if need_educational_centers == "Sí":
                    centros_data_filtered = filter_centers_within_barrios(
                        centros_data, filtered_barrios_data, metro_data, filter_metro_stations_only
                    )
                    centros_data_filtered = centros_data_filtered[
                        centros_data_filtered['regimen_normalized'].isin([normalize_text(t) for t in selected_school_types])
                    ]

                    if len(centros_data_filtered) > 0:
                        filtered_barrios_data = filtered_barrios_data[
                            filtered_barrios_data.geometry.intersects(centros_data_filtered.unary_union)
                        ]
                    else:
                        filtered_barrios_data = gpd.GeoDataFrame(columns=filtered_barrios_data.columns)
                else:
                    centros_data_filtered = pd.DataFrame(columns=centros_data.columns)

                st.session_state.filtered_barrios_data = filtered_barrios_data
                st.session_state.metro_data_filtered = metro_data_filtered
                st.session_state.centros_data_filtered = centros_data_filtered
                st.session_state.show_results = True

                # Save to demand table
                if 'nombre' in filtered_barrios_data.columns:
                    barrios_optimos = filtered_barrios_data['nombre'].unique().tolist()
                else:
                    barrios_optimos = []
                
                if barrios_optimos:
                    save_demanda(barrios_optimos, st.session_state.email, st.session_state.nombre, st.session_state.apellidos)
                    st.success("Datos guardados en la tabla 'demanda'.")
                else:
                    st.warning("No hay barrios que cumplan las condiciones para guardar en demanda.")

            if st.session_state.show_results:
                filtered_barrios_data = st.session_state.filtered_barrios_data
                metro_data_filtered = st.session_state.metro_data_filtered
                centros_data_filtered = st.session_state.centros_data_filtered

                st.subheader("Mapa Interactivo")
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

                st.subheader("Detalles de los Barrios")
                if not filtered_barrios_data.empty:
                    filtered_barrios_display = filtered_barrios_data.drop(columns=['geometry'], errors='ignore')
                    st.dataframe(filtered_barrios_display)
                else:
                    st.write("No hay barrios que cumplan las condiciones.")

                st.subheader("Paradas de Metro Filtradas")
                if not metro_data_filtered.empty:
                    metro_display = metro_data_filtered.drop(columns=['geometry'], errors='ignore')
                    st.dataframe(metro_display)
                else:
                    st.write("No hay paradas de metro en los barrios seleccionados.")

                if need_educational_centers == "Sí":
                    st.subheader("Centros Educativos Filtrados")
    
                    if not centros_data_filtered.empty:
                        columnas_a_mostrar = ['nombre', 'regimen', 'direccion', 'mail', 'telef', 'dgenerica_', 'despecific']
                        columnas_presentes = [col for col in columnas_a_mostrar if col in centros_data_filtered.columns]
        
                        if columnas_presentes:
                            st.dataframe(centros_data_filtered[columnas_presentes])
                        else:
                            st.warning(f"No se encuentran todas las columnas requeridas: {columnas_a_mostrar}")
                    else:
                        st.info("No hay centros educativos disponibles para mostrar.")
                        
                if price_category != "Todos":
                    st.subheader("Información de Precios")
                    if not filtered_barrios_data.empty:
                        price_info = filtered_barrios_data[['nombre', 'precio_2022', 'categoria_precio']].drop_duplicates()
                        st.dataframe(price_info)
                    else:
                        st.write("No hay información de precios disponible para los barrios seleccionados.")

if __name__ == "__main__":
    main()