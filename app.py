# app.py

import streamlit as st
from app.session_state import obtener_estado, cerrar_sesion
from app.auth import mostrar_login, mostrar_registro
from app.db import init_db

# === Inicializa la base de datos (crear tablas si no existen) ===
init_db()

# === Cargar CSS externo ===
with open("app/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Configurar página ===
st.set_page_config(page_title="Dashboards Académicos", layout="centered")

# === Obtener estado de sesión ===
estado = obtener_estado()

# === Encabezado principal ===
st.markdown("## 📊 Sistema de Dashboards Académicos")

if estado["logueado"]:
    # === Usuario logueado ===
    st.success(f"Bienvenido, **{estado['nombre_usuario']}**")

    # === Menú lateral ===
    # === Preparar valor seleccionado en el menú lateral ===
    if "menu_lateral" not in st.session_state:
        st.session_state.menu_lateral = "Crear nuevo dashboard"

    # Si se solicitó un cambio de menú desde otro módulo, aplicarlo antes de
    # crear el widget para evitar modificar el estado luego de instanciarlo.
    if estado.get("menu"):
        st.session_state.menu_lateral = estado["menu"]
        estado["menu"] = None

    menu_actual = st.sidebar.radio(
        "Menú",
        ["Crear nuevo dashboard", "Ver dashboards", "Cerrar sesión"],
        key="menu_lateral",
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
