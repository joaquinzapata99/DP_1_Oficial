#!/bin/bash

echo "Esperando a que NiFi se inicie..."
while ! curl -s -o /dev/null -w "%{http_code}" -k https://localhost:8443/nifi-api/system-diagnostics | grep -q "200"; do
  echo "NiFi no está disponible todavía..."
  sleep 60
done
echo "NiFi está activo."

echo "Subiendo el template..."
curl -k -X POST "https://localhost:8443/nifi-api/process-groups/root/templates/upload" \
  -H "Content-Type: multipart/form-data" \
  -u admin:ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB \
  -F "template=@/opt/nifi/templates/template.xml"

TEMPLATE_ID=$(curl -k -u admin:ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB \
  -X GET "https://localhost:8443/nifi-api/flow/templates" | jq -r '.templates[0].id')

echo "Template ID: $TEMPLATE_ID"

if [ -z "$TEMPLATE_ID" ]; then
  echo "Error: no se encontró el ID del template. Verifica el archivo template.xml."
  exit 1
fi

echo "Instanciando el template..."
curl -k -X POST "https://localhost:8443/nifi-api/process-groups/root/template-instance" \
  -u admin:ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB \
  -H "Content-Type: application/json" \
  -d "{\"templateId\":\"$TEMPLATE_ID\", \"originX\": 0, \"originY\": 0}"

echo "Iniciando el flujo..."
PROCESS_GROUP_ID=$(curl -k -u admin:ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB \
  -X GET "https://localhost:8443/nifi-api/flow/process-groups/root" | jq -r '.processGroupFlow.id')

curl -k -X PUT "https://localhost:8443/nifi-api/flow/process-groups/$PROCESS_GROUP_ID" \
  -u admin:ctsBtRBKHRAx69EqUghvvgEvjnaLjFEB \
  -H "Content-Type: application/json" \
  -d '{"id":"'"$PROCESS_GROUP_ID"'","state":"RUNNING"}'

echo "Flujo instanciado y ejecutándose."
