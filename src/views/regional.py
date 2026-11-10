"""View module for Paraíba state and Northeast regional context."""

import streamlit as st
import pandas as pd

from src.config import FOCUS_YEARS, NORTHEAST_STATES
from src.data.transformers import build_hierarchical_drilldown
from src.ui.charts import (
    build_northeast_time_series,
    build_horizontal_ranking,
    build_drilldown_time_series,
)
from src.ui.components import render_highlight_box


def render_regional_view(df_state: pd.DataFrame, df_trajectory: pd.DataFrame) -> None:
    """Renders the Paraíba and Northeast comparative dashboard page."""
    st.title("📍 Paraíba no Contexto do Nordeste (2020–2024)")

    df_focus_uf = df_state[df_state["ANO_FLUXO"].isin(FOCUS_YEARS)]
    ne_data = df_focus_uf[df_focus_uf["UF"].isin(NORTHEAST_STATES)]

    # 1. State KPIs
    pb_current = df_focus_uf.loc[
        (df_focus_uf["UF"] == "Paraíba") & (df_focus_uf["ANO_FLUXO"] == "2023-2024")
    ]
    pb_initial = df_focus_uf.loc[
        (df_focus_uf["UF"] == "Paraíba") & (df_focus_uf["ANO_FLUXO"] == "2020-2021")
    ]

    val_pb_current = float(pb_current["TOTAL"].iloc[0]) if not pb_current.empty else 0.0
    val_pb_initial = float(pb_initial["TOTAL"].iloc[0]) if not pb_initial.empty else 0.0
    fem_pb = float(pb_current["FEMININO"].iloc[0]) if not pb_current.empty else 0.0
    masc_pb = float(pb_current["MASCULINO"].iloc[0]) if not pb_current.empty else 0.0

    ne_2024 = ne_data.loc[ne_data["ANO_FLUXO"] == "2023-2024"]
    mean_ne = float(ne_2024["TOTAL"].mean()) if not ne_2024.empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Evasão PB (2023-24)", f"{val_pb_current:.1f}%", f"{val_pb_current - val_pb_initial:+.1f}% vs 2020")
    col2.metric("📊 Média Nordeste", f"{mean_ne:.1f}%")
    col3.metric("👩 Taxa Feminina (PB)", f"{fem_pb:.1f}%")
    col4.metric("👨 Taxa Masculina (PB)", f"{masc_pb:.1f}%")

    st.markdown("---")

    # 2. Time Series
    st.subheader("📊 Paraíba vs Estados do Nordeste — Série Temporal")
    fig_ne = build_northeast_time_series(ne_data, NORTHEAST_STATES)
    st.plotly_chart(fig_ne, use_container_width=True)

    st.markdown("---")

    # 3. Northeast Ranking
    st.subheader("🏅 Ranking Nordeste — 2023–2024")
    df_rank_ne = ne_2024.sort_values("TOTAL", ascending=True)
    colors_ne = ["#f59e0b" if uf == "Paraíba" else "#475569" for uf in df_rank_ne["UF"]]

    fig_rank_ne = build_horizontal_ranking(
        df=df_rank_ne,
        value_col="TOTAL",
        label_col="UF",
        colors=colors_ne,
        benchmark_mean=mean_ne,
        benchmark_label="Média NE",
        title="Ranking Nordeste por Taxa de Evasão (2023–2024)",
    )
    st.plotly_chart(fig_rank_ne, use_container_width=True)

    st.markdown("---")

    # 4. Hierarchical Drilldown
    st.subheader("🔍 Drilldown: Brasil → Paraíba → Rio Tinto")
    df_drill = build_hierarchical_drilldown(df_trajectory)
    fig_drill = build_drilldown_time_series(df_drill)
    st.plotly_chart(fig_drill, use_container_width=True)

    render_highlight_box(
        "⚠️ <b>Perspectiva Hierárquica:</b> Enquanto as taxas transversais estaduais sugerem estabilidade, "
        "a curva acumulada (TDA) longitudinal revela aceleração crítica da evasão no ciclo de graduação em Rio Tinto.",
        is_warning=True,
    )

