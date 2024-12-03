import requests
import pandas as pd
import psycopg2
from io import StringIO

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
        # Connect to PostgreSQL with PostGIS extension
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Ensure PostGIS extension is enabled
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

        # Load CSV into DataFrame
        data = pd.read_csv(StringIO(csv_data), delimiter=delimiter)
        
        # Print column info for debugging
        print(f"Columnas y tipos de datos: {data.dtypes}")

        # Prepare table creation with explicit geometry column
        data_columns = [col for col in data.columns if col != 'geo_point_2d']
        
        # Drop table if exists to recreate with correct schema
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        
        # Create table with geometry column
        create_table_query = f"""
        CREATE TABLE {table_name} (
            {', '.join([f'{col} TEXT' for col in data_columns])},
            geo_point_2d geometry(Point, 4326)
        );
        """
        cursor.execute(create_table_query)

        # Prepare and insert data
        for _, row in data.iterrows():
            # Handle geo_point_2d conversion
            geo_point_query = 'NULL'
            if 'geo_point_2d' in row and pd.notna(row['geo_point_2d']):
                try:
                    # Split coordinates and convert
                    latitude, longitude = map(float, row['geo_point_2d'].split(','))
                    geo_point_query = f"ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)"
                except (ValueError, TypeError) as e:
                    print(f"Error processing geo point {row['geo_point_2d']}: {e}")
                    continue

            # Prepare values for insertion
            values = [row[col] if col in data_columns else None for col in data_columns]
            
            # Create insert query with geometry
            placeholders = ', '.join(['%s'] * len(values))
            insert_query = f"""
            INSERT INTO {table_name} ({', '.join(data_columns)}, geo_point_2d)
            VALUES ({placeholders}, {geo_point_query});
            """
            
            try:
                cursor.execute(insert_query, values)
            except Exception as insert_error:
                print(f"Error inserting row: {insert_error}")

        # Commit transactions
        conn.commit()
        print(f"Datos cargados en la tabla '{table_name}' correctamente.")

    except Exception as e:
        print(f"Error al cargar los datos en PostgreSQL: {e}")
        if conn:
            conn.rollback()

    finally:
        # Safely close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Configuración
URL_CSV = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/valenbisi-disponibilitat-valenbisi-dsiponibilidad/exports/csv?lang=en&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
NOMBRE_TABLA = "valenbisi_disponibilidad"
CONFIG_DB = {
    "host": "postgres",  # Use service name defined in docker-compose
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
}

# Ejecutar script
if __name__ == "__main__":
    csv_data = descargar_csv(URL_CSV)
    if csv_data:
        cargar_datos_a_postgres(csv_data, NOMBRE_TABLA, CONFIG_DB, delimiter=";")