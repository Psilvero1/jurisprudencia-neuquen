import streamlit as st
import PyPDF2
import base64
import re
from supabase import create_client, Client

# Configuración de la página
st.set_page_config(page_title="Buscador de Jurisprudencia NQN", page_icon="⚖️", layout="wide")

# Conectar con la Base de Datos
@st.cache_resource
def init_conexion():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_conexion()

# Título
st.title("⚖️ Buscador de Jurisprudencia")
st.subheader("Provincia de Neuquén")
st.markdown("---")

# Las tres pestañas principales
tab1, tab2, tab3 = st.tabs(["🔍 Buscador Público", "📤 Aportar Jurisprudencia", "🔒 Aduana (Admin)"])

with tab1:
    st.write("### Búsqueda en Fallos Aprobados")
    
    query = st.text_input("Buscar palabra o frase (Ej: 'daño moral', 'bicicleta'):")
    
    if st.button("Buscar en la base de datos"):
        if not query:
            st.warning("Escribí algo en el buscador.")
        else:
            with st.spinner("Buscando en los archivos del juzgado..."):
                # Magia Supabase: Buscar solo los 'aprobados' que contengan la palabra (ilike no distingue mayúsculas)
                respuesta = supabase.table("fallos_nqn").select("*").eq("estado", "aprobado").ilike("texto_completo", f"%{query}%").execute()
                fallos_encontrados = respuesta.data
                
                if fallos_encontrados:
                    st.success(f"Se encontraron {len(fallos_encontrados)} fallos con esa coincidencia.")
                    for fallo in fallos_encontrados:
                        st.markdown(f"### 📄 `{fallo['nombre_archivo']}`")
                        
                        # Extraer un "pedacito" de texto para dar contexto
                        texto = fallo['texto_completo']
                        indice = texto.lower().find(query.lower())
                        
                        if indice != -1:
                            inicio = max(0, indice - 150)
                            fin = min(len(texto), indice + len(query) + 150)
                            fragmento = texto[inicio:fin]
                            fragmento_resaltado = re.sub(f"({re.escape(query)})", r"**\1**", fragmento, flags=re.IGNORECASE)
                            st.info(f"... {fragmento_resaltado} ...")
                        
                        # Botón de descarga original
                        b64 = fallo['archivo_b64']
                        href = f'''
                        <a href="data:application/pdf;base64,{b64}" download="{fallo['nombre_archivo']}"
                           style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #FF4B4B; text-decoration: none; border-radius: 4px; margin-bottom: 15px;">
                           ⬇️ Descargar Fallo Completo
                        </a>
                        '''
                        st.markdown(href, unsafe_allow_html=True)
                        st.markdown("---")
                else:
                    st.error("No se encontraron fallos públicos que contengan esa frase.")

with tab2:
    st.write("### Subir Nuevos Fallos")
    st.write("Los fallos subidos quedarán en estado 'Pendiente' hasta ser aprobados por moderación.")
    
    archivos_subidos = st.file_uploader("Arrastrá los fallos acá", type=["pdf"], accept_multiple_files=True)
    
    if archivos_subidos:
        if st.button("Enviar para Revisión"):
            with st.spinner("Procesando y enviando a la base de datos segura..."):
                for archivo in archivos_subidos:
                    try:
                        lector = PyPDF2.PdfReader(archivo)
                        texto_extraido = "".join([pagina.extract_text() for pagina in lector.pages if pagina.extract_text()])
                        
                        # Convertir el PDF original a texto para guardarlo en la base
                        pdf_b64 = base64.b64encode(archivo.getvalue()).decode('utf-8')
                        
                        # Enviar a Supabase con estado 'pendiente'
                        supabase.table("fallos_nqn").insert({
                            "nombre_archivo": archivo.name,
                            "texto_completo": texto_extraido,
                            "archivo_b64": pdf_b64,
                            "estado": "pendiente"
                        }).execute()
                        
                        st.success(f"✔️ '{archivo.name}' enviado con éxito.")
                    except Exception as e:
                        st.error(f"Error procesando {archivo.name}: {str(e)}")

with tab3:
    st.write("### ⚖️ Despacho Privado")
    clave = st.text_input("Ingresá la clave de administrador:", type="password")
    
    if clave == st.secrets["ADMIN_PASSWORD"]:
        st.success("Acceso autorizado.")
        
        # Buscar fallos que el público aún no puede ver
        respuesta = supabase.table("fallos_nqn").select("id, nombre_archivo").eq("estado", "pendiente").execute()
        pendientes = respuesta.data
        
        if pendientes:
            st.write(f"Tenés **{len(pendientes)}** fallos esperando tu aprobación:")
            
            for p in pendientes:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"📄 **{p['nombre_archivo']}**")
                
                if col2.button("✅ Aprobar", key=f"aprobar_{p['id']}"):
                    supabase.table("fallos_nqn").update({"estado": "aprobado"}).eq("id", p['id']).execute()
                    st.rerun()
                    
                if col3.button("❌ Rechazar", key=f"rechazar_{p['id']}"):
                    supabase.table("fallos_nqn").delete().eq("id", p['id']).execute()
                    st.rerun()
        else:
            st.info("No hay fallos pendientes de revisión en este momento.")
    elif clave:
        st.error("Contraseña incorrecta.")
