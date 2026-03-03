import streamlit as st
import google.generativeai as genai
import PyPDF2

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# Configurar la API de Gemini
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- NUEVO: CREAR LA MEMORIA DE LA APLICACIÓN ---
# Esto guardará los textos de los fallos mientras la página esté abierta
if 'memoria_fallos' not in st.session_state:
    st.session_state['memoria_fallos'] = ""
    st.session_state['cantidad_fallos'] = 0

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
            st.warning("⚠️ La base de datos está vacía. Por favor, andá a la pestaña de al lado y subí un fallo primero.")
        elif query:
            with st.spinner("Buscando respuestas estrictamente en tus fallos..."):
                # EL CANDADO: Instrucciones estrictas para que no invente
                prompt_estricto = f"""Sos un asistente jurídico estricto. 
                REGLA FUNDAMENTAL: Respondé a la consulta del usuario basándote ÚNICA Y EXCLUSIVAMENTE en el texto de los fallos que te proveo a continuación.
                Si la respuesta a la consulta NO se encuentra en este texto, tu única respuesta debe ser: 'No se encontraron respuestas a esta consulta en los fallos cargados en la base de datos actual'.
                NO uses conocimiento externo, NO inventes jurisprudencia.

                --- TEXTO DE LOS FALLOS EN LA BASE DE DATOS ---
                {st.session_state['memoria_fallos']}
                -----------------------------------------------

                Consulta del usuario: {query}"""
                
                respuesta = model.generate_content(prompt_estricto)
                st.success("Búsqueda completada:")
                st.write(respuesta.text)
        else:
            st.warning("Por favor, escribí una consulta antes de buscar.")

with tab2:
    st.write("### Carga y Resumen Automático de Fallos")
    st.write("Subí una sentencia en PDF. La IA la leerá, la resumirá de forma estricta y la guardará en la memoria para que puedas buscarla en la otra pestaña.")
    uploaded_file = st.file_uploader("Subí un fallo en formato PDF", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Leer, Resumir y Guardar en Memoria"):
            with st.spinner("Procesando el expediente de forma estricta..."):
                try:
                    # Leer el texto del PDF
                    lector_pdf = PyPDF2.PdfReader(uploaded_file)
                    texto_fallo = ""
                    for pagina in lector_pdf.pages:
                        texto_fallo += pagina.extract_text()
                    
                    # Guardar en la memoria temporal para el buscador de la Pestaña 1
                    st.session_state['memoria_fallos'] += f"\n\n--- INICIO FALLO: {uploaded_file.name} ---\n{texto_fallo}\n--- FIN FALLO ---\n"
                    st.session_state['cantidad_fallos'] += 1
                    
                    # Pedirle a Gemini que lo resuma con EL CANDADO
                    prompt_resumen = f"""Sos un abogado relator estricto de la provincia de Neuquén. 
                    REGLA FUNDAMENTAL: Basate ÚNICAMENTE en el texto de la sentencia provista abajo. NO inventes datos que no estén en el texto.
                    
                    Hacé un resumen estructurado con:
                    1. Autos (Carátula)
                    2. Hechos principales
                    3. Doctrina y Fundamentos jurídicos aplicados
                    4. Resolución (Fallo)
                    
                    Texto de la sentencia:
                    {texto_fallo}"""
                    
                    respuesta_resumen = model.generate_content(prompt_resumen)
                    
                    st.success(f"¡Fallo '{uploaded_file.name}' procesado y guardado en la base de datos temporal!")
                    st.write("### Resumen Inteligente Estricto")
                    st.write(respuesta_resumen.text)
                except Exception as e:
                    st.error(f"Hubo un error al procesar el archivo. Asegurate de que sea un PDF de texto legible.")
