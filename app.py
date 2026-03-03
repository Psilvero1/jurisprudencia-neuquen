import streamlit as st
import google.generativeai as genai
import PyPDF2
import base64

# Nuevas herramientas profesionales para la Base de Datos Vectorial
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# Configurar las llaves y el modelo
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Configurar el motor de la Base de Datos Vectorial
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)

# --- NUEVA MEMORIA VECTORIAL ---
if 'vector_store' not in st.session_state:
    st.session_state['vector_store'] = None # Acá vivirá el índice inteligente
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
                    # 1. El buscador extrae SOLO los 5 fragmentos más relevantes de toda tu base
                    documentos_relevantes = st.session_state['vector_store'].similarity_search(query, k=5)
                    
                    # 2. Unimos esos pedacitos para dárselos a la IA
                    contexto_extraido = ""
                    archivos_citados = set() # Usamos un 'set' para no repetir nombres de botones
                    
                    for doc in documentos_relevantes:
                        nombre_origen = doc.metadata['source']
                        archivos_citados.add(nombre_origen)
                        contexto_extraido += f"\n--- Extraído de: {nombre_origen} ---\n{doc.page_content}\n"
                    
                    # 3. Le pasamos solo esa selección a la IA (Ahorro masivo de recursos)
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
                    
                    # --- FILTRO DE DESCARGAS ---
                    st.markdown("---")
                    st.write("### 📄 Fallos utilizados para esta respuesta:")
                    for nombre_archivo in archivos_citados:
                        # Verificamos si la IA realmente usó el texto de este archivo en su redacción
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
                    st.error(f"Hubo un error en la búsqueda. Asegurate de que los archivos estén bien cargados.")
        else:
            st.warning("Por favor, escribí una consulta antes de buscar.")

with tab2:
    st.write("### Indexación Silenciosa y Escalable")
    st.write("Subí archivos PDF sin preocuparte por el peso. El sistema los fragmentará y guardará en la base de datos sin consumir tu límite de resúmenes.")
    
    uploaded_files = st.file_uploader("Subí uno o varios fallos", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Indexar en la Base de Datos"):
            with st.spinner("Procesando, cortando e indexando... esto tomará unos segundos."):
                for uploaded_file in uploaded_files:
                    try:
                        # 1. Leer texto del PDF
                        lector_pdf = PyPDF2.PdfReader(uploaded_file)
                        texto_fallo = ""
                        for pagina in lector_pdf.pages:
                            extraido = pagina.extract_text()
                            if extraido:
                                texto_fallo += extraido
                        
                        # 2. CORTAR EN PEDACITOS (El secreto del éxito)
                        # Cortamos en bloques de 1000 letras, superponiendo 200 para no cortar ideas a la mitad
                        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        fragmentos = text_splitter.split_text(texto_fallo)
                        
                        # 3. Preparar las etiquetas (para saber de qué PDF viene cada pedacito)
                        docs = [Document(page_content=frag, metadata={"source": uploaded_file.name}) for frag in fragmentos]
                        
                        # 4. Guardar en la Base de Datos Vectorial (FAISS)
                        if st.session_state['vector_store'] is None:
                            st.session_state['vector_store'] = FAISS.from_documents(docs, embeddings)
                        else:
                            st.session_state['vector_store'].add_documents(docs)
                        
                        # 5. Guardar el archivo físico para descargas
                        st.session_state['archivos_pdf'][uploaded_file.name] = uploaded_file.getvalue()
                        st.session_state['cantidad_fallos'] += 1
                        
                        st.success(f"✔️ Fallo '{uploaded_file.name}' fragmentado e indexado correctamente ({len(fragmentos)} párrafos guardados).")
                        
                    except Exception as e:
                        st.error(f"⚠️ Error procesando {uploaded_file.name}. Verificá que el PDF sea de texto legible.")
                
                st.info("¡Proceso terminado! Ya podés ir a la Pestaña 1 para hacer tus consultas jurídicas.")
