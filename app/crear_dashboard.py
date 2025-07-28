# app/crear_dashboard.py

import streamlit as st
import pandas as pd
from app.db import SessionLocal, Dashboard, Evaluacion, Alumno, Resultado, Materia
from app.extractores import extraer_ordinario, extraer_extraordinario, extraer_ets
from app.utils import obtener_estatus, obtener_genero
from app.session_state import obtener_estado


def crear_dashboard():
    estado = obtener_estado()
    db = SessionLocal()

    st.markdown("## 📊 Crear nuevo Dashboard")
    st.markdown("Carga los archivos oficiales para generar el análisis académico.")

    with st.form("form_dashboard", clear_on_submit=False):
        # === Configuración del Dashboard ===
        st.markdown("### ✏️ Configuración del Dashboard")
        titulo = st.text_input("Título del Dashboard", placeholder="Ej. Análisis y Diseño de Algoritmos — 2025-2")

        # === Subida de archivos ===
        st.markdown("### 📤 Sube los archivos en formato PDF")

        archivo_ordinario = st.file_uploader("📘 Ordinario (obligatorio)", type="pdf")
        archivo_extra = st.file_uploader("🟢 Extraordinario (obligatorio)", type="pdf")
        agregar_ets = st.checkbox("¿Agregar archivo ETS?")
        archivo_ets = None
        if agregar_ets:
            archivo_ets = st.file_uploader("🔴 ETS (opcional)", type="pdf")

        submitted = st.form_submit_button("🔒 Generar Dashboard")

    if submitted:
        errores = []
        if not titulo:
            errores.append("⚠️ Falta el título del dashboard.")
        if not archivo_ordinario:
            errores.append("📘 Falta el archivo ordinario.")
        if not archivo_extra:
            errores.append("🟢 Falta el archivo extraordinario.")

        if errores:
            st.error("Faltan campos obligatorios:")
            for e in errores:
                st.markdown(f"- {e}")
            return

        try:
            # === Procesar archivos ===
            encabezado_o, df_o = extraer_ordinario(archivo_ordinario)
            encabezado_e, df_e = extraer_extraordinario(archivo_extra)
            df_ets, encabezado_ets, stats_ets = None, None, None
            incluye_ets = False

            if agregar_ets and archivo_ets is not None:
                encabezado_ets, df_ets, stats_ets = extraer_ets(archivo_ets)
                incluye_ets = True

            # === Materia ===
            nombre_materia = encabezado_o.get("Materia", "Sin nombre")
            materia = db.query(Materia).filter(Materia.nombre_materia == nombre_materia).first()
            if not materia:
                materia = Materia(nombre_materia=nombre_materia)
                db.add(materia)
                db.commit()
                db.refresh(materia)

            # === Crear Dashboard ===
            dashboard = Dashboard(
                id_usuario=estado["id_usuario"],
                id_materia=materia.id_materia,
                titulo_personalizado=titulo,
                incluye_ets=incluye_ets
            )
            db.add(dashboard)
            db.commit()
            db.refresh(dashboard)

            # === Función auxiliar ===
            def guardar_evaluacion(encabezado, df, tipo_eval):
                eval = Evaluacion(
                    id_dashboard=dashboard.id_dashboard,
                    tipo_evaluacion=tipo_eval,
                    licenciatura=encabezado.get("Licenciatura", "Desconocida"),
                    grupo=(encabezado.get("Grupo", "") if tipo_eval != "ets" else "N/A"),
                    promedio_general=encabezado.get("Promedio General", None),
                    total_aprobados=encabezado.get("Aprobados", 0),
                    total_reprobados=encabezado.get("Reprobados", 0),
                    total_np=encabezado.get("No Presentaron", 0)
                )
                db.add(eval)
                db.commit()
                db.refresh(eval)

                for _, fila in df.iterrows():
                    alumno = db.query(Alumno).filter(Alumno.boleta == fila["Boleta"]).first()
                    if not alumno:
                        alumno = Alumno(
                            boleta=fila["Boleta"],
                            nombre=fila["Nombre"],
                            genero=obtener_genero(fila["Nombre"])  # Corregido: infiere género
                        )
                        db.add(alumno)
                        db.commit()
                        db.refresh(alumno)

                    resultado = Resultado(
                        id_evaluacion=eval.id_evaluacion,
                        id_alumno=alumno.id_alumno,
                        calificacion=None if fila["Calificacion"] == "NP" else fila["Calificacion"],
                        estatus=fila["Estatus"]
                    )
                    db.add(resultado)
                db.commit()

            # === Guardar evaluaciones ===
            guardar_evaluacion(encabezado_o, df_o, "ordinario")
            guardar_evaluacion(encabezado_e, df_e, "extraordinario")
            if incluye_ets and df_ets is not None:
                guardar_evaluacion(encabezado_ets, df_ets, "ets")

            st.success("✅ Dashboard creado correctamente. Redirigiendo...")

            # === Redirección al ver dashboards ===
            estado["menu"] = "Ver dashboards"
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error al procesar los archivos: {e}")
