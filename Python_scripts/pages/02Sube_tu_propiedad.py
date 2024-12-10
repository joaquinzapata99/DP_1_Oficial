import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuración de la base de datos
DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

# Lista de barrios predefinidos
BARRIOS = [
    "L'AMISTAT", "EL GRAU", "RAFALELL-VISTABELLA", "LA CARRASCA", "BENIFERRI", "EL SALER", "CARPESA", "SANT ANTONI",
    "MARXALENES", "EL CALVARI", "LES TENDETES", "EXPOSICIO", "LA VEGA BAIXA", "L'HORT DE SENABRE", "EL PILAR", 
    "CAMI FONDO", "RUSSAFA", "SAFRANAR", "EN CORTS", "LES CASES DE BARCENA", "CIUTAT FALLERA", "NOU MOLES", 
    "MESTALLA", "MAHUELLA-TAULADELLA", "MASSARROJOS", "LA LLUM", "LA MALVA-ROSA", "MORVEDRE", "SANT PAU", 
    "JAUME ROIG", "SANT MARCEL.LI", "LA CREU COBERTA", "CAMI REAL", "LA PUNTA", "CAMPANAR", "EL CARME", 
    "BENIMAMET", "SANT LLORENS", "CIUTAT UNIVERSITARIA", "BETERO", "EL PLA DEL REMEI", "LA XEREA", "ALBORS", 
    "ARRANCAPINS", "LA ROQUETA", "LA GRAN VIA", "LA CREU DEL GRAU", "SANT ISIDRE", "MALILLA", "BENICALAP", 
    "LA PETXINA", "PENYA-ROJA", "FAITANAR", "EL FORN D'ALCEDO", "PINEDO", "CASTELLAR-L'OLIVERAL", "AIORA", 
    "NA ROVELLA", "FAVARA", "NATZARET", "LA FONTETA S.LLUIS", "CIUTAT JARDI", "CAMI DE VERA", "EL PALMAR", 
    "EL PERELLONET", "VARA DE QUART", "SOTERNES", "LA FONTSANTA", "EL BOTANIC", "BORBOTO", "L'ILLA PERDUDA", 
    "TRES FORQUES", "PATRAIX", "LA RAIOSA", "BENIFARAIG", "TORREFIEL", "TORMOS", "BENIMACLET", "TRINITAT", 
    "CABANYAL-CANYAMELAR", "EL MERCAT", "POBLE NOU", "CIUTAT DE LES ARTS I DE LES CIENCIES", "LA TORRE", 
    "SANT FRANCESC", "ELS ORRIOLS", "LA SEU", "MONTOLIVET"
]

def create_sqlalchemy_engine():
    """
    Crea un motor SQLAlchemy para conectarse a PostgreSQL.
    """
    connection_string = f"postgresql+pg8000://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(connection_string)

def check_table_exists(conn, table_name):
    """
    Verifica si la tabla existe en la base de datos.
    """
    try:
        result = conn.execute(text(f"SELECT to_regclass('{table_name}');"))
        table_exists = result.scalar() is not None
        return table_exists
    except Exception as e:
        st.error(f"Error verificando la existencia de la tabla '{table_name}': {e}")
        return False

def load_properties_from_db(conn, table_name):
    """
    Carga los registros de la base de datos y los devuelve como un DataFrame.
    Si la tabla no existe o está vacía, se devuelve un DataFrame vacío.
    """
    try:
        if check_table_exists(conn, table_name):
            query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC;"
            df = pd.read_sql(query, conn)
            if not df.empty:
                return df
            else:
                st.info(f"La tabla '{table_name}' existe, pero no tiene registros.")
                return pd.DataFrame()
        else:
            st.info(f"La tabla '{table_name}' no existe.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar los datos de la tabla '{table_name}': {e}")
        return pd.DataFrame()

