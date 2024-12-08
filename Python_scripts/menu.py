import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Tindrahood 🔥",
    page_icon=":house_with_garden:",
    layout="wide"
)

# Título principal
st.title("¡Bienvenido a Tindrahood, tu guía definitiva para encontrar, invertir y ofrecer viviendas! :cityscape:")

# Subtítulo o introducción
st.markdown("""
En **Tindrahood**, te ofrecemos una experiencia única para encontrar el barrio perfecto, poner tu vivienda en alquiler o descubrir cómo invertir de forma inteligente en bienes raíces. 
¡Todo en un solo lugar y con una navegación sencilla e intuitiva! 🚀
""")

# Explicación general de las funcionalidades principales
st.markdown("""
## 🌟 ¿Qué encontrarás en Tindrahood?
Con Tindrahood, tendrás acceso a tres secciones principales diseñadas para cubrir todas tus necesidades en el sector inmobiliario. Aquí te las presentamos:
""")

# Sección 1: Filtrar Barrios
st.markdown("""
### 🏙️ **1. Filtrar y Encuentra tu Barrio Ideal** 
¿Buscas un barrio que se adapte a tu estilo de vida? ¡Aquí lo encontrarás!  
Podrás aplicar filtros personalizados para encontrar el barrio perfecto según tus preferencias, como:  
- **Acceso a transporte público (metro, autobús, etc.)** 🚉  
- **Proximidad a colegios y centros educativos** 🎓  
- **Nivel de seguridad del barrio** 🚨  
- **Acceso a servicios esenciales (supermercados, centros de salud, etc.)** 🏥🛒  

Con esta herramienta, ahorrarás tiempo y esfuerzo en la búsqueda de tu hogar ideal. ¡Encuentra tu lugar perfecto en la ciudad!  
""")

# Sección 2: Ofrecer tu Vivienda en Alquiler
st.markdown("""
### 🏠 **2. Ofrece tu Vivienda en Alquiler**  
¿Tienes una propiedad que quieres poner en alquiler? ¡Hazlo fácil con Tindrahood!  
En esta sección, podrás describir todas las características de tu vivienda para hacerla irresistible a posibles inquilinos:  
- **Sube fotos de tu vivienda** 📸  
- **Especifica detalles importantes** (número de habitaciones, baños, metros cuadrados, etc.) 📐  
- **Describe los servicios adicionales** (piscina, terraza, garaje, etc.) 🌴🚗  

¡Haz que tu propiedad se destaque en el mercado y encuentra a los mejores inquilinos!  
""")

# Sección 3: Invertir en Viviendas y Rentabilizar tu Dinero
st.markdown("""
### 💸 **3. Invierte y Haz Crecer tu Dinero con Viviendas en Alquiler**  
¿Te interesa invertir en el sector inmobiliario pero no sabes por dónde empezar? ¡Nosotros te guiamos!  
Accede a una lista de propiedades en venta recopiladas de plataformas como **Idealista** y otras fuentes. Aquí verás:  
- **Propiedades con alta rentabilidad potencial** 📈  
- **Precio de compra y previsión de ingresos por alquiler** 💰  
- **Cálculo automático de la rentabilidad estimada** 📊  

Deja de preguntarte dónde invertir tu dinero y toma decisiones informadas con datos reales y precisos. ¡Conviértete en un inversor inteligente!  
""")

# Consejo de navegación
st.markdown("""
## 🔍 **¿Cómo navegar por Tindrahood?**  
Utiliza el menú de la barra lateral (arriba a la izquierda) para acceder a las diferentes secciones. Cada una de ellas está diseñada para ofrecerte una experiencia interactiva y personalizada.  
👉 **Encuentra tu barrio ideal** para comprar o alquilar.  
👉 **Ofrece tu vivienda** y muestra su mejor versión.  
👉 **Invierte con seguridad** en propiedades con alta rentabilidad.  

Disfruta de una experiencia fácil, eficiente y personalizada con Tindrahood. ¡Elige el camino que mejor se adapte a tus necesidades y alcanza tus objetivos inmobiliarios!  
""")

# Espacio extra para hacerlo más limpio visualmente
st.write("")
st.write("")

# Llamada a la acción final
st.markdown("""
## 🚀 **¡Empieza ahora y descubre todo lo que Tindrahood tiene para ofrecerte!**  
Ya sea que busques hogar, quieras alquilar tu propiedad o desees invertir, aquí encontrarás la mejor solución.  
¡Con Tindrahood, el sector inmobiliario nunca fue tan accesible! 🏡💪  
""")
