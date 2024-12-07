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


# Fetch filtered rental data (average monthly rent)
def fetch_filtered_rental_data(habitaciones, banos, ascensor, parking):
    conn, cursor = connect_to_db()

    try:
        # Map 'Sí'/'No' to boolean values
        ascensor_boolean = True if ascensor == "Sí" else False
        parking_boolean = True if parking == "Sí" else False

        # Query to compute average monthly rent
        query = """
            SELECT barrio, AVG(precio) AS promedio_renta
            FROM alquileres
            WHERE habitaciones = %s
            AND banos = %s
            AND ascensor = %s
            AND parking = %s
            GROUP BY barrio
        """

        cursor.execute(query, (habitaciones, banos, ascensor_boolean, parking_boolean))
        data = pd.DataFrame(cursor.fetchall(), columns=["barrio", "promedio_renta"])

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
            SELECT barrio, AVG(precio) AS avg_apartment_cost
            FROM compras
            WHERE habitaciones = %s
            AND banos = %s
            AND ascensor = %s
            AND parking = %s
            GROUP BY barrio
        """

        cursor.execute(query, (habitaciones, banos, ascensor_boolean, parking_boolean))
        data = pd.DataFrame(cursor.fetchall(), columns=["barrio", "avg_apartment_cost"])

    except Exception as e:
        st.error(f"Database query error in purchase data fetch: {e}")
        data = pd.DataFrame()
    finally:
        cursor.close()
        conn.close()

    return data


# Streamlit App - Calculate Rentability
st.title("Apartment Rentability Analysis")

st.sidebar.header("Filter Options")

# Sidebar filters
num_habitaciones = st.sidebar.slider(
    "Select number of habitaciones:",
    min_value=1,
    max_value=5,
    value=3
)

num_banos = st.sidebar.slider(
    "Select number of baños:",
    min_value=1,
    max_value=3,
    value=1
)

ascensor = st.sidebar.selectbox(
    "Has elevator (ascensor)?", options=["Sí", "No"], index=0
)

parking = st.sidebar.selectbox(
    "Has parking?", options=["Sí", "No"], index=0
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
    analysis_df["Anual_Income"] = analysis_df["promedio_renta"] * 12
    analysis_df["Rentability_%"] = (analysis_df["Anual_Income"] / analysis_df["avg_apartment_cost"]) * 100

    # Sort the data by calculated rentability percentage
    analysis_df_sorted = analysis_df.sort_values(by="Rentability_%", ascending=False)

    # Display results
    st.write(f"Dynamic Rentability Analysis for {num_habitaciones} habitaciones, {num_banos} baños, elevator={ascensor}, parking={parking}:")
    st.table(analysis_df_sorted[["barrio", "promedio_renta", "avg_apartment_cost", "Anual_Income", "Rentability_%"]])
