import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Aduana de Jurisprudencia", page_icon="🔒")

# Protección de entrada
clave = st.text_input("Contraseña de Administrador", type="password")
if clave == st.secrets["ADMIN_PASSWORD"]: # Usa la clave "pedrote_garrote_2026" guardada en Secrets
    st.title("⚖️ Despacho de Moderación")
    
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    
    # Ver pendientes
    respuesta = supabase.table("fallos_nqn").select("id, nombre_archivo").eq("estado", "pendiente").execute()
    
    if respuesta.data:
        for p in respuesta.data:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"📄 {p['nombre_archivo']}")
            if col2.button("✅ Aprobar", key=f"ap_{p['id']}"):
                supabase.table("fallos_nqn").update({"estado": "aprobado"}).eq("id", p['id']).execute()
                st.rerun()
            if col3.button("❌ Rechazar", key=f"re_{p['id']}"):
                supabase.table("fallos_nqn").delete().eq("id", p['id']).execute()
                st.rerun()
    else:
        st.info("No hay fallos pendientes.")
else:
    if clave: st.error("Acceso denegado.")
