#!/bin/sh
set -e

# Wait a bit to ensure previous scripts have completed
echo "Waiting for database upload scripts to finish..."
sleep 30

# Run Streamlit
echo "Starting Streamlit application..."
streamlit run streamlit.py --server.port 8501 --server.address 0.0.0.0