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

# Format currency values (with thousand separator, no decimals, and euro symbol)
def format_currency(value):
    return f"{int(round(value)):,}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# Format percentage values (with comma decimal separator and 1 decimal)
def format_percentage(value):
    return f"{value:.1f}".replace(".", ",") + "%"

# Fetch filtered rental data (average monthly rent)
def fetch_filtered_rental_data(habitaciones, banos, ascensor, parking):
    conn, cursor = connect_to_db()

    try:
        # Map 'Sí'/'No' to boolean values
        ascensor_boolean = True if ascensor == "Sí" else False
        parking_boolean = True if parking == "Sí" else False

        # Query to compute average monthly rent
        query = """
            SELECT barrio, AVG(precio) AS alquiler_mensual
            FROM alquileres
            WHERE habitaciones = %s
            AND banos = %s
            AND ascensor = %s
            AND parking = %s
            GROUP BY barrio
        """

        cursor.execute(query, (habitaciones, banos, ascensor_boolean, parking_boolean))
        data = pd.DataFrame(cursor.fetchall(), columns=["barrio", "alquiler_mensual"])

    except Exception as e:
        st.error(f"Database query error in rental data fetch: {e}")
        data = pd.DataFrame()
    finally:
        cursor.close()
        conn.close()

    return data

# Fetch filtered purchase data (average purchase cost)
def fetch_filtered_purchase_data(habitaciones, banos, ascensor, parking):
    conn, cursor = connect_to_db()

    try:
        # Map 'Sí'/'No' to boolean values
        ascensor_boolean = True if ascensor == "Sí" else False
        parking_boolean = True if parking == "Sí" else False

        # Query to compute average purchase cost
        query = """
            SELECT barrio, AVG(precio) AS precio_venta
            FROM compras
            WHERE habitaciones = %s
            AND banos = %s
            AND ascensor = %s
            AND parking = %s
            GROUP BY barrio
        """

        cursor.execute(query, (habitaciones, banos, ascensor_boolean, parking_boolean))
        data = pd.DataFrame(cursor.fetchall(), columns=["barrio", "precio_venta"])

    except Exception as e:
        st.error(f"Database query error in purchase data fetch: {e}")
        data = pd.DataFrame()
    finally:
        cursor.close()
        conn.close()

    return data

# Streamlit App - Calculate Rentability
st.title("Invierte con Nosotros")

st.sidebar.header("Filter Options")

# Sidebar filters
num_habitaciones = st.sidebar.slider(
    "Numero de habitaciones:",
    min_value=1,
    max_value=5,
    value=3
)

num_banos = st.sidebar.slider(
    "Numero de baños:",
    min_value=1,
    max_value=3,
    value=1
)

ascensor = st.sidebar.selectbox(
    "Con ascensor?", options=["Sí", "No"], index=0
)

parking = st.sidebar.selectbox(
    "Con parking?", options=["Sí", "No"], index=0
)

# Fetch filtered rental and purchase data
rental_data = fetch_filtered_rental_data(num_habitaciones, num_banos, ascensor, parking)
purchase_data = fetch_filtered_purchase_data(num_habitaciones, num_banos, ascensor, parking)

# Ensure data exists
if rental_data.empty or purchase_data.empty:
    st.warning("No data found for these filters. Try modifying the selection criteria.")
else:
    # Merge the rental and purchase data on 'barrio' for analysis
    analysis_df = pd.merge(
        rental_data,
        purchase_data,
        how="inner",
        on="barrio"
    )

    # Compute the annual income and rentability percentage dynamically
    analysis_df["Renta_Anual"] = analysis_df["alquiler_mensual"] * 12
    analysis_df["Rentability_%"] = (analysis_df["Renta_Anual"] / analysis_df["precio_venta"]) * 100

    # Sort the data by calculated rentability percentage
    analysis_df_sorted = analysis_df.sort_values(by="Rentability_%", ascending=False)

    # Format the numeric columns
    formatted_df = analysis_df_sorted.copy()
    formatted_df["alquiler_mensual"] = formatted_df["alquiler_mensual"].apply(format_currency)
    formatted_df["precio_venta"] = formatted_df["precio_venta"].apply(format_currency)
    formatted_df["Renta_Anual"] = formatted_df["Renta_Anual"].apply(format_currency)
    formatted_df["Rentability_%"] = formatted_df["Rentability_%"].apply(format_percentage)

    # Rename columns for display
    display_df = formatted_df.rename(columns={
        "barrio": "Barrio",
        "alquiler_mensual": "Alquiler Mensual",
        "precio_venta": "Precio de Venta",
        "Renta_Anual": "Renta Anual",
        "Rentability_%": "Rentabilidad"
    })

    # Display results
    st.write(f"Rentabilidad esperada por {num_habitaciones} habitaciones, {num_banos} baños, ascensor: {ascensor}, parking: {parking}:")
    st.table(display_df[["Barrio", "Alquiler Mensual", "Precio de Venta", "Renta Anual", "Rentabilidad"]])