def save_property_to_db(property_data, table_name):
    """
    Guarda la descripción de una propiedad en la base de datos en la tabla especificada.
    """
    try:
        engine = create_sqlalchemy_engine()
        with engine.connect() as conn:
            # Crear la tabla si no existe
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    barrio TEXT,
                    direccion TEXT,
                    numero_calle TEXT,
                    metros_cuadrados FLOAT,
                    habitaciones INTEGER,
                    banos INTEGER,
                    dependencias TEXT,
                    ascensor BOOLEAN,
                    parking BOOLEAN,
                    precio FLOAT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            # Insertar los datos de la propiedad
            insert_query = text(f"""
                INSERT INTO {table_name} (
                    barrio, direccion, numero_calle, metros_cuadrados, habitaciones,
                    banos, dependencias, ascensor, parking, precio
                ) VALUES (
                    :barrio, :direccion, :numero_calle, :metros_cuadrados, :habitaciones,
                    :banos, :dependencias, :ascensor, :parking, :precio
                )
            """)
            conn.execute(insert_query, property_data)
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error al guardar los datos en la tabla '{table_name}': {e}")
        return False

def main():
    """
    Interfaz principal de la página de subida de propiedades.
    """
    st.set_page_config(
        page_title="Subida de Propiedades",
        page_icon="🏠",
        layout="wide"
    )

    st.title("Subida de Propiedades - Venta o Alquiler")
    st.write("Por favor, complete los datos del formulario para registrar una nueva propiedad.")

    with st.form(key="property_form"):
        st.subheader("Detalles de la Propiedad")

        tipo_operacion = st.radio("¿Es una propiedad para venta o alquiler?", ["Venta", "Alquiler"])
        barrio = st.selectbox("Barrio:", options=BARRIOS)
        direccion = st.text_input("Dirección:")
        numero_calle = st.text_input("Número de la Calle:")
        metros_cuadrados = st.number_input("Metros Cuadrados:", min_value=0.0, format="%.2f")
        habitaciones = st.number_input("Número de Habitaciones:", min_value=0, step=1)
        banos = st.number_input("Número de Baños:", min_value=0, step=1)
        dependencias = st.text_area("Descripción de Otras Dependencias:")
        ascensor = st.checkbox("El edificio dispone de ascensor")
        parking = st.checkbox("El edificio dispone de parking")
        precio = st.number_input("Precio (en euros):", min_value=0.0, format="%.2f")

        submit_button = st.form_submit_button(label="Subir Propiedad")

        if submit_button:
            property_data = {
                "barrio": barrio,
                "direccion": direccion,
                "numero_calle": numero_calle,
                "metros_cuadrados": metros_cuadrados,
                "habitaciones": habitaciones,
                "banos": banos,
                "dependencias": dependencias,
                "ascensor": ascensor,
                "parking": parking,
                "precio": precio,
            }
            table_name = "propiedades_venta" if tipo_operacion == "Venta" else "propiedades_alquiler"
            success = save_property_to_db(property_data, table_name)
            if success:
                st.success(f"¡Propiedad subida correctamente a la tabla '{table_name}'!")
                
    st.subheader("Propiedades Registradas")
    try:
        engine = create_sqlalchemy_engine()
        with engine.connect() as conn:
            # Mostrar propiedades para venta
            st.subheader("Propiedades para Venta")
            venta_df = load_properties_from_db(conn, "propiedades_venta")
            if not venta_df.empty:
                st.dataframe(venta_df)
            else:
                st.info("No hay propiedades registradas para venta.")

            # Mostrar propiedades para alquiler
            st.subheader("Propiedades para Alquiler")
            alquiler_df = load_properties_from_db(conn, "propiedades_alquiler")
            if not alquiler_df.empty:
                st.dataframe(alquiler_df)
            else:
                st.info("No hay propiedades registradas para alquiler.")
    except Exception as e:
        st.error(f"Error al cargar los datos de la base de datos: {e}")

if __name__ == "__main__":
    main()