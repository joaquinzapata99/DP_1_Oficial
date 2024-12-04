import requests
import pandas as pd
import pg8000
from io import StringIO
from time import sleep
import random  # Para generar valores aleatorios

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
        filtered_data = data[['Nombre', 'geo_shape']]

        # Generar la columna 'Criminalidad' basada en el índice del barrio
        filtered_data['Criminalidad'] = [
            list(range(random.randint(0, 3) + 1)) for _ in range(len(filtered_data))
        ]

        # Convertir la lista a un string para almacenamiento
        filtered_data['Criminalidad'] = filtered_data['Criminalidad'].apply(lambda x: ",".join(map(str, x)))


        # Imprimir datos filtrados para depuración
        print(f"Datos filtrados con criminalidad:\n{filtered_data.head()}")

        # Crear tabla en PostgreSQL
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        create_table_query = f"""
        CREATE TABLE {table_name} (
            Nombre TEXT,
            geo_shape geometry(Polygon, 4326),
            Criminalidad TEXT
        );
        """
        cursor.execute(create_table_query)

        # Insertar datos en la tabla
        for _, row in filtered_data.iterrows():
            geo_shape_query = 'NULL'
            if pd.notna(row['geo_shape']):
                try:
                    geo_shape_query = f"ST_GeomFromGeoJSON('{row['geo_shape']}')"
                except Exception as e:
                    print(f"Error procesando geo_shape: {e}")
                    continue

            insert_query = f"""
            INSERT INTO {table_name} (nombre, geo_shape, criminalidad)
            VALUES (%s, {geo_shape_query}, %s);
            """
            try:
                cursor.execute(insert_query, (row['Nombre'], row['Criminalidad']))
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

sleep(5)

# Configuración
URL_CSV = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/barris-barrios/exports/csv?lang=es&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
NOMBRE_TABLA = "barrios_valencia"
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