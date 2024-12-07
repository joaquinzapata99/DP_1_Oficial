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

# Mantener el contenedor activo después de ejecutar los scripts
tail -f /dev/null