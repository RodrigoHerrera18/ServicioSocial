# app/auth.py

import streamlit as st
import base64
from pathlib import Path
from app.db import SessionLocal, Usuario
from app.utils import hash_password, verificar_password, correo_valido
from app.session_state import iniciar_sesion

def mostrar_login():
    """Pantalla de inicio de sesión con estilo personalizado."""

    def _load_svg(path: str) -> str:
        """Carga un SVG y lo codifica en base64."""
        svg_bytes = Path(path).read_bytes()
        return base64.b64encode(svg_bytes).decode()

    escom_svg = _load_svg("app/assets/escom_logo.svg")
    ipn_svg = _load_svg("app/assets/ipn_logo.svg")

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: #1a237e;
        }}
        div.block-container {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            max-width: 400px;
            background: none;
            box-shadow: none;
            padding: 0;
        }}
        .logo-row {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        .logo-row img {{
            width: 80px;
            height: 80px;
            object-fit: contain;
        }}
        h1.login-title {{
            color: #ffffff;
            font-weight: 600;
            text-align: center;
            margin-bottom: 0.2rem;
        }}
        p.login-subtitle {{
            color: rgba(255,255,255,0.7);
            text-align: center;
            margin-bottom: 1.5rem;
        }}
        input {{
            background-color: #ffffff !important;
        }}
        div.stButton>button {{
            background-color: #ffffff !important;
            color: #1a237e !important;
            border-radius: 8px !important;
            width: 100%;
        }}
        div.stButton>button:hover {{
            background-color: #e8eaf6 !important;
        }}
        </style>
        <div class="logo-row">
            <img src="data:image/svg+xml;base64,{escom_svg}" alt="Logo ESCOM"/>
            <img src="data:image/svg+xml;base64,{ipn_svg}" alt="Logo IPN"/>
        </div>
        <h1 class="login-title">Inicio de Sesión</h1>
        <p class="login-subtitle">Sistema de Evaluación Académica — ESCOM / IPN</p>
        """,
        unsafe_allow_html=True,
    )

    correo = st.text_input("Correo electrónico", placeholder="tucorreo@dominio.com")
    contraseña = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        if not correo or not contraseña:
            st.error("⚠️ Todos los campos son obligatorios.")
            return

        db = SessionLocal()
        usuario = db.query(Usuario).filter(Usuario.correo == correo).first()

        if usuario and verificar_password(contraseña, usuario.contraseña_hash):
            iniciar_sesion(usuario.id_usuario, usuario.nombre_usuario, usuario.correo)
            st.success(f"✅ Bienvenido, {usuario.nombre_usuario}")
            st.rerun()
        else:
            st.error("❌ Correo o contraseña incorrectos.")


def mostrar_registro():
    st.subheader("📝 Registro de nuevo usuario")

    nombre = st.text_input("Nombre completo", placeholder="Ej. Rodrigo Pérez")
    correo = st.text_input("Correo electrónico", placeholder="Ej. rodrigo@escom.ipn.mx")
    contraseña = st.text_input("Contraseña", type="password")
    confirmar = st.text_input("Confirmar contraseña", type="password")

    if st.button("Registrarse"):
        if not nombre or not correo or not contraseña or not confirmar:
            st.error("⚠️ Todos los campos son obligatorios.")
            return

        if contraseña != confirmar:
            st.error("🔁 Las contraseñas no coinciden.")
            return

        if not correo_valido(correo):
            st.error("📧 Correo inválido.")
            return

        db = SessionLocal()
        if db.query(Usuario).filter(Usuario.correo == correo).first():
            st.warning("⚠️ Ya existe una cuenta con ese correo.")
            return

        nuevo = Usuario(
            nombre_usuario=nombre,
            correo=correo,
            contraseña_hash=hash_password(contraseña)
        )
        db.add(nuevo)
        db.commit()

        st.success("✅ Usuario registrado exitosamente. Ahora puedes iniciar sesión.")
