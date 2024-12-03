#!/bin/bash

# Ruta al archivo nifi.properties
NIFI_PROPERTIES="/opt/nifi/nifi-current/conf/nifi.properties"

echo "Modificando configuración de NiFi..."

# Asegurarse de que NiFi no esté corriendo
/opt/nifi/nifi-current/bin/nifi.sh stop || true

# Crear una copia temporal y modificarla
echo "Creando copia temporal de nifi.properties..."
cp $NIFI_PROPERTIES /tmp/nifi.properties

# Modificar el valor de nifi.web.https.host
sed -i 's/^nifi.web.https.host=.*/nifi.web.https.host=/' /tmp/nifi.properties

# Reemplazar el archivo original con la copia modificada
echo "Reemplazando nifi.properties..."
mv /tmp/nifi.properties $NIFI_PROPERTIES

# Confirmar cambios
echo "Archivo nifi.properties actualizado:"
grep 'nifi.web.https.host' $NIFI_PROPERTIES

# Iniciar NiFi
echo "Iniciando Apache NiFi..."
/opt/nifi/nifi-current/bin/nifi.sh start

# Esperar a que NiFi esté activo
echo "Esperando a que NiFi esté activo..."
while ! curl -s -o /dev/null -k https://localhost:8443/nifi-api/system-diagnostics; do
  echo "NiFi no está listo. Reintentando en 10 segundos..."
  sleep 10
done
echo "NiFi está activo."

# Ejecutar el script de importación del template
echo "Ejecutando import-template.sh..."
/opt/nifi/scripts/import-template.sh

# Mantener el contenedor en ejecución
echo "NiFi configurado correctamente. Manteniendo el contenedor en ejecución..."
tail -f /opt/nifi/nifi-current/logs/nifi-app.log
