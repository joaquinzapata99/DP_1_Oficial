#!/bin/sh
set -e  # Detiene el script si ocurre algún error

echo "Ejecutando script.py..."
python script.py

echo "Ejecutando barrios.py..."
python scriptbarrios.py

echo "Ejecutando metros..."
python scriptmetro.py 

echo "Ejecutando compras..."
python scriptcompras.py

echo "Ejecutando precios..."
python scriptprecios.py

echo "Ejecutando alquileres..."
python scriptalquileres.py

echo "Ejecutando demanda..."
python scriptdemanda.py

echo "Ejecutando parques infantiles"
python scriptjuegos.py

# Mantener el contenedor activo después de ejecutar los scripts
tail -f /dev/null