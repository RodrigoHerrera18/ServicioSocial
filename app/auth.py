# app/auth.py

import streamlit as st
from app.db import SessionLocal, Usuario
from app.utils import hash_password, verificar_password, correo_valido
from app.session_state import iniciar_sesion

def mostrar_login():
    st.subheader("🔒 Iniciar sesión")

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
