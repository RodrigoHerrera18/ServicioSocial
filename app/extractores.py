# app/extractores.py
"""
Módulo centralizado para extraer y normalizar la información
de los PDFs de Ordinario, Extraordinario y ETS.

Cada función devuelve:
    1. encabezado   -> dict   (metadatos del acta)
    2. df_alumnos   -> pd.DataFrame con al menos:
          ['Boleta', 'Nombre', 'Calificacion', 'Origen']
    3. stats*       -> dict (opcional, solo ETS lo necesita)
"""

import re
import io
import pdfplumber
import PyPDF2
import pandas as pd
from typing import Tuple, Dict, Any
from app.utils import obtener_estatus

# ------------------------------------------------------------------
# Utilidad interna para leer texto (soporta bytes o ruta)
# ------------------------------------------------------------------
def _leer_pdf_con_plumber(source) -> str:
    texto = ""
    with pdfplumber.open(source) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto += t
    return texto


def _leer_pdf_con_pypdf2(source) -> str:
    texto = ""
    lector = PyPDF2.PdfReader(source)
    for pagina in lector.pages:
        texto += pagina.extract_text()
    return texto


def _leer_pdf(source) -> str:
    """
    Intenta con pdfplumber y, si falla, con PyPDF2.
    `source` puede ser:
        - bytes
        - str (ruta)
        - file-like object
    """
    try:
        if isinstance(source, (bytes, bytearray)):
            stream = io.BytesIO(source)
        else:
            stream = source
        return _leer_pdf_con_plumber(stream)
    except Exception:
        if isinstance(source, (bytes, bytearray)):
            stream = io.BytesIO(source)
        else:
            stream = source
        return _leer_pdf_con_pypdf2(stream)


# ------------------------------------------------------------------
# Extractor genérico para Ordinario / Extraordinario
# ------------------------------------------------------------------
_REGEX_HEADER_OE = {
    "Licenciatura": r"Licenciatura:\s+(.*)",
    "Profesor": r"Profesor:\s+[A-Z0-9]+\s+(.*)",
    "Grupo": r"Grupo:\s+(.*)",
    "Materia": r"Materia:\s+[A-Z0-9]+\s+(.*)",
    "Total de Alumnos": r"Total de Alumnos:\s+(\d+)",
    "Aprobados": r"Aprobados:\s+(\d+)",
    "Reprobados": r"Reprobados:\s+(\d+)",
    "No Presentaron": r"No Presentaron:\s+(\d+)",
    "Promedio General": r"Promedio General:\s+([\d.]+)",
}

_REGEX_FILA_OE = re.compile(r"^\s*\d{1,2}\s+(\d{10})\s+(.*?)\s+(\d{1,2}|NP)\s*$")


def _extraer_ordinario_extra(texto: str, origen: str) -> Tuple[Dict[str, Any], pd.DataFrame]:
    encabezado: Dict[str, Any] = {}
    registros = []

    # Encabezado
    for key, pat in _REGEX_HEADER_OE.items():
        m = re.search(pat, texto)
        if m:
            val = m.group(1).strip()
            if key in ["Total de Alumnos", "Aprobados", "Reprobados", "No Presentaron"]:
                val = int(val)
            elif key == "Promedio General":
                val = float(val)
            encabezado[key] = val

    # Alumnos
    for line in texto.split("\n"):
        m = _REGEX_FILA_OE.match(line)
        if m:
            boleta, nombre, calif = m.groups()
            calif_val = calif if calif == "NP" else int(calif)
            registros.append(
                {
                    "Boleta": boleta.strip(),
                    "Nombre": nombre.strip(),
                    "Calificacion": calif_val,
                    "Estatus": obtener_estatus(calif_val),
                    "Origen": origen,
                }
            )

    df = pd.DataFrame(registros)
    return encabezado, df


# ------------------------------------------------------------------
# Extractor ETS (estructura distinta)
# ------------------------------------------------------------------
_PAT_GENERAL_ETS = {
    "Licenciatura": r'LICENCIATURA\s*:\s*(.+)',
    "Materia": r'MATERIA:\s*(.+)',
    "Profesor": r'PROFESOR:\s*(.+)',
    "Periodo": r'PERIODO\s+(\w+)',
}

_PAT_STATS_ETS = r'INSCRITOS:\s*(\d+)\s+APROBADOS:\s*(\d+)\s+REPROBADOS:\s*(\d+)\s+NO PRESENTARON:\s*(\d+)'
_PAT_ESTUDIANTE_ETS = r'(\d{10})\s+([A-Z\s]+?)\s+(NP|[0-9]+)\s+\(([^)]+)\)\s+(\d+)'

def _extraer_ets(texto: str) -> Tuple[Dict[str, Any], pd.DataFrame, Dict[str, int]]:
    encabezado: Dict[str, Any] = {}
    for key, pat in _PAT_GENERAL_ETS.items():
        m = re.search(pat, texto, re.IGNORECASE)
        encabezado[key] = m.group(1).strip() if m else ""

    # Los archivos ETS no contienen información de grupo ni promedio general
    # Para mantener consistencia con el modelo de datos, se asignan valores
    # por defecto.
    encabezado["Grupo"] = "N/A"
    encabezado["Promedio General"] = None

    # Estadísticas
    stats = {"inscritos": 0, "aprobados": 0, "reprobados": 0, "no_presentaron": 0}
    s = re.search(_PAT_STATS_ETS, texto)
    if s:
        stats = {
            "inscritos": int(s.group(1)),
            "aprobados": int(s.group(2)),
            "reprobados": int(s.group(3)),
            "no_presentaron": int(s.group(4)),
        }

    # Estudiantes
    registros = []
    for boleta, nombre, calif, _, num_lista in re.findall(_PAT_ESTUDIANTE_ETS, texto):
        calif_val = calif if calif == "NP" else int(calif)
        registros.append(
            {
                "Boleta": boleta,
                "Nombre": nombre.strip(),
                "Calificacion": calif_val,
                "Estatus": obtener_estatus(calif_val),
                "NumeroLista": int(num_lista),
                "Origen": "ets",
            }
        )

    df = pd.DataFrame(registros).sort_values("NumeroLista").reset_index(drop=True)
    return encabezado, df, stats


# ------------------------------------------------------------------
# API pública del módulo
# ------------------------------------------------------------------
def extraer_ordinario(file) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """file: bytes, str path o file-like"""
    texto = _leer_pdf(file)
    return _extraer_ordinario_extra(texto, "ordinario")


def extraer_extraordinario(file) -> Tuple[Dict[str, Any], pd.DataFrame]:
    texto = _leer_pdf(file)
    return _extraer_ordinario_extra(texto, "extraordinario")


def extraer_ets(file) -> Tuple[Dict[str, Any], pd.DataFrame, Dict[str, int]]:
    texto = _leer_pdf(file)
    return _extraer_ets(texto)
