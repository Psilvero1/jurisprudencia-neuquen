import streamlit as st
import google.generativeai as genai
import PyPDF2
import base64

# Herramientas de LangChain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# EL NUEVO MOTOR INDEPENDIENTE (Bypass a Google)
from langchain_community.embeddings import HuggingFaceEmbeddings

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# Configurar la llave SOLO para redactar las respuestas finales
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# AUTODETECCIÓN: Le preguntamos a Google qué modelo tenés habilitado
modelos_validos = []
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        modelos_validos.append(m.name.replace("models/", ""))

# Elegimos automáticamente el primer modelo que funcione en tu cuenta
modelo_elegido = modelos_validos[0] if modelos_validos else "gemini-1.5-flash"
model = genai.GenerativeModel(modelo_elegido)

# --- MOTOR DE LECTURA 100% GRATUITO Y LOCAL ---
# Usamos un modelo de HuggingFace optimizado para español
@st.cache_resource
def cargar_motor():
    return HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")

embeddings = cargar_motor()

# --- NUEVA MEMORIA VECTORIAL ---
if 'vector_store' not in st.session_state:
    st.session_state['vector_store'] = None
if 'archivos_pdf' not in st.session_state:
    st.session_state['archivos_pdf'] = {}
if 'cantidad_fallos' not in st.session_state:
    st.session_state['cantidad_fallos'] = 0

# Título principal
st.title("⚖️ Buscador Inteligente de Jurisprudencia")
st.subheader("Provincia de Neuquén")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Buscar en mis Fallos", "📤 Carga Silenciosa de Jurisprudencia"])

with tab1:
    st.write("### Buscador de Precisión (Vectorial)")
    st.write(f"Fallos indexados en la base actual: **{st.session_state['cantidad_fallos']}**")
    
    query = st.text_input("Escribí tu consulta jurídica (Ej: 'Doctrina sobre carga de la prueba'):")
    
    if st.button("Buscar en mi base de datos"):
        if st.session_state['vector_store'] is None:
            st.warning("⚠️ La base de datos está vacía. Subí jurisprudencia en la otra pestaña primero.")
        elif query:
            with st.spinner("Buscando los párrafos más exactos en tu archivo..."):
                try:
                    documentos_relevantes = st.session_state['vector_store'].similarity_search(query, k=5)
                    
                    contexto_extraido = ""
                    archivos_citados = set()
                    
                    for doc in documentos_relevantes:
                        nombre_origen = doc.metadata['source']
                        archivos_citados.add(nombre_origen)
                        contexto_extraido += f"\n--- Extraído de: {nombre_origen} ---\n{doc.page_content}\n"
                    
                    prompt_estricto = f"""Sos un asistente jurídico estricto. 
                    REGLA FUNDAMENTAL: Respondé a la consulta basándote ÚNICA Y EXCLUSIVAMENTE en los fragmentos de jurisprudencia extraídos que te proveo abajo.
                    Si la respuesta NO está en estos fragmentos, decí: 'No se encontraron respuestas a esta consulta en la jurisprudencia indexada'.
                    
                    MUY IMPORTANTE: Mencioná siempre de qué archivo/s sacaste la información.

                    --- FRAGMENTOS RELEVANTES EXTRAÍDOS ---
                    {contexto_extraido}
                    -----------------------------------------

                    Consulta del usuario: {query}"""
                    
                    respuesta = model.generate_content(prompt_estricto)
                    
                    st.success("Búsqueda completada:")
                    st.write(respuesta.text)
                    
                    st.markdown("---")
                    st.write("### 📄 Fallos utilizados para esta respuesta:")
                    for nombre_archivo in archivos_citados:
                        if nombre_archivo in respuesta.text and nombre_archivo in st.session_state['archivos_pdf']:
                            bytes_archivo = st.session_state['archivos_pdf'][nombre_archivo]
                            b64 = base64.b64encode(bytes_archivo).decode()
                            href = f'''
                            <a href="data:application/pdf;base64,{b64}" download="{nombre_archivo}"
                               style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #FF4B4B; text-decoration: none; border-radius: 4px; margin-bottom: 5px;">
                               ⬇️ Descargar {nombre_archivo}
                            </a><br><br>
                            '''
                            st.markdown(href, unsafe_allow_html=True)
                            
                except Exception as e:
                    st.error(f"Hubo un error en la búsqueda: {str(e)}")
        else:
            st.warning("Por favor, escribí una consulta antes de buscar.")

with tab2:
    st.write("### Indexación Silenciosa y Escalable")
    st.write("Subí archivos PDF. El nuevo motor local los fragmentará y guardará en la base de datos sin consumir tu cuota de Google.")
    
    uploaded_files = st.file_uploader("Subí uno o varios fallos", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Indexar en la Base de Datos"):
            with st.spinner("Procesando e indexando (la primera vez puede demorar unos segundos extra en arrancar el motor)..."):
                for uploaded_file in uploaded_files:
                    try:
                        lector_pdf = PyPDF2.PdfReader(uploaded_file)
                        texto_fallo = ""
                        for pagina in lector_pdf.pages:
                            extraido = pagina.extract_text()
                            if extraido:
                                texto_fallo += extraido
                        
                        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        fragmentos = text_splitter.split_text(texto_fallo)
                        
                        docs = [Document(page_content=frag, metadata={"source": uploaded_file.name}) for frag in fragmentos]
                        
                        if st.session_state['vector_store'] is None:
                            st.session_state['vector_store'] = FAISS.from_documents(docs, embeddings)
                        else:
                            st.session_state['vector_store'].add_documents(docs)
                        
                        st.session_state['archivos_pdf'][uploaded_file.name] = uploaded_file.getvalue()
                        st.session_state['cantidad_fallos'] += 1
                        
                        st.success(f"✔️ Fallo '{uploaded_file.name}' fragmentado e indexado correctamente ({len(fragmentos)} párrafos guardados).")
                        
                    except Exception as e:
                        st.error(f"⚠️ Error técnico con {uploaded_file.name}: {str(e)}")
                
                st.info("¡Proceso terminado! Ya podés ir a la Pestaña 1 para hacer tus consultas jurídicas.")
