# app/auth.py
import streamlit as st
from app.db import SessionLocal, Usuario
from app.utils import hash_password, verificar_password, correo_valido
from app.session_state import iniciar_sesion


def mostrar_login():
    """Pantalla de inicio de sesión con estilo personalizado."""

    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f5f7fe;
        }
        div.block-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 0;
            background: none;
            box-shadow: none;
        }
        .logo-row {
            display: flex;
            gap: 20px;
        }
        .logo-placeholder {
            width: 60px;
            height: 60px;
            border-radius: 8px;
            background-color: #6a00c8;
            color: white;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        h1.login-title {
            font-size: 1.8rem;
            color: #1a1a1a;
            font-weight: bold;
            text-align: center;
            margin-top: 1rem;
        }
        p.login-subtitle {
            font-size: 1rem;
            color: #555;
            margin-bottom: 2rem;
            text-align: center;
        }
        .form-container {
            background: #fff;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0px 5px 20px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 350px;
        }
        .form-container input {
            width: 100% !important;
            padding: 0.75rem !important;
            border-radius: 6px !important;
            border: 1px solid #ccc !important;
        }
        .stButton>button {
            width: 100%;
            background-color: #3a007a;
            color: white;
            padding: 0.75rem;
            border-radius: 6px;
            font-weight: 600;
            margin-top: 1rem;
        }
        .stButton>button:hover {
            background-color: #2e0064;
        }
        .admin-link {
            font-size: 0.9rem;
            color: #3a007a;
            text-decoration: underline;
            text-align: center;
            margin-top: 1rem;
            display: block;
        }
        .login-footer {
            font-size: 0.8rem;
            color: #777;
            margin-top: 2rem;
            text-align: center;
        }
        @media (max-width: 480px) {
            .form-container {
                width: 90%;
                max-width: 350px;
            }
        }
        </style>
        <div class="logo-row">
            <div class="logo-placeholder">IPN</div>
            <div class="logo-placeholder">ESCOM</div>
        </div>
        <h1 class="login-title">Sistema Académico</h1>
        <p class="login-subtitle">Escuela Superior de Cómputo</p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    correo = st.text_input("Correo electrónico", placeholder="Correo electrónico")
    contraseña = st.text_input("Contraseña", type="password", placeholder="Contraseña")

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

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<a class="admin-link" href="#">Acceso de administrador</a>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="login-footer">
            Sistema de análisis académico — ESCOM IPN<br/>
            Instituto Politécnico Nacional © 2024
        </div>
        """,
        unsafe_allow_html=True,
    )


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

