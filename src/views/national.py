"""View module for National and Regional evasion panorama."""

import streamlit as st
import pandas as pd

from src.config import FOCUS_YEARS, REGION_COLORS
from src.data.transformers import get_regional_kpis
from src.ui.charts import build_regional_time_series, build_horizontal_ranking
from src.ui.components import render_highlight_box


def render_national_view(df_regional: pd.DataFrame) -> None:
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

    # 3. Horizontal Ranking
    st.subheader("🏆 Ranking de Regiões — Período 2023–2024")
    df_ranking = (
        df_focus.loc[df_focus["ANO_FLUXO"] == "2023-2024"]
        .sort_values("TOTAL", ascending=True)
    )

    ranking_colors = [REGION_COLORS.get(r, "#94a3b8") for r in df_ranking["REGIAO"]]
    regional_mean = float(df_ranking["TOTAL"].mean())

    fig_ranking = build_horizontal_ranking(
        df=df_ranking,
        value_col="TOTAL",
        label_col="REGIAO",
        colors=ranking_colors,
        benchmark_mean=regional_mean,
        benchmark_label="Média Regiões",
        title="Ranking por Taxa de Evasão (2023–2024)",
    )
    st.plotly_chart(fig_ranking, use_container_width=True)

