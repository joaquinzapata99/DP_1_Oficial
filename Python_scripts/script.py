import requests
import pandas as pd
import pg8000
from io import StringIO
from time import sleep 

def descargar_csv(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content.decode('utf-8')
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el archivo: {e}")
        return None

def cargar_datos_a_postgres(csv_data, table_name, db_config, delimiter=";"):
    conn = None
    cursor = None
    try:
        # Conectar a PostgreSQL
        conn = pg8000.connect(**db_config)
        cursor = conn.cursor()

        # Cargar CSV en DataFrame
        data = pd.read_csv(StringIO(csv_data), delimiter=delimiter)

        # Log para verificar columnas y tipos de datos
        print(f"Columnas y tipos de datos: {data.dtypes}")

        # Crear tabla con tipos de datos más específicos
        columns = ", ".join([f"{col} TEXT" for col in data.columns])  # Ajustar tipos de datos si es necesario
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});")

        # Insertar datos en la tabla utilizando parámetros para evitar problemas con comillas y caracteres especiales
        for _, row in data.iterrows():
            # Convertir fila a una lista de valores
            values = tuple(row)
            placeholders = ", ".join(["%s"] * len(values))  # Crear placeholders (%s) para cada valor

            # Ejecutar la inserción de forma segura utilizando parámetros
            cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders});", values)

        conn.commit()
        print(f"Datos cargados en la tabla '{table_name}' correctamente.")
    except Exception as e:
        print(f"Error al cargar los datos en PostgreSQL: {e}")
    finally:
        # Close cursor and connection safely
        if cursor:
            cursor.close()
        if conn:
            conn.close()

sleep(60)

# Configuración
URL_CSV = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/valenbisi-disponibilitat-valenbisi-dsiponibilidad/exports/csv?lang=en&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
NOMBRE_TABLA = "valenbisi_disponibilidad"
CONFIG_DB = {
    "host": "postgres",  # Use service name defined in docker-compose
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

# Ejecutar script
if __name__ == "__main__":
    csv_data = descargar_csv(URL_CSV)
    if csv_data:
        cargar_datos_a_postgres(csv_data, NOMBRE_TABLA, CONFIG_DB, delimiter=";")
