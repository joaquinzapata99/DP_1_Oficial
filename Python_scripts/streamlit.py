import streamlit as st
import pandas as pd
import geopandas as gpd
import pg8000
import time
from streamlit_folium import st_folium
import folium
from sqlalchemy import create_engine
import sqlalchemy

# Enhanced Database Configuration
DB_CONFIG = {
    "host": "postgres_container",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

def create_sqlalchemy_engine():
    """Create SQLAlchemy engine using pg8000 dialect"""
    connection_string = f"postgresql+pg8000://postgres:postgres@postgres_container:5432/postgres"
    return create_engine(connection_string)

def fetch_data(table_name):
    """Fetch data from PostgreSQL with enhanced error handling"""
    try:
        # Use SQLAlchemy engine for connection
        engine = create_sqlalchemy_engine()
        
        # Dynamically determine the geometry column
        # First, get the column names
        columns_query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
        columns = pd.read_sql(columns_query, engine)
        
        # Find geometry columns (assuming they contain 'geo' or 'shape')
        geo_columns = columns[columns['column_name'].str.contains('geo|shape', case=False)]['column_name'].tolist()
        
        if not geo_columns:
            st.error(f"No geometry column found in table {table_name}")
            return None
        
        # Try reading with each potential geometry column
        for geo_col in geo_columns:
            try:
                query = f"SELECT * FROM {table_name} LIMIT 500;"
                data = gpd.read_postgis(query, engine, geom_col=geo_col)
                st.success(f"Successfully read data using geometry column: {geo_col}")
                return data
            except Exception as inner_e:
                st.warning(f"Failed to read with column {geo_col}: {inner_e}")
        
        st.error("Could not read spatial data from any geometry column")
        return None
    
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return None

def create_map(metro_data, barrios_data, filter_metro_stations_only):
    """Create an interactive Folium map"""
    m = folium.Map(location=[39.4699, -0.3763], zoom_start=12)  

    # Color schemes
    metro_color = 'red'
    barrios_color = 'blue'
    selected_color = 'green'

    # Plot metro stations
    for _, row in metro_data.iterrows():
        try:
            geo_col = [col for col in row.index if 'geo' in col.lower() or 'point' in col.lower()][0]
            point = row[geo_col]
            
            if not point.is_empty:
                folium.CircleMarker(
                    location=[point.y, point.x],
                    radius=5,
                    popup=row.get("name", "Metro Station"),
                    color=metro_color,
                    fill=True,
                    fillColor=metro_color
                ).add_to(m)
        except Exception as e:
            st.warning(f"Error plotting metro station: {e}")

    # Plot barrios (districts)
    for _, row in barrios_data.iterrows():
        try:
            geo_col = [col for col in row.index if 'geo' in col.lower() or 'shape' in col.lower()][0]
            geometry = row[geo_col]
            
            # Get the neighborhood name using 'nombre' column
            neighborhood_name = row.get("nombre", None)
            
            # Filter neighborhoods that have metro stations inside them if filter is enabled
            if filter_metro_stations_only:
                # Check if metro station exists within this barrio
                metros_in_barrio = metro_data[metro_data.geometry.within(geometry)]
                if not metros_in_barrio.empty:
                    # If metro station is inside the neighborhood, plot it
                    if geometry.geom_type in ['Polygon', 'MultiPolygon']:
                        geo_json = folium.GeoJson(
                            geometry.__geo_interface__,
                            popup=row.get("nombre", "Barrio"),
                            style_function=lambda feature: {
                                'fillColor': selected_color,
                                'fillOpacity': 0.5,
                                'weight': 1,
                                'color': selected_color
                            }
                        )
                        geo_json.add_to(m)
                    elif not geometry.is_empty:
                        folium.CircleMarker(
                            location=[geometry.y, geometry.x],
                            radius=3,
                            popup=row.get("nombre", "Barrio"),
                            color=selected_color,
                            fill=True,
                            fillColor=selected_color
                        ).add_to(m)
            else:
                # If filter is off, show all barrios
                if geometry.geom_type in ['Polygon', 'MultiPolygon']:
                    geo_json = folium.GeoJson(
                        geometry.__geo_interface__,
                        popup=row.get("nombre", "Barrio"),
                        style_function=lambda feature: {
                            'fillColor': barrios_color,
                            'fillOpacity': 0.5,
                            'weight': 1,
                            'color': barrios_color
                        }
                    )
                    geo_json.add_to(m)
                elif not geometry.is_empty:
                    folium.CircleMarker(
                        location=[geometry.y, geometry.x],
                        radius=3,
                        popup=row.get("nombre", "Barrio"),
                        color=barrios_color,
                        fill=True,
                        fillColor=barrios_color
                    ).add_to(m)
        except Exception as e:
            st.warning(f"Error plotting barrio: {e}")

    return m

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Valencia Metro and Barrios Viewer", 
        page_icon=":metro:", 
        layout="wide"
    )

    # App title and description
    st.title("🚇 Valencia Metro and Barrios Mapping")
    st.markdown("""
    ### Interactive Geospatial Visualization
    Explore the metro stations and neighborhoods of Valencia through an interactive map.
    """)

    # Fetch data from PostgreSQL
    with st.spinner('Fetching geographic data...'):
        metro_data = fetch_data("paradas_metro")
        barrios_data = fetch_data("barrios_valencia")

    # Check if data was successfully fetched
    if metro_data is not None and barrios_data is not None:
        # Sidebar filter to show only neighborhoods with metro stations
        filter_metro_stations_only = st.sidebar.checkbox(
            "Show only neighborhoods with metro stations", value=False
        )

        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["Map", "Metro Stations", "Barrios"])

        with tab1:
            st.subheader("Interactive Map")
            # Create and display map
            m = create_map(metro_data, barrios_data, filter_metro_stations_only)
            st_folium(m, width=900, height=600)

        with tab2:
            st.subheader("Metro Stations Details")
            st.dataframe(metro_data)

        with tab3:
            st.subheader("Barrios Details")
            st.dataframe(barrios_data)

    else:
        st.error("Failed to retrieve geographic data. Please check your database connection.")

if __name__ == "__main__":
    main()
