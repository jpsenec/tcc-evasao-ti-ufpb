"""View module for UFPB Campus IV (Rio Tinto) degree programs."""

import streamlit as st
import pandas as pd

from src.config import (
    CODE_MUNICIPALITY_RIO_TINTO,
    CODE_COURSE_LIC_CC,
    CODE_COURSE_SI,
)
from src.data.transformers import (
    get_course_kpis,
    compute_degree_comparison,
)
from src.ui.charts import (
    build_course_trajectory_chart,
    build_degree_comparison_chart,
)
from src.ui.components import render_highlight_box


def render_local_view(df_trajectory: pd.DataFrame) -> None:
    """Renders the Rio Tinto campus IT degree programs analysis page."""
    st.title("🎓 Análise dos Cursos de TI — UFPB Campus Rio Tinto")

    df_rt = df_trajectory.loc[
        df_trajectory["CO_MUNICIPIO"] == CODE_MUNICIPALITY_RIO_TINTO
    ].copy()

    df_cc = df_rt.loc[df_rt["CO_CURSO"] == CODE_COURSE_LIC_CC].sort_values("NU_ANO_REFERENCIA")
    df_si = df_rt.loc[df_rt["CO_CURSO"] == CODE_COURSE_SI].sort_values("NU_ANO_REFERENCIA")

    # 1. Course KPI Cards
    st.markdown("### 📊 Métricas da Coorte 2020 (Acompanhamento até 2024)")
    col1, col2 = st.columns(2)

    kpis_cc = get_course_kpis(df_cc, target_year=2024)
    with col1:
        st.markdown("**🟣 Licenciatura em Ciência da Computação**")
        c1a, c1b, c1c = st.columns(3)
        c1a.metric("Ingressantes (2020)", kpis_cc["ingressantes"])
        c1b.metric("TDA em 2024", f"{kpis_cc['tda']:.1f}%")
        c1c.metric("Ativos em 2024", kpis_cc["permanencia"])

    kpis_si = get_course_kpis(df_si, target_year=2024)
    with col2:
        st.markdown("**🟢 Sistemas de Informação (Bacharelado)**")
        c2a, c2b, c2c = st.columns(3)
        c2a.metric("Ingressantes (2020)", kpis_si["ingressantes"])
        c2b.metric("TDA em 2024", f"{kpis_si['tda']:.1f}%")
        c2c.metric("Ativos em 2024", kpis_si["permanencia"])

    st.markdown("---")

    # 2. Course Trajectory Chart
    st.subheader("📉 Trajetória de Desistência — TDA Acumulada e Anual")
    fig_trajectory = build_course_trajectory_chart(df_cc, df_si)
    st.plotly_chart(fig_trajectory, use_container_width=True)

    st.markdown("---")

    # 3. Contextual Degree Comparison (Bacharelado vs Licenciatura)
    st.subheader("🎯 Contexto: Licenciatura vs Bacharelado em TI na Paraíba (2024)")
    degree_averages = compute_degree_comparison(df_trajectory, target_year=2024)

    fig_degree = build_degree_comparison_chart(
        medias_grau=degree_averages,
        rate_cc_2024=kpis_cc["tda"],
        rate_si_2024=kpis_si["tda"],
    )
    st.plotly_chart(fig_degree, use_container_width=True)

    render_highlight_box(
        "⭐ <b>As estrelas amarelas</b> marcam onde os cursos de Rio Tinto se situam em relação à média "
        "estadual de cada grau acadêmico — evidenciando que a Licenciatura local sofre pressão de evasão desproporcional.",
        is_warning=True,
    )

    st.markdown("---")

    # 4. Detailed Data Table
    st.subheader("📋 Dados Detalhados — Cursos de Rio Tinto")
    display_columns = [
        "NO_CURSO", "NU_ANO_REFERENCIA", "QT_INGRESSANTE",
        "QT_PERMANENCIA", "QT_CONCLUINTE", "QT_DESISTENCIA",
        "TAP", "TDA", "TCA", "TADA"
    ]
    df_table = df_rt[display_columns].sort_values(["NO_CURSO", "NU_ANO_REFERENCIA"])
    st.dataframe(
        df_table.style.background_gradient(subset=["TDA"], cmap="Reds"),
        use_container_width=True,
    )

