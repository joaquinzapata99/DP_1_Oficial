import pandas as pd
import pg8000
import streamlit as st

# Database Configuration
CONFIG_DB = {
    "host": "postgres",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

# Connect to PostgreSQL
def connect_to_db():
    conn = pg8000.connect(**CONFIG_DB)
    cursor = conn.cursor()
    return conn, cursor

def create_demanda_table():
    conn, cursor = connect_to_db()
    try:
        # First, check if the table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demanda (
                id SERIAL PRIMARY KEY,
                barrio VARCHAR(255),
                email VARCHAR(255),
                nombre VARCHAR(255),
                apellidos VARCHAR(255),
                tipo_transaccion VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Check if tipo_transaccion column exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns 
            WHERE table_name = 'demanda' 
            AND column_name = 'tipo_transaccion';
        """)
        
        column_exists = cursor.fetchone()[0]
        
        # Add the column if it doesn't exist
        if column_exists == 0:
            cursor.execute("""
                ALTER TABLE demanda 
                ADD COLUMN tipo_transaccion VARCHAR(50);
            """)
            
        conn.commit()
        st.success("Tabla 'demanda' creada o actualizada correctamente.")
    except Exception as e:
        st.error(f"Error al crear/actualizar la tabla demanda: {e}")
    finally:
        cursor.close()
        conn.close()

# Ejecución
if __name__ == "__main__":
    create_demanda_table()