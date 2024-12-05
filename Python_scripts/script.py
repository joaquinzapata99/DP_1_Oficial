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

        # Asegurar que la extensión PostGIS está habilitada
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

        # Cargar datos en un DataFrame
        data = pd.read_csv(StringIO(csv_data), delimiter=delimiter)

        # Filtrar columnas necesarias
        filtered_data = data[['Geo Point', 'regimen']]

        # Imprimir datos filtrados para depuración
        print(f"Datos filtrados:\n{filtered_data.head()}")

        # Crear tabla en PostgreSQL
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        create_table_query = f"""
        CREATE TABLE {table_name} (
            geo_point geometry(Point, 4326),
            regimen TEXT
        );
        """
        cursor.execute(create_table_query)

        # Insertar datos en la tabla
        for _, row in filtered_data.iterrows():
            geo_point_query = 'NULL'
            if pd.notna(row['Geo Point']):
                try:
                    latitude, longitude = map(float, row['Geo Point'].split(','))
                    geo_point_query = f"ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)"
                except (ValueError, TypeError) as e:
                    print(f"Error procesando Geo Point {row['Geo Point']}: {e}")
                    continue

            insert_query = f"""
            INSERT INTO {table_name} (geo_point, regimen)
            VALUES ({geo_point_query}, %s);
            """
            try:
                cursor.execute(insert_query, (row['regimen'],))
            except Exception as insert_error:
                print(f"Error al insertar fila: {insert_error}")

        # Confirmar transacciones
        conn.commit()
        print(f"Datos cargados en la tabla '{table_name}' correctamente.")

    except Exception as e:
        print(f"Error al cargar los datos en PostgreSQL: {e}")
        if conn:
            conn.rollback()
    finally:
        # Cerrar cursor y conexión de forma segura
        if cursor:
            cursor.close()
        if conn:
            conn.close()

sleep(30)

# Configuración
URL_CSV = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/centros-educativos-en-valencia/exports/csv?lang=en&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
NOMBRE_TABLA = "centros_educativos"
CONFIG_DB = {
    "host": "postgres",  # Nombre del servicio definido en docker-compose
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