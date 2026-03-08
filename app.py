import streamlit as st
import PyPDF2
import base64
import re
from supabase import create_client, Client

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# Conectar con Supabase
@st.cache_resource
def init_conexion():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_conexion()

# Título y Bienvenida
st.title("⚖️ Buscador de Jurisprudencia")
st.subheader("Provincia de Neuquén & CSJN")

st.info("""
**¡Colaborá con la Comunidad Jurídica!** 🤝  
Invitamos a todos los colegas a aportar fallos novedosos de la **Provincia de Neuquén** o de la **CSJN** que consideren útiles para el ejercicio profesional en nuestra región.
""")

tab1, tab2 = st.tabs(["🔍 Buscador Público", "📤 Aportar Jurisprudencia"])

with tab1:
    st.write("### Búsqueda en Fallos Aprobados")
    query = st.text_input("Buscar palabra o frase:")
    
    if st.button("Buscar"):
        if query:
            respuesta = supabase.table("fallos_nqn").select("*").eq("estado", "aprobado").ilike("texto_completo", f"%{query}%").execute()
            if respuesta.data:
                for fallo in respuesta.data:
                    st.markdown(f"### 📄 `{fallo['nombre_archivo']}`")
                    # Lógica de resaltado
                    texto = fallo['texto_completo']
                    indice = texto.lower().find(query.lower())
                    if indice != -1:
                        inicio = max(0, indice - 150)
                        fin = min(len(texto), indice + len(query) + 150)
                        fragmento_resaltado = re.sub(f"({re.escape(query)})", r"**\1**", texto[inicio:fin], flags=re.IGNORECASE)
                        st.info(f"... {fragmento_resaltado} ...")
                    
                    b64 = fallo['archivo_b64']
                    href = f'<a href="data:application/pdf;base64,{b64}" download="{fallo["nombre_archivo"]}" style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #FF4B4B; text-decoration: none; border-radius: 4px; margin-bottom: 15px;">⬇️ Descargar Fallo</a>'
                    st.markdown(href, unsafe_allow_html=True)
            else:
                st.error("No se encontraron resultados.")

with tab2:
    st.write("### Subir Nuevos Fallos")
    archivos = st.file_uploader("Subir PDFs", type=["pdf"], accept_multiple_files=True)
    if archivos and st.button("Enviar para Revisión"):
        for archivo in archivos:
            lector = PyPDF2.PdfReader(archivo)
            texto = "".join([p.extract_text() for p in lector.pages if p.extract_text()])
            pdf_b64 = base64.b64encode(archivo.getvalue()).decode('utf-8')
            supabase.table("fallos_nqn").insert({"nombre_archivo": archivo.name, "texto_completo": texto, "archivo_b64": pdf_b64, "estado": "pendiente"}).execute()
            st.success(f"✔️ '{archivo.name}' enviado.")
