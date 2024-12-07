import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Tindralencia 🔥",
    page_icon=":house:",
    layout="wide"
)

# Título principal
st.title("Bienvenido/a a la Guía Interactiva de Barrios de Valencia :cityscape:")

# Subtítulo o descripción
st.markdown("""
¡Hola! En esta aplicación encontrarás toda la información necesaria para **encontrar el barrio ideal en Valencia**, ya sea que estés buscando comprar o alquilar una vivienda.
""")


# Explicación de las funcionalidades
st.markdown("""
### ¿Qué podrás hacer en las siguientes páginas?

- **Filtrar Barrios:**  
  Aplica filtros basados en tus criterios: cercanía a centros educativos, acceso a transporte público (metro), nivel de seguridad, y más.
  
- **Ver Viviendas Disponibles:**  
  Encuentra viviendas en venta o alquiler en los barrios que más se ajusten a tus necesidades.
  
- **Información Detallada de los Barrios:**  
  Descubre datos clave sobre cada barrio, como índices de criminalidad, disponibilidad de servicios, escuelas cercanas, conexiones de transporte y otras estadísticas relevantes.
""")

# Consejo de navegación
st.markdown("""
### ¿Cómo navegar?
Utiliza el menú en la barra lateral (arriba a la izquierda) para acceder a las diferentes secciones de la aplicación. Cada página te ofrecerá opciones interactivas y visualizaciones que te ayudarán a tomar una decisión informada.

¡Esperamos que disfrutes la experiencia y encuentres el barrio perfecto para tu nuevo hogar! :house_with_garden:
""")

# Espacio para hacerlo más "limpio"
st.write("")
st.write("")

# Puedes añadir un botón para dirigir a las otras páginas, si lo deseas, pero no es obligatorio.
# Por ejemplo, si has configurado páginas multipágina, aparecerán automáticamente en el menú lateral.
# Si quieres poner un link a una página externa o un PDF, puedes usar st.markdown con enlace directo.
