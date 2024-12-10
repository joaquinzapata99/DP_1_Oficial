# DP_1_Oficial  

# Tindrahood 🔥

¡Bienvenido al proyecto **Tindrahood**! Este repositorio contiene toda la información, estructura y documentación necesaria para entender y colaborar en el desarrollo de esta aplicación revolucionaria. **Tindrahood** está destinada a tres objetivos principales:

1. 🏙️ **Encontrar el barrio ideal** aplicando filtros personalizados.
2. 🏠 **Subir pisos a la venta o alquiler** para conectar con potenciales interesados.
3. 💰 **Rentabilizar dinero mediante inversiones** en pisos de Valencia aplicando filtros avanzados para encontrar el piso ideal para invertir.

<img src="wlogo.png" alt="Description of the image" width="300" />

---

## 🏗️ **Estructura del Proyecto**

El proyecto está organizado en carpetas y archivos de forma clara y lógica para facilitar su mantenimiento y escalabilidad. A continuación, se detalla la estructura principal del proyecto:

📦 Tindrahood/

```plaintext
Python_scripts/          # Directorio principal del proyecto
├── IdeaDatos/           # Carpeta para los datos crudos, limpios y procesados
│   ├── alquiler_total.csv  # Datos de alquileres de pisos en Valencia
│   └── compras_total.csv   # Datos de pisos en Valencia en venta
│
├── pages/               # Carpeta con las páginas de la aplicación Streamlit
│   ├── 01Encuentra_tu_barrio.py  # Página donde el usuario busca su barrio ideal y conecta con postgres guardando los barrios ideales en nuestra BD
│   ├── 02Sube_tu_propiedad.py    # Página para subir pisos en venta o alquiler y conecta con postgres guardando los pisos en nuestra BD
│   └── 03Rentabilidad.py         # Página donde los usuarios invierten y rentabilizan su dinero
│
├── Bienvenido.py        # Archivo de bienvenida a la aplicación
├── docker-compose.yml   # Archivo para configuración de Docker Compose
├── dockerfile           # Archivo para construir la imagen Docker
├── entrypoint.sh        # Script de inicio para el contenedor Docker y orquestar el inicio de los scripts
├── init_postgis.sql     # Script para inicializar la base de datos y crear la extensión de postgis y postgis_topology
├── requirements.txt     # Archivo con las dependencias del proyecto
├── script.py            # Script donde se suben los centros educativos a postgres
├── scriptalquileres.py  # Script donde se toman los pisos en alquiler de el csv de alquiler_total.csv
├── scriptbarrios.py     # Script para subir los datos de barrios
├── scriptcompras.py     # Script donde se toman los pisos en venta de el csv de compras_total.csv
├── scriptdemanda.py     # Script para analizar la demanda de propiedades
├── scriptjuegos.py      # Script donde se suben las zonas infantiles a nuestra BD
├── scriptmetro.py       # Script subir las bocas de metro en Valencia en nuestra BD
├── scriptprecios.py     # Script para analizar y gestionar datos de precios
└── streamlit_entrypoint.sh  # Script de entrada para iniciar la aplicación Streamlit
```

---

## 🚀 **Guía paso a paso** 

### **1️⃣ Encontrar el barrio ideal**
- **Objetivo**: Ayudar a los usuarios a encontrar el barrio ideal donde vivir.
- **Acciones clave**:
  - Los usuarios podrán aplicar **filtros personalizados** (precio, servicios cercanos, transporte público, etc.).
  - La aplicación ofrece una **interfaz gráfica intuitiva** para la navegación y la selección.
  - Utilizamos **algoritmos de recomendación** para sugerir barrios relevantes.

---

### **2️⃣ Subir pisos a la venta o alquiler**
- **Objetivo**: Los usuarios pueden subir pisos en venta o alquiler, facilitando la oferta de inmuebles.
- **Acciones clave**:
  - Los usuarios pueden **registrar una propiedad** llenando un formulario con detalles (precio, ubicación, imágenes, etc.).

---

### **3️⃣ Rentabilizar dinero mediante inversiones**
- **Objetivo**: Ayudar a los usuarios a identificar **pisos en Valencia** que representen la mejor inversión.
- **Acciones clave**:
  - Los usuarios pueden aplicar **filtros de inversión** (retorno esperado, precio, tipo de propiedad, etc.).
  - La aplicación muestra una **lista priorizada** con los mejores pisos de inversión.
  - Se utilizan **modelos predictivos** que calculan la rentabilidad de cada inversión.

---

## **🚀 Ejecutar la aplicación**
Para iniciar la aplicación, utiliza el siguiente comando:
- docker-compose up --build 

Accecder a nuestro navegador y en el buscador poner:
- http://0.0.0.0:8501/

O también el siguiente: 
- http://loacalhost:8501/

---

## **📩 Contacto**
Si tienes dudas o sugerencias, no dudes en abrir un "issue" o ponerte en contacto con nosotros.

---

<img src="WhatsApp Image 2024-12-03 at 12.54.45.jpeg" alt="Description of the image" width="300" />

<img src="WhatsApp Image 2024-12-03 at 13.00.23.jpeg" alt="Description of the image" width="300" />

<img src="WhatsApp Image 2024-12-03 at 13.00.48.jpeg" alt="Description of the image" width="300" />

<img src="WhatsApp Image 2024-12-03 at 13.01.07.jpeg" alt="Description of the image" width="300" />
