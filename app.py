# app.py

import streamlit as st
from app.session_state import obtener_estado, cerrar_sesion
from app.auth import mostrar_login, mostrar_registro
from app.db import init_db

# === Inicializa la base de datos (crear tablas si no existen) ===
init_db()

# === Configurar página ===
st.set_page_config(page_title="Dashboards Académicos", layout="wide")

# === Cargar CSS externo ===
with open("app/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Obtener estado de sesión ===
estado = obtener_estado()

# === Encabezado institucional ===
st.markdown(
    """
    <div class="header-logos">
        <img src="app/assets/ipn.png" alt="IPN">
        <img src="app/assets/escom.png" alt="ESCOM">
    </div>
    """,
    unsafe_allow_html=True,
)

# === Encabezado principal ===
st.markdown("## 📊 Sistema de Dashboards Académicos")

if estado["logueado"]:
    # === Usuario logueado ===
    st.success(f"Bienvenido, **{estado['nombre_usuario']}**")

    # === Redirección si se estableció desde otro módulo ===
    if estado.get("menu"):
        st.session_state["menu_sidebar"] = estado["menu"]
        estado["menu"] = None  # Reiniciar el estado para futuras vistas

    # === Menú lateral ===
    menu_actual = st.sidebar.radio(
        "Menú",
        ["Crear nuevo dashboard", "Ver dashboards", "Cerrar sesión"],
        key="menu_sidebar"
    )

    if menu_actual == "Crear nuevo dashboard":
        from app.crear_dashboard import crear_dashboard
        crear_dashboard()

    elif menu_actual == "Ver dashboards":
        from app.ver_dashboard import ver_dashboards
        ver_dashboards()

    elif menu_actual == "Cerrar sesión":
        cerrar_sesion()
        st.rerun()

else:
    # === Usuario no logueado ===
    menu = st.selectbox("Selecciona una opción", ["Iniciar sesión", "Registrarse"])

    if menu == "Iniciar sesión":
        mostrar_login()
    else:
        mostrar_registro()

# === Pie de página ===
st.markdown(
    """
    <div class="footer">
        <div class="header-logos">
            <img src="app/assets/ipn.png" alt="IPN">
            <img src="app/assets/escom.png" alt="ESCOM">
        </div>
        <p>Sistema de análisis académico - ESCOM IPN<br>Instituto Politécnico Nacional © 2025</p>
    </div>
    """,
    unsafe_allow_html=True,
)
