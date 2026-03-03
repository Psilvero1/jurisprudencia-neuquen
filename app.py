import streamlit as st
import google.generativeai as genai
import PyPDF2
import base64
import time  # NUEVA HERRAMIENTA para hacer pausas y no saturar la API

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# Configurar la API de Gemini
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- MEMORIA AMPLIADA ---
if 'memoria_fallos' not in st.session_state:
    st.session_state['memoria_fallos'] = ""
    st.session_state['cantidad_fallos'] = 0
    st.session_state['archivos_pdf'] = {}

# Título y encabezado principal
st.title("⚖️ Buscador Inteligente de Jurisprudencia")
st.subheader("Provincia de Neuquén")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Buscar en mis Fallos", "📤 Subir y Resumir Jurisprudencia"])

with tab1:
    st.write("### Buscador con 'Candado' (Grounding)")
    st.write(f"Fallos cargados en la memoria actual: **{st.session_state['cantidad_fallos']}**")
    
    query = st.text_input("Escribí tu consulta:")
    
    if st.button("Buscar en mi base de datos"):
        if st.session_state['cantidad_fallos'] == 0:
            st.warning("⚠️ La base de datos está vacía. Por favor, andá a la pestaña de al lado y subí jurisprudencia primero.")
        elif query:
            with st.spinner("Buscando respuestas estrictamente en tus fallos..."):
                prompt_estricto = f"""Sos un asistente jurídico estricto. 
                REGLA FUNDAMENTAL: Respondé a la consulta del usuario basándote ÚNICA Y EXCLUSIVAMENTE en el texto de los fallos que te proveo a continuación.
                Si la respuesta NO se encuentra en este texto, tu única respuesta debe ser: 'No se encontraron respuestas a esta consulta en los fallos cargados en la base de datos actual'.
                NO uses conocimiento externo, NO inventes jurisprudencia.
                
                MUY IMPORTANTE: Al final de tu respuesta, DEBES indicar el nombre exacto del archivo o archivos de los fallos que utilizaste para responder.

                --- TEXTO DE LOS FALLOS EN LA BASE DE DATOS ---
                {st.session_state['memoria_fallos']}
                -----------------------------------------------

                Consulta del usuario: {query}"""
                
                try:
                    respuesta = model.generate_content(prompt_estricto)
                    st.success("Búsqueda completada:")
                    st.write(respuesta.text)
                    
                    st.markdown("---")
                    st.write("### 📄 Fallos citados en esta respuesta:")
                    
                    archivos_mostrados = 0
                    for nombre_archivo, bytes_archivo in st.session_state['archivos_pdf'].items():
                        if nombre_archivo in respuesta.text:
                            b64 = base64.b64encode(bytes_archivo).decode()
                            href = f'''
                            <a href="data:application/pdf;base64,{b64}" download="{nombre_archivo}"
                               style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #FF4B4B; text-decoration: none; border-radius: 4px; margin-bottom: 5px;">
                               ⬇️ Descargar {nombre_archivo}
                            </a><br><br>
                            '''
                            st.markdown(href, unsafe_allow_html=True)
                            archivos_mostrados += 1
                    
                    if archivos_mostrados == 0:
                        st.info("No hay archivos específicos para descargar vinculados a esta consulta.")
                        
                except Exception as e:
                    st.error("⚠️ La Inteligencia Artificial se saturó temporalmente por exceso de datos. Por favor, esperá 1 minuto y volvé a intentar buscar.")

        else:
            st.warning("Por favor, escribí una consulta antes de buscar.")

with tab2:
    st.write("### Carga y Resumen Automático Múltiple")
    uploaded_files = st.file_uploader("Subí uno o varios fallos en formato PDF", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Leer, Resumir y Guardar en Memoria"):
            with st.spinner("Procesando los expedientes... esto puede tomar unos minutos dependiendo de la cantidad."):
                for uploaded_file in uploaded_files:
                    try:
                        lector_pdf = PyPDF2.PdfReader(uploaded_file)
                        texto_fallo = ""
                        for pagina in lector_pdf.pages:
                            texto_fallo += pagina.extract_text()
                        
                        st.session_state['memoria_fallos'] += f"\n\n--- INICIO FALLO: {uploaded_file.name} ---\n{texto_fallo}\n--- FIN FALLO ---\n"
                        st.session_state['cantidad_fallos'] += 1
                        st.session_state['archivos_pdf'][uploaded_file.name] = uploaded_file.getvalue()
                        
                        prompt_resumen = f"""Sos un abogado relator estricto de la provincia de Neuquén. 
                        REGLA FUNDAMENTAL: Basate ÚNICAMENTE en el texto de la sentencia provista abajo. NO inventes datos.
                        
                        Hacé un resumen estructurado con:
                        1. Autos (Carátula)
                        2. Hechos principales
                        3. Doctrina y Fundamentos jurídicos aplicados
                        4. Resolución (Fallo)
                        
                        Texto de la sentencia:
                        {texto_fallo}"""
                        
                        respuesta_resumen = model.generate_content(prompt_resumen)
                        
                        st.success(f"¡Fallo '{uploaded_file.name}' procesado y guardado!")
                        with st.expander(f"Ver resumen inteligente de {uploaded_file.name}"):
                            st.write(respuesta_resumen.text)
                        
                        # --- EL FRENO AUTOMÁTICO ---
                        # Obligamos al sistema a esperar 4 segundos antes de procesar el próximo archivo
                        time.sleep(4)
                            
                    except Exception as e:
                        st.error(f"⚠️ Error procesando {uploaded_file.name}. Si es por saturación de cuota, intentá subir menos archivos a la vez.")
