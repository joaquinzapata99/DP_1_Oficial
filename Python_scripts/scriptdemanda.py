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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demanda (
                id SERIAL PRIMARY KEY,
                barrio VARCHAR(255),
                email VARCHAR(255),
                nombre VARCHAR(255),
                apellidos VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        st.success("Tabla 'demanda' creada o ya existente.")
    except Exception as e:
        st.error(f"Error al crear la tabla demanda: {e}")
    finally:
        cursor.close()
        conn.close()

# Ejecución
if __name__ == "__main__":
    create_demanda_table()
