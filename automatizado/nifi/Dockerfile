# Usa la imagen base de Apache NiFi
FROM apache/nifi:1.21.0

# Cambiar al usuario root para instalar dependencias
USER root

# Instalar herramientas necesarias (opcional)
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crear directorios necesarios
RUN mkdir -p /opt/nifi/scripts /opt/nifi/templates

# Copiar scripts y archivos necesarios al contenedor
COPY import-template.sh /opt/nifi/scripts/import-template.sh
COPY template.xml /opt/nifi/templates/template.xml
COPY init-nifi.sh /init-nifi.sh

# Hacer los scripts ejecutables
RUN chmod +x /opt/nifi/scripts/import-template.sh /init-nifi.sh

# Cambiar de vuelta al usuario NiFi
USER nifi

# Ejecutar el script maestro como comando de inicio
CMD ["/init-nifi.sh"]
