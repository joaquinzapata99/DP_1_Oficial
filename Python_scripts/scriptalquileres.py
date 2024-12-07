import os
import pandas as pd
import pg8000

def cargar_datos_a_postgres(csv_path, table_name, db_config, delimiter=";"):
    conn = None
    cursor = None
    try:
        # Load data with explicit dtype handling
        data = pd.read_csv(csv_path, delimiter=delimiter, 
                            dtype={
                                'Id del anuncio': int,
                                'Habitaciones': int,
                                'Baños': int,
                                'Precio': float
                            })
        
        # Remove duplicate rows based on 'Id del anuncio'
        data = data.drop_duplicates(subset=['Id del anuncio'])

        # Normalize boolean columns
        data['Ascensor (Sí/No)'] = data['Ascensor (Sí/No)'].map({'Sí': True, 'No': False})
        data['Parking (Sí/No)'] = data['Parking (Sí/No)'].map({'Sí': True, 'No': False})

        # Connect to PostgreSQL
        conn = pg8000.connect(**db_config)
        conn.autocommit = False  # Explicitly manage transactions
        cursor = conn.cursor()

        # Drop and recreate table
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        create_table_query = f"""
        CREATE TABLE {table_name} (
            id_anuncio BIGINT PRIMARY KEY,
            tipo_inmueble TEXT,
            direccion TEXT,
            precio NUMERIC,
            habitaciones INTEGER,
            banos INTEGER,
            barrio TEXT,
            ascensor BOOLEAN,
            parking BOOLEAN
        );
        """
        cursor.execute(create_table_query)

        # Prepare insert statement
        insert_query = f"""
        INSERT INTO {table_name} (
            id_anuncio, tipo_inmueble, direccion, precio, 
            habitaciones, banos, barrio, ascensor, parking
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id_anuncio) DO NOTHING;
        """

        # Batch insert
        values = data[['Id del anuncio', 'Tipo de inmueble', 'Dirección', 'Precio', 
                      'Habitaciones', 'Baños', 'Barrio', 'Ascensor (Sí/No)', 'Parking (Sí/No)']].values.tolist()
        
        cursor.executemany(insert_query, values)

        # Commit transaction
        conn.commit()
        print(f"Datos cargados en la tabla '{table_name}' correctamente.")

    except Exception as e:
        print(f"Error al cargar los datos en PostgreSQL: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        # Close cursor and connection safely
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Configuration
RUTA_CSV = "/app/IdeaDatos/alquiler_total .csv"
NOMBRE_TABLA = "alquileres"
CONFIG_DB = {
    "host": "postgres",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

# Run script
if __name__ == "__main__":
    cargar_datos_a_postgres(RUTA_CSV, NOMBRE_TABLA, CONFIG_DB)