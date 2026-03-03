import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# Título y encabezado principal
st.title("⚖️ Buscador Inteligente de Jurisprudencia")
st.subheader("Provincia de Neuquén")
st.markdown("---")

# Crear pestañas para organizar la página
tab1, tab2 = st.tabs(["🔍 Buscar Fallos", "📤 Subir Jurisprudencia"])

# Contenido de la Pestaña 1: Buscador
with tab1:
    st.write("### Buscador potenciado por IA")
    st.write("Hacé tu consulta jurídica con lenguaje natural. El sistema buscará en la base de datos y resumirá la doctrina aplicable.")
    
    # Barra de búsqueda
    query = st.text_input("Escribí tu consulta (Ej: 'Fallo reciente sobre división de bienes en la provincia'):")
    
    # Botón de buscar
    if st.button("Buscar jurisprudencia"):
        st.info("⏳ Pronto conectaremos el cerebro de Inteligencia Artificial para responder a esta consulta.")

# Contenido de la Pestaña 2: Carga de archivos
with tab2:
    st.write("### Carga Colaborativa de Fallos")
    st.write("Aportá fallos novedosos de los juzgados o cámaras de Neuquén para enriquecer nuestra base de datos.")
    
    # Subidor de archivos
    uploaded_file = st.file_uploader("Subí un fallo en formato PDF o Word", type=["pdf", "doc", "docx"])
    
    if uploaded_file is not None:
        st.success("¡Archivo recibido exitosamente! (En la próxima etapa, esto se enviará a tu bandeja de revisión para ser aprobado).")
