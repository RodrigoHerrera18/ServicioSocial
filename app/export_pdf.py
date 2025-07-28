# app/export_pdf.py

from fpdf import FPDF
import pandas as pd
import tempfile
import os

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.set_text_color(60, 13, 153)  # Color IPN
        self.cell(0, 10, "Sistema de Análisis Académico - ESCOM IPN", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")

def exportar_dashboard_pdf(titulo: str, df: pd.DataFrame, filtros: dict) -> str:
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Título del Dashboard
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, titulo, ln=True)

    # Filtros aplicados
    pdf.set_font("Arial", "", 12)
    for clave, valor in filtros.items():
        pdf.cell(0, 10, f"{clave}: {valor}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Tabla General de Estudiantes", ln=True)
    pdf.ln(5)

    # Tabla
    pdf.set_font("Arial", "", 9)

    columnas = list(df.columns)
    col_width = pdf.w / len(columnas) - 5
    for col in columnas:
        pdf.cell(col_width, 10, col, border=1)

    pdf.ln()

    for i, row in df.iterrows():
        for col in columnas:
            valor = str(row[col])[:20]  # Evitar texto largo
            pdf.cell(col_width, 10, valor, border=1)
        pdf.ln()

    # Guardar PDF temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    ruta = temp_file.name
    pdf.output(ruta)
    temp_file.close()
    return ruta
