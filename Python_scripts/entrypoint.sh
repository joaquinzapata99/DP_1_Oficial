#!/bin/sh
set -e  # Detiene el script si ocurre algún error

echo "Ejecutando script.py..."
python script.py

echo "Ejecutando scriptbarrios.py..."
python scriptbarrios.py

# Mantener el contenedor activo después de ejecutar los scripts
tail -f /dev/null
