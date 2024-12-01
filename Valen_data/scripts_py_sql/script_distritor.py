from pymongo import MongoClient
import pg8000
from datetime import datetime

# Configuración de MongoDB
MONGO_URI = "mongodb://root:example@localhost:27017"
MONGO_DB_NAME = "distritos_data"
MONGO_COLLECTION_NAME = "distritos_col"

# Configuración de PostgreSQL
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "Welcome01"
POSTGRES_DB = "dataproject"

def migrate_distritos_data():
    conn = None
    try:
        # Conectar a MongoDB
        mongo_client = MongoClient(MONGO_URI)
        mongo_db = mongo_client[MONGO_DB_NAME]
        mongo_collection = mongo_db[MONGO_COLLECTION_NAME]

        # Conectar a PostgreSQL
        conn = pg8000.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
        )
        pg_cursor = conn.cursor()

        # Crear la tabla `distritos_data` si no existe
        pg_cursor.execute("""
        CREATE TABLE IF NOT EXISTS distritos_data (
            id SERIAL PRIMARY KEY,
            _id TEXT NOT NULL,
            nombre TEXT,
            coddistrit INTEGER,
            gis_gis_distritos_area GEOMETRY(Polygon, 4326),
            geo_shape_coordinates GEOMETRY(Polygon, 4326),
            geo_point_2d_lat DOUBLE PRECISION,
            geo_point_2d_lon DOUBLE PRECISION,
            latitud DOUBLE PRECISION,
            longitud DOUBLE PRECISION
        );
        """)
        conn.commit()

        # Leer los datos de MongoDB
        records = mongo_collection.find()

        for record in records:
            try:
                # Extraer y limpiar datos
                _id = str(record.get("_id", ""))
                nombre = record.get("nombre", "")
                coddistrit = record.get("coddistrit", None)
                geo_shape_coordinates = record.get("geo_shape_coordinates", [])
                geo_point_2d_lat = record.get("geo_point_2d_lat", None)
                geo_point_2d_lon = record.get("geo_point_2d_lon", None)
                latitud = record.get("latitud", None)
                longitud = record.get("longitud", None)

                # Generar el campo gis_gis_distritos_area (Polygon)
                gis_gis_distritos_area = None
                if geo_shape_coordinates:
                    try:
                        # Convertir las coordenadas a formato WKT
                        gis_gis_distritos_area = "POLYGON(("
                        for coordinates in geo_shape_coordinates[0]:  # Sólo procesamos el primer conjunto de coordenadas
                            lon, lat = coordinates
                            gis_gis_distritos_area += f"{lon} {lat}, "
                        gis_gis_distritos_area = gis_gis_distritos_area.rstrip(", ") + "))"
                    except Exception as e:
                        print(f"Error al procesar geo_shape_coordinates: {e}")
                        continue  # Salta este registro si hay un error en la conversión de coordenadas
                
                # Insertar datos en PostgreSQL
                pg_cursor.execute("""
                    INSERT INTO distritos_data (
                        _id, nombre, coddistrit, gis_gis_distritos_area, geo_shape_coordinates, 
                        geo_point_2d_lat, geo_point_2d_lon, latitud, longitud
                    ) VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326), ST_GeomFromText(%s, 4326), %s, %s, %s, %s)
                """, (
                    _id, nombre, coddistrit, gis_gis_distritos_area, 
                    gis_gis_distritos_area,  # Geo_shape_coordinates también debe pasarse como texto WKT
                    geo_point_2d_lat, geo_point_2d_lon, latitud, longitud
                ))
            except Exception as e:
                print(f"Error insertando registro: {record}")
                print(f"Detalles del error: {e}")
                # Si ocurre un error, realiza un rollback para evitar que se quede en un estado de transacción fallida
                conn.rollback()
                continue  # Salta este registro y continúa con el siguiente

        # Confirmar la transacción
        conn.commit()

    except Exception as e:
        print(f"Error general: {e}")
        if conn:
            conn.rollback()  # Si ocurre un error general, aseguramos que el rollback ocurra
    finally:
        if conn:
            conn.close()
        if mongo_client:
            mongo_client.close()

# Ejecutar la función de migración
migrate_distritos_data()
