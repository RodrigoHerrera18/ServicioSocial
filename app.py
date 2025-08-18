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

# === Encabezado institucional (usando st.columns + st.image) ===
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    st.image("static/ipn.png", width=100)
with col2:
    st.markdown("<h2 style='text-align: center;'>📊 Sistema de Aprovechamiento Escolar</h2>", unsafe_allow_html=True)
with col3:
    st.image("static/escom.png", width=100)

# === Contenido principal ===
if estado["logueado"]:
    st.success(f"Bienvenido, **{estado['nombre_usuario']}**")

    if estado.get("menu"):
        st.session_state["menu_sidebar"] = estado["menu"]
        estado["menu"] = None

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
    menu = st.selectbox("Selecciona una opción", ["Iniciar sesión", "Registrarse"])
    if menu == "Iniciar sesión":
        mostrar_login()
    else:
        mostrar_registro()

# === Pie de página institucional ===
st.markdown("---", unsafe_allow_html=True)
footer1, footer2, footer3 = st.columns([1, 4, 1])
with footer1:
    st.image("static/ipn.png", width=80)
with footer2:
    st.markdown(
        "<p style='text-align: center;'>Sistema de análisis académico - ESCOM IPN<br>Instituto Politécnico Nacional © 2025</p>",
        unsafe_allow_html=True
    )
with footer3:
    st.image("static/escom.png", width=80)
