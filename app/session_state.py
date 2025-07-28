# app/session_state.py

import streamlit as st

def obtener_estado():
    """Inicializa o recupera el estado de sesión."""
    if "estado" not in st.session_state:
        st.session_state.estado = {
            "logueado": False,
            "id_usuario": None,
            "nombre_usuario": None,
            "correo": None,
        }
    return st.session_state.estado


def iniciar_sesion(id_usuario, nombre_usuario, correo):
    """Guarda los datos del usuario logueado."""
    estado = obtener_estado()
    estado["logueado"] = True
    estado["id_usuario"] = id_usuario
    estado["nombre_usuario"] = nombre_usuario
    estado["correo"] = correo


def cerrar_sesion():
    """Reinicia el estado de sesión."""
    if "estado" in st.session_state:
        del st.session_state["estado"]
