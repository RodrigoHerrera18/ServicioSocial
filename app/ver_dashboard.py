# app/ver_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.orm import joinedload
from app.db import SessionLocal, Dashboard, Evaluacion, Alumno, Resultado, Materia
from app.session_state import obtener_estado


def ver_dashboards():
    estado = obtener_estado()
    db = SessionLocal()

    st.markdown("## 📋 Dashboards disponibles")
    if st.button("➕ Crear nuevo dashboard"):
        estado["menu"] = "Crear nuevo dashboard"
        st.rerun()
    dashboards = db.query(Dashboard).options(joinedload(Dashboard.materia)).all()

    if not dashboards:
        st.info("⚠️ No hay dashboards creados aún.")
        return

    opciones = {
        f"{d.titulo_personalizado} ({d.materia.nombre_materia})": d.id_dashboard for d in dashboards
    }
    seleccion = st.selectbox(
        "Selecciona un dashboard",
        list(opciones.keys()),
        key="seleccion_dashboard"
    )

    if not seleccion:
        return

    id_dashboard = opciones[seleccion]
    dashboard = db.query(Dashboard).filter_by(id_dashboard=id_dashboard).first()
    evaluaciones = db.query(Evaluacion).filter_by(id_dashboard=id_dashboard).all()

    if not evaluaciones:
        st.warning("No hay evaluaciones cargadas para este dashboard.")
        return

    st.markdown(f"### 📘 {dashboard.titulo_personalizado}")
    df_total = []

    for ev in evaluaciones:
        resultados = (
            db.query(Resultado)
            .join(Alumno)
            .filter(Resultado.id_evaluacion == ev.id_evaluacion)
            .all()
        )

        datos = []
        for r in resultados:
            datos.append({
                "Boleta": r.alumno.boleta,
                "Nombre": r.alumno.nombre,
                "Grupo": ev.grupo if ev.grupo else "N/A",
                "Licenciatura": ev.licenciatura,
                "Género": r.alumno.genero,
                # Guardar la calificación como texto para evitar problemas al
                # mostrarla en Streamlit. Si es None (NP) se guarda como "NP".
                "Calificación": str(r.calificacion) if r.calificacion is not None else "NP",
                "Estatus": r.estatus,
                "Origen": ev.tipo_evaluacion
            })
        df = pd.DataFrame(datos)
        df_total.append(df)

    # Unificar todos los orígenes
    df_completo = pd.concat(df_total, ignore_index=True)

    # === Filtros ===
    col1, col2 = st.columns(2)
    grupos = df_completo["Grupo"].unique().tolist()
    carreras = df_completo["Licenciatura"].unique().tolist()

    grupo_sel = col1.selectbox(
        "Filtrar por grupo",
        ["Todos"] + grupos,
        key="filtro_grupo"
    )
    carrera_sel = col2.selectbox(
        "Filtrar por licenciatura",
        ["Todos"] + carreras,
        key="filtro_carrera"
    )

    df_filtrado = df_completo.copy()
    if grupo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Grupo"] == grupo_sel]
    if carrera_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Licenciatura"] == carrera_sel]

    # === KPIs generales ===
    st.markdown("### 📊 KPIs generales")
    total = len(df_filtrado)
    aprobados = len(df_filtrado[df_filtrado["Estatus"] == "Aprobado"])
    reprobados = len(df_filtrado[df_filtrado["Estatus"] == "Reprobado"])
    np = len(df_filtrado[df_filtrado["Estatus"] == "NP"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total evaluados", total)
    col2.metric("Aprobados", f"{aprobados} ({aprobados / total:.0%})" if total else "0")
    col3.metric("No presentaron", f"{np} ({np / total:.0%})" if total else "0")

    # === KPI por género ===
    st.markdown("### 👩‍🎓 Desglose por género")

    for genero in ["Mujer", "Hombre", "Desconocido"]:
        subset = df_filtrado[df_filtrado["Género"] == genero]
        total_gen = len(subset)
        if total_gen == 0:
            continue
        aprobados_g = len(subset[subset["Estatus"] == "Aprobado"])
        reprobados_g = len(subset[subset["Estatus"] == "Reprobado"])
        np_g = len(subset[subset["Estatus"] == "NP"])

        st.markdown(f"**{genero}s**")
        st.markdown(
            f"- ✅ Aprobados: {aprobados_g} ({aprobados_g / total_gen:.0%})\n"
            f"- ❌ Reprobados: {reprobados_g} ({reprobados_g / total_gen:.0%})\n"
            f"- ⚠️ NP: {np_g} ({np_g / total_gen:.0%})"
        )

    # === Gráfica de género ===
    st.markdown("### 🧩 Distribución por Género")
    genero_count = df_filtrado["Género"].value_counts().reset_index()
    genero_count.columns = ["Género", "Cantidad"]

    fig = px.pie(
        genero_count,
        names="Género",
        values="Cantidad",
        title="Distribución de Género",
        hole=0.4,
        color="Género",
        color_discrete_map={
            "Mujer": "#e6007e",
            "Hombre": "#3f0071",
            "Desconocido": "#666666",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    # === Gráfico por origen ===
    st.markdown("### 📊 Histograma por Origen")
    df_bar = df_filtrado.copy()
    origines = ["ordinario", "extraordinario", "ets"]
    estatuses = ["Aprobado", "Reprobado", "NP"]

    # Normalizar valores por si provienen con mayúsculas o espacios
    df_bar["Origen"] = df_bar["Origen"].str.lower().str.strip()
    df_bar["Estatus"] = df_bar["Estatus"].str.strip()

    # Convertir a categóricos para garantizar que aparezcan todas las barras
    df_bar["Origen"] = pd.Categorical(df_bar["Origen"], categories=origines, ordered=True)
    df_bar["Estatus"] = pd.Categorical(df_bar["Estatus"], categories=estatuses, ordered=True)

    conteo = (
        df_bar
        .groupby(["Origen", "Estatus"], observed=False)  # type: ignore[arg-type]
        .size()
        .reset_index(name="Cantidad")
    )

    fig_bar = px.bar(
        conteo,
        x="Origen",
        y="Cantidad",
        color="Estatus",
        barmode="stack",
        category_orders={"Origen": origines, "Estatus": estatuses},
        color_discrete_map={
            "Aprobado": "#00c853",
            "Reprobado": "#d50000",
            "NP": "#666666",
        }
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # === Tabla final ===
    st.markdown("### 📋 Tabla General de Estudiantes")

    def estilo_estatus(val):
        if val == "Aprobado":
            return "background-color: #e8f5e9; color: #00c853; font-weight:600;"
        if val == "Reprobado":
            return "background-color: #ffebee; color: #d50000; font-weight:600;"
        if val == "NP":
            return "background-color: #eeeeee; color: #666666; font-weight:600;"
        return ""

    df_style = df_filtrado.style.applymap(estilo_estatus, subset=["Estatus"])
    st.dataframe(df_style, use_container_width=True)
