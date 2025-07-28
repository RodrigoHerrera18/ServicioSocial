# app/utils.py

import bcrypt
import re

# === CONTRASEÑAS ===

def hash_password(password: str) -> str:
    """Hashea una contraseña en texto plano."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_password(password: str, hashed: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# === VALIDACIÓN DE CORREO ===

def correo_valido(correo: str) -> bool:
    """Valida un correo electrónico simple."""
    patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(patron, correo) is not None


# === DETERMINAR ESTATUS DESDE CALIFICACIÓN ===

def obtener_estatus(calificacion: str | float) -> str:
    """Devuelve el estatus de un alumno según su calificación."""
    if isinstance(calificacion, str) and calificacion.upper() == "NP":
        return "NP"
    try:
        cal = float(calificacion)
        return "Aprobado" if cal >= 6 else "Reprobado"
    except ValueError:
        return "NP"


# === FORMATO DE COLORES (para plotly o badges si lo necesitas luego) ===

def color_por_estatus(estatus: str) -> str:
    return {
        "Aprobado": "#00C853",     # verde
        "Reprobado": "#D50000",    # rojo
        "NP": "#9E9E9E"            # gris
    }.get(estatus, "#000000")


def color_por_genero(genero: str) -> str:
    return {
        "Mujer": "#F48FB1",        # rosa
        "Hombre": "#42A5F5",       # azul
        "Desconocido": "#BDBDBD"
    }.get(genero, "#000000")

import gender_guesser.detector as gender

detector = gender.Detector()

def obtener_genero(nombre_completo: str) -> str:
    # Toma solo el primer nombre (última palabra del nombre completo)
    partes = nombre_completo.strip().split()
    if not partes:
        return "Desconocido"
    primer_nombre = partes[-1].capitalize()

    genero_detectado = detector.get_gender(primer_nombre)

    if genero_detectado in ["male", "mostly_male"]:
        return "Hombre"
    elif genero_detectado in ["female", "mostly_female"]:
        return "Mujer"
    else:
        return "Desconocido"

