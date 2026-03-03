import streamlit as st
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# Configurar la API de Gemini usando los "Secretos" de Streamlit
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Título y encabezado principal
st.title("⚖️ Buscador Inteligente de Jurisprudencia")
st.subheader("Provincia de Neuquén")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Buscar Fallos", "📤 Subir Jurisprudencia"])

with tab1:
    st.write("### Buscador potenciado por IA")
    st.write("Hacé tu consulta jurídica con lenguaje natural. (En esta etapa de prueba, la IA responderá en base a su conocimiento general sobre derecho de fondo y forma local).")
    
    query = st.text_input("Escribí tu consulta (Ej: 'Doctrina sobre daño moral en accidentes de tránsito'):")
    
    if st.button("Buscar jurisprudencia"):
        if query:
            with st.spinner("Analizando doctrina y jurisprudencia..."):
                # Le damos a la IA el rol de asistente jurídico local
                prompt_completo = f"Sos un asistente jurídico experto en derecho civil, comercial y procesal de la provincia de Neuquén. Respondé a esta consulta de manera profesional y sucinta: {query}"
                
                respuesta = model.generate_content(prompt_completo)
                
                st.success("Análisis completado:")
                st.write(respuesta.text)
        else:
            st.warning("Por favor, escribí una consulta antes de buscar.")

with tab2:
    st.write("### Carga Colaborativa de Fallos")
    st.write("Aportá fallos novedosos de los juzgados o cámaras de Neuquén.")
    uploaded_file = st.file_uploader("Subí un fallo en formato PDF o Word", type=["pdf", "doc", "docx"])
    
    if uploaded_file is not None:
        st.success("¡Archivo recibido exitosamente! Pronto implementaremos la base de datos para guardarlo.")
