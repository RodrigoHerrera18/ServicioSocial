# app/ver_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.orm import joinedload
from app.db import SessionLocal, Dashboard, Evaluacion, Alumno, Resultado, Materia
from app.session_state import obtener_estado, cerrar_sesion


def ver_dashboards():
    estado = obtener_estado()
    db = SessionLocal()

    top_left, top_right = st.columns([8, 1])
    with top_left:
        st.markdown("## Dashboards disponibles")
    with top_right:
        if st.button("🔒 Cerrar sesión"):
            cerrar_sesion()
            st.rerun()

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
    calificaciones = pd.to_numeric(df_filtrado["Calificación"], errors="coerce")
    promedio = calificaciones.mean()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total evaluados", total)
    kpi2.metric("Aprobados", f"{aprobados} ({aprobados / total:.0%})" if total else "0")
    kpi3.metric("No presentaron", f"{np} ({np / total:.0%})" if total else "0")
    kpi4.metric("🎓 Promedio General", f"{promedio:.2f}" if not pd.isna(promedio) else "N/A")

    # === Histograma por género ===
    st.markdown("### 👩‍🎓 Estatus académico por género")

    generos = ["Mujer", "Hombre", "Desconocido"]
    cols_genero = st.columns(3)
    for genero, col in zip(generos, cols_genero):
        subset = df_filtrado[df_filtrado["Género"] == genero]
        conteo = (
            subset["Estatus"].value_counts().reindex(["Aprobado", "Reprobado", "NP"], fill_value=0)
            .reset_index()
        )
        conteo.columns = ["Estatus", "Cantidad"]
        fig_gen = px.bar(
            conteo,
            x="Estatus",
            y="Cantidad",
            title=genero,
            color="Estatus",
            color_discrete_map={
                "Aprobado": "#00C853",
                "Reprobado": "#D50000",
                "NP": "#FFD600",
            },
        )
        col.plotly_chart(fig_gen, use_container_width=True)

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
        color_discrete_sequence=["#F48FB1", "#42A5F5", "#BDBDBD"]
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
            "Aprobado": "#00C853",
            "Reprobado": "#D50000",
            "NP": "#9E9E9E"
        }
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # === Tabla final ===
    st.markdown("### 📋 Tabla General de Estudiantes")
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Descargar CSV",
        data=csv,
        file_name="estudiantes_filtrados.csv",
        mime="text/csv",
    )
    st.dataframe(df_filtrado, use_container_width=True)
