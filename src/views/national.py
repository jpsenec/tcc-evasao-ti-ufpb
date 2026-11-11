"""View module for National and Regional evasion panorama."""

import streamlit as st
import pandas as pd

from src.config import FOCUS_YEARS, REGION_COLORS
from src.data.transformers import (
    get_regional_kpis,
    compute_regional_cycle_ranking,
    compute_regional_cohort_tda,
)
from src.ui.charts import build_regional_time_series, build_horizontal_ranking
from src.ui.components import render_highlight_box


def render_national_view(
    df_regional: pd.DataFrame,
    df_trajectory: pd.DataFrame = None,
) -> None:
    """Renders the National & Macro-regions dashboard page."""
    st.title("🌎 Evasão em Cursos de Tecnologia — Panorama Nacional (2020–2024)")

    df_focus = df_regional[df_regional["ANO_FLUXO"].isin(FOCUS_YEARS)]
    regional_kpis = get_regional_kpis(df_focus)

    # 1. KPI Columns
    cols = st.columns(len(regional_kpis))
    for col, (region, (final_rate, delta_rate)) in zip(cols, regional_kpis.items()):
        col.metric(region, f"{final_rate:.1f}%", f"{delta_rate:+.1f}% vs 2020")

    st.markdown("---")

    # 2. Time Series
    st.subheader("📈 Evolução da Taxa de Evasão por Região (2020–2024)")
    fig_time_series = build_regional_time_series(df_focus)
    st.plotly_chart(fig_time_series, use_container_width=True)

    render_highlight_box(
        "💡 <b>O Nordeste</b> encerrou o período como a região de menor taxa de evasão "
        "transversal (16,0%), mantendo-se consistentemente abaixo da média regional agregada (17,7%)."
    )

    st.markdown("---")

    # 3. Horizontal Ranking with Interactive Scope Selector
    st.subheader("🏆 Ranking de Regiões por Retenção e Evasão")
    st.caption("Alterne entre a medição anual recente, a média histórica do ciclo ou a desistência acumulada da coorte de TI.")

    ranking_mode = st.radio(
        "Selecione a perspectiva de análise:",
        options=[
            "📌 Último Período (2023–2024)",
            "📊 Média do Ciclo Completo (2020–2024)",
            "🎓 Coorte 2020 de TI (TDA Acumulada em 5 Anos)",
        ],
        horizontal=True,
    )

    if ranking_mode == "📌 Último Período (2023–2024)":
        df_ranking = (
            df_focus.loc[df_focus["ANO_FLUXO"] == "2023-2024"]
            .sort_values("TOTAL", ascending=True)
            .reset_index(drop=True)
        )
        chart_title = "Ranking por Taxa de Evasão Anual (2023–2024)"
        highlight_msg = (
            "🥇 <b>1º Lugar no Período Recente:</b> O <b>Nordeste</b> encerrou 2023–2024 com a menor taxa de evasão "
            "(<b>16,0%</b>), posicionando-se 1,7 p.p. abaixo da média regional brasileira (17,7%)."
        )
    elif ranking_mode == "📊 Média do Ciclo Completo (2020–2024)":
        df_ranking = compute_regional_cycle_ranking(df_focus)
        chart_title = "Ranking por Média do Ciclo Transversal (2020–2024)"
        highlight_msg = (
            "🥇 <b>1º Lugar no Ciclo Quinquenal:</b> Ao longo de todo o período (2020 a 2024), "
            "o <b>Nordeste</b> sustentou a menor taxa média anual de evasão do país (<b>15,2%</b>), "
            "superando o Sudeste (15,6%), Sul (15,8%), Centro-Oeste (16,5%) e Norte (17,1%)."
        )
    else:
        if df_trajectory is not None and not df_trajectory.empty:
            df_ranking = compute_regional_cohort_tda(df_trajectory, target_year=2024)
        else:
            df_ranking = pd.DataFrame(columns=["REGIAO", "TOTAL"])
        chart_title = "Ranking por TDA Acumulada da Coorte 2020 (TI — 2020 a 2024)"
        highlight_msg = (
            "🥇 <b>1º Lugar na Retenção Longitudinal da Coorte:</b> Na turma de ingressantes de 2020 acompanhada até 2024 "
            "em cursos de TI, o <b>Nordeste</b> registrou a menor desistência acumulada do Brasil (<b>53,4%</b>), "
            "perdendo 4,0 p.p. a menos de estudantes que o Sudeste (57,4%) e superando a média nacional (56,2%)."
        )

    ranking_colors = [REGION_COLORS.get(r, "#94a3b8") for r in df_ranking["REGIAO"]]
    regional_mean = float(df_ranking["TOTAL"].mean()) if not df_ranking.empty else 0.0

    fig_ranking = build_horizontal_ranking(
        df=df_ranking,
        value_col="TOTAL",
        label_col="REGIAO",
        colors=ranking_colors,
        benchmark_mean=regional_mean,
        benchmark_label="Média Regiões",
        title=chart_title,
    )
    st.plotly_chart(fig_ranking, use_container_width=True)
    render_highlight_box(highlight_msg)
