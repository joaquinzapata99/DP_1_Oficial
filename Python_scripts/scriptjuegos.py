import requests
import pandas as pd
import pg8000
from io import StringIO
from time import sleep

def descargar_csv(url):
    """
    Descarga el contenido CSV desde la URL proporcionada.

    Args:
        url (str): URL del archivo CSV.

    Returns:
        str: Contenido del CSV como cadena de texto o None si falla.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content.decode('utf-8')
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el archivo: {e}")
        return None

def cargar_datos_a_postgres(csv_data, table_name, db_config, delimiter=";"):
    """
    Carga los datos filtrados del CSV en una tabla PostgreSQL.

    Args:
        csv_data (str): Contenido del CSV.
        table_name (str): Nombre de la tabla en PostgreSQL.
        db_config (dict): Configuración de la conexión a PostgreSQL.
        delimiter (str, opcional): Delimitador del CSV. Por defecto es ";".
    """
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

        # Verificar los nombres de las columnas disponibles
        print(f"Columnas disponibles en el CSV: {data.columns.tolist()}")

        # Filtrar columnas necesarias
        # Asegúrate de que los nombres de las columnas coincidan exactamente con los del CSV
        # Aquí corregimos 'jardin' a 'Jardin'
        if 'Jardin' not in data.columns or 'geo_point_2d' not in data.columns:
            print("Error: Las columnas 'Jardin' y/o 'geo_point_2d' no se encontraron en el CSV.")
            return

        filtered_data = data[['Jardin', 'geo_point_2d']]

        # Imprimir datos filtrados para depuración
        print(f"Datos filtrados:\n{filtered_data.head()}")

        # Crear tabla en PostgreSQL
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        create_table_query = f"""
        CREATE TABLE {table_name} (
            Jardin TEXT,
            geo_point_2d geometry(Point, 4326)
        );
        """
        cursor.execute(create_table_query)

        # Insertar datos en la tabla
        for index, row in filtered_data.iterrows():
            geo_point_query = 'NULL'
            if pd.notna(row['geo_point_2d']):
                try:
                    # Asumiendo que 'geo_point_2d' está en formato "lat,lon"
                    latitude, longitude = map(float, row['geo_point_2d'].split(','))
                    geo_point_query = f"ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)"
                except (ValueError, TypeError) as e:
                    print(f"Error procesando geo_point_2d '{row['geo_point_2d']}': {e}")
                    continue

            # Asegurarse de usar el nombre correcto de la columna 'Jardin'
            insert_query = f"""
            INSERT INTO {table_name} (Jardin, geo_point_2d)
            VALUES (%s, {geo_point_query});
            """
            try:
                cursor.execute(insert_query, (row['Jardin'],))
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

# Esperar 2 segundos antes de iniciar (opcional)
sleep(2)

# Configuración
URL_CSV = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/zones-jocs-infantils-zona-juegos-infantiles/exports/csv?lang=es&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"  # URL proporcionada
NOMBRE_TABLA = "zonas_infantiles"
CONFIG_DB = {
    "host": "postgres",       # Nombre del servicio definido en docker-compose o dirección IP
    "port": 5432,             # Puerto de PostgreSQL
    "database": "postgres",   # Nombre de la base de datos
    "user": "postgres",       # Usuario de PostgreSQL
    "password": "postgres",   # Contraseña de PostgreSQL
}

# Ejecutar script
if __name__ == "__main__":
    csv_data = descargar_csv(URL_CSV)
    if csv_data:
        cargar_datos_a_postgres(csv_data, NOMBRE_TABLA, CONFIG_DB, delimiter=";")
