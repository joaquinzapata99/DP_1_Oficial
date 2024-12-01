from pymongo import MongoClient
import pg8000
from datetime import datetime

# Configuración de MongoDB
MONGO_URI = "mongodb://root:example@localhost:27017"
MONGO_DB_NAME = "valenbisi_data"
MONGO_COLLECTION_NAME = "bike_data"

# Configuración de PostgreSQL
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "Welcome01"
POSTGRES_DB = "postgres"

def migrate_valenbisi_data():
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

        # Crear la tabla `valenbisi_data` si no existe
        pg_cursor.execute("""
        CREATE TABLE IF NOT EXISTS valenbisi_data (
            id SERIAL PRIMARY KEY,
            _id TEXT NOT NULL,
            address TEXT,
            number INTEGER,
            open TEXT,
            available INTEGER,
            free INTEGER,
            total INTEGER,
            ticket TEXT,
            updated_at TIMESTAMP,
            geo_shape_coordinates TEXT,
            geo_point_2d_lat DOUBLE PRECISION,
            geo_point_2d_lon DOUBLE PRECISION,
            update_jcd TIMESTAMP
        );
        """)
        conn.commit()

        # Leer los datos de MongoDB
        records = mongo_collection.find()

        for record in records:
            try:
                # Extraer y limpiar datos
                _id = str(record.get("_id", ""))
                address = record.get("address", "")
                number = record.get("number", None)
                open_status = record.get("open", "")
                available = record.get("available", None)
                free = record.get("free", None)
                total = record.get("total", None)
                ticket = record.get("ticket", "")
                updated_at = record.get("updated_at", None)
                geo_shape_coordinates = record.get("geo_shape_coordinates", [])
                geo_point_2d_lat = record.get("geo_point_2d_lat", None)
                geo_point_2d_lon = record.get("geo_point_2d_lon", None)
                update_jcd = record.get("update_jcd", None)

                # Convertir fechas
                if updated_at:
                    updated_at = datetime.strptime(updated_at, "%d/%m/%Y %H:%M:%S")
                if update_jcd:
                    update_jcd = datetime.fromisoformat(update_jcd)

                # Insertar datos en PostgreSQL
                pg_cursor.execute("""
                    INSERT INTO valenbisi_data (
                        _id, address, number, open, available, free, total, ticket, updated_at, 
                        geo_shape_coordinates, geo_point_2d_lat, geo_point_2d_lon, update_jcd
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    _id, address, number, open_status, available, free, total, ticket, updated_at,
                    ','.join(map(str, geo_shape_coordinates)) if geo_shape_coordinates else None,
                    geo_point_2d_lat, geo_point_2d_lon, update_jcd
                ))
            except Exception as e:
                print(f"Error insertando registro: {record}")
                print(f"Detalles del error: {e}")

        # Confirmar la transacción
        conn.commit()

        # Cerrar conexiones
        pg_cursor.close()
        conn.close()
        mongo_client.close()

    except Exception as e:
        print(f"Error general: {e}")


# Ejecutar la función de migración
migrate_valenbisi_data()
