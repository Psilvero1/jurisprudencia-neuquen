import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Aduana de Jurisprudencia", page_icon="🔒")

# Protección de entrada con tu clave: pedrote_garrote_2026
clave = st.text_input("Contraseña de Administrador", type="password")

if clave == st.secrets["ADMIN_PASSWORD"]:
    st.title("⚖️ Despacho de Moderación y Control")
    
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    # --- SECCIÓN 1: PENDIENTES DE APROBACIÓN ---
    st.subheader("📥 Fallos en Sala de Espera")
    res_pendientes = supabase.table("fallos_nqn").select("*").eq("estado", "pendiente").execute()
    
    if res_pendientes.data:
        for p in res_pendientes.data:
            with st.expander(f"Revisar: {p['nombre_archivo']}"):
                # NUEVA FUNCIÓN: Previsualización del texto
                if st.button("👁️ Previsualizar Texto", key=f"pre_{p['id']}"):
                    st.text_area("Contenido extraído:", value=p['texto_completo'], height=300, key=f"txt_{p['id']}")
                
                # Opción para RENOMBRAR antes de aprobar
                nuevo_nombre = st.text_input("Editar nombre del fallo:", value=p['nombre_archivo'], key=f"edit_{p['id']}")
                
                col1, col2 = st.columns(2)
                if col1.button("✅ Aprobar", key=f"ap_{p['id']}"):
                    supabase.table("fallos_nqn").update({
                        "estado": "aprobado", 
                        "nombre_archivo": nuevo_nombre
                    }).eq("id", p['id']).execute()
                    st.success(f"Fallo '{nuevo_nombre}' publicado.")
                    st.rerun()
                
                if col2.button("❌ Rechazar", key=f"re_{p['id']}"):
                    supabase.table("fallos_nqn").delete().eq("id", p['id']).execute()
                    st.warning("Archivo descartado.")
                    st.rerun()
    else:
        st.info("No hay archivos nuevos para revisar.")

    st.markdown("---")

    # --- SECCIÓN 2: GESTIÓN DE FALLOS PÚBLICOS ---
    st.subheader("📚 Gestión de Fallos Ya Publicados")
    res_aprobados = supabase.table("fallos_nqn").select("id, nombre_archivo").eq("estado", "aprobado").execute()
    
    if res_aprobados.data:
        for a in res_aprobados.data:
            col_n, col_b = st.columns([4, 1])
            col_n.write(f"📄 {a['nombre_archivo']}")
            if col_b.button("🗑️ Eliminar", key=f"del_{a['id']}"):
                supabase.table("fallos_nqn").delete().eq("id", a['id']).execute()
                st.error(f"Se eliminó '{a['nombre_archivo']}' del buscador público.")
                st.rerun()
    else:
        st.write("Aún no hay fallos aprobados.")
else:
    if clave: st.error("Acceso denegado.")
