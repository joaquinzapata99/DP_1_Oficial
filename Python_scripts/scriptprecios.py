import requests
import pandas as pd
import pg8000
from io import StringIO
from time import sleep
import numpy as np
import json

def descargar_csv(url):
    """
    Download CSV file from the given URL.
    
    Args:
        url (str): URL of the CSV file to download
    
    Returns:
        str or None: CSV content as a string, or None if download fails
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
    Load CSV data into PostgreSQL with price categorization and robust error handling.
    
    Args:
        csv_data (str): CSV content as a string
        table_name (str): Name of the table to create/load
        db_config (dict): Database connection configuration
        delimiter (str, optional): CSV delimiter. Defaults to ";"
    """
    conn = None
    cursor = None
    try:
        # Conectar a PostgreSQL
        conn = pg8000.connect(**db_config)
        cursor = conn.cursor()

        # Cargar datos en un DataFrame
        data = pd.read_csv(StringIO(csv_data), delimiter=delimiter)

        # Limpiar y preparar datos
        data = data.copy()
        
        # Convertir precio a numérico y quitar filas con datos faltantes
        data['Precio_2022 (Euros/m2)'] = pd.to_numeric(data['Precio_2022 (Euros/m2)'], errors='coerce')
        filtered_data = data[['BARRIO', 'Precio_2022 (Euros/m2)']].dropna()

        # Categorizar precios en 3 niveles basados en los cuantiles de Precio_2022
        price_2022 = filtered_data['Precio_2022 (Euros/m2)']
        
        # Manejar caso de pocos datos únicos
        if len(price_2022.unique()) < 3:
            print("Advertencia: Pocos valores únicos para categorización de precios.")
            price_categories = pd.cut(price_2022, bins=3, labels=[1, 2, 3])
        else:
            price_categories = pd.qcut(price_2022, q=3, labels=[1, 2, 3])
        
        filtered_data['Categoria_Precio'] = price_categories

        # Crear tabla en PostgreSQL
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        create_table_query = f"""
        CREATE TABLE {table_name} (
            Barrio TEXT,
            Precio_2022 FLOAT,
            Categoria_Precio INTEGER
        );
        """
        cursor.execute(create_table_query)

        # Preparar la consulta de inserción fuera del bucle para eficiencia
        insert_query = f"""
        INSERT INTO {table_name} (
            Barrio, Precio_2022, Categoria_Precio
        ) VALUES (%s, %s, %s);
        """

        # Contador de filas insertadas
        filas_insertadas = 0
        filas_fallidas = 0

        # Insertar datos en la tabla
        for _, row in filtered_data.iterrows():
            try:
                # Intentar insertar la fila
                cursor.execute(insert_query, (
                    str(row['BARRIO']), 
                    float(row['Precio_2022 (Euros/m2)']), 
                    int(row['Categoria_Precio'])
                ))
                filas_insertadas += 1

            except Exception as insert_error:
                print(f"Error al insertar fila: {insert_error}")
                filas_fallidas += 1

        # Confirmar transacciones
        conn.commit()
        print(f"Datos cargados en la tabla '{table_name}' correctamente.")
        print(f"Filas insertadas: {filas_insertadas}")
        print(f"Filas fallidas: {filas_fallidas}")

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

# Pequeño retraso para evitar problemas de concurrencia
sleep(2)

# Configuración
URL_CSV = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/precio-de-compra-en-idealista/exports/csv?lang=es&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"  # Reemplaza con la URL real
NOMBRE_TABLA = "precios_barrios"
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
