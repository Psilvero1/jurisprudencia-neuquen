import streamlit as st
import PyPDF2
import base64
import re

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# --- MEMORIA LIVIANA ---
if 'base_fallos' not in st.session_state:
    st.session_state['base_fallos'] = {} # Acá guardamos el texto puro
if 'archivos_pdf' not in st.session_state:
    st.session_state['archivos_pdf'] = {} # Acá guardamos el archivo para descargar

# Título
st.title("⚖️ Buscador de Jurisprudencia")
st.subheader("Provincia de Neuquén")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Buscador por Palabras", "📤 Subir Expedientes"])

with tab1:
    st.write(f"Fallos disponibles en el sistema: **{len(st.session_state['base_fallos'])}**")
    
    # Buscador estilo Google (palabras exactas)
    query = st.text_input("Buscar palabra o frase (Ej: 'daño moral', 'artículo 41', 'bicicleta'):")
    
    if st.button("Buscar en los fallos"):
        if not st.session_state['base_fallos']:
            st.warning("⚠️ Primero tenés que subir fallos en la otra pestaña.")
        elif not query:
            st.warning("Escribí algo en el buscador.")
        else:
            resultados_encontrados = 0
            
            with st.spinner("Buscando coincidencias a la velocidad de la luz..."):
                for nombre_archivo, texto_completo in st.session_state['base_fallos'].items():
                    
                    # Si la palabra está en el texto de este fallo (ignorando mayúsculas/minúsculas)
                    if query.lower() in texto_completo.lower():
                        resultados_encontrados += 1
                        st.markdown(f"### 📄 Encontrado en: `{nombre_archivo}`")
                        
                        # Extraer un "pedacito" de texto alrededor de la palabra para dar contexto
                        coincidencias = [m.start() for m in re.finditer(re.escape(query.lower()), texto_completo.lower())]
                        
                        # Mostramos hasta 3 fragmentos donde aparezca la palabra
                        for indice in coincidencias[:3]:
                            inicio = max(0, indice - 150)
                            fin = min(len(texto_completo), indice + len(query) + 150)
                            fragmento = texto_completo[inicio:fin]
                            
                            # Resaltar la palabra buscada en negrita
                            fragmento_resaltado = re.sub(f"({re.escape(query)})", r"**\1**", fragmento, flags=re.IGNORECASE)
                            st.info(f"... {fragmento_resaltado} ...")
                        
                        # Botón de descarga rápida
                        bytes_archivo = st.session_state['archivos_pdf'][nombre_archivo]
                        b64 = base64.b64encode(bytes_archivo).decode()
                        href = f'''
                        <a href="data:application/pdf;base64,{b64}" download="{nombre_archivo}"
                           style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #FF4B4B; text-decoration: none; border-radius: 4px; margin-bottom: 15px;">
                           ⬇️ Descargar Fallo Completo
                        </a>
                        '''
                        st.markdown(href, unsafe_allow_html=True)
                        st.markdown("---")
                
                if resultados_encontrados == 0:
                    st.error("No se encontraron fallos que contengan esa palabra o frase exacta.")

with tab2:
    st.write("### Alimentar la Base de Datos")
    st.write("El sistema extraerá el texto de los PDFs para que puedan ser buscados instantáneamente.")
    
    archivos_subidos = st.file_uploader("Arrastrá los fallos acá", type=["pdf"], accept_multiple_files=True)
    
    if archivos_subidos:
        if st.button("Procesar e Indexar"):
            with st.spinner("Leyendo PDFs..."):
                for archivo in archivos_subidos:
                    try:
                        lector = PyPDF2.PdfReader(archivo)
                        texto_extraido = ""
                        for pagina in lector.pages:
                            extraido = pagina.extract_text()
                            if extraido:
                                texto_extraido += extraido
                        
                        # Guardar en la memoria rápida
                        st.session_state['base_fallos'][archivo.name] = texto_extraido
                        st.session_state['archivos_pdf'][archivo.name] = archivo.getvalue()
                        
                        st.success(f"✔️ {archivo.name} listo para buscar.")
                    except Exception as e:
                        st.error(f"Error leyendo {archivo.name}")
