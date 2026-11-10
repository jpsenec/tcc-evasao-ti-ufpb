"""Plotly visual builder functions and chart templates."""

from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go

from src.config import (
    BASE_PLOT_LAYOUT,
    REGION_COLORS,
    STATE_COLORS_NORTHEAST,
    DRILLDOWN_COLORS,
    COURSE_COLORS,
)


def _apply_theme(fig: go.Figure, title: str, x_title: str = "", y_title: str = "") -> go.Figure:
    """Applies standardized dark layout, typography and grid styling."""
    fig.update_layout(
        **BASE_PLOT_LAYOUT,
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        xaxis=dict(gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155"),
    )
    return fig


def build_regional_time_series(df_regional: pd.DataFrame) -> go.Figure:
    """Builds multi-line time series chart for Brazilian geographic regions."""
    fig = go.Figure()

    for region in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]:
        sub_df = df_regional.loc[df_regional["REGIAO"] == region]
        color = REGION_COLORS.get(region, "#94a3b8")
        is_highlight = region == "Nordeste"

        fig.add_trace(
            go.Scatter(
                x=sub_df["ANO_FLUXO"],
                y=sub_df["TOTAL"],
                name=region,
                mode="lines+markers",
                line=dict(color=color, width=4 if is_highlight else 2),
                marker=dict(size=9 if is_highlight else 6, color=color),
                hovertemplate=f"<b>{region}</b><br>%{{x}}<br>Evasão: %{{y:.1f}}%<extra></extra>",
            )
        )

    return _apply_theme(fig, "Série Temporal por Região", "Período", "Taxa de Evasão (%)")


def build_horizontal_ranking(
    df: pd.DataFrame,
    value_col: str,
    label_col: str,
    colors: List[str],
    benchmark_mean: float,
    benchmark_label: str = "Média",
    title: str = "",
) -> go.Figure:
    """Builds horizontal bar ranking with vertical benchmark line."""
    fig = go.Figure(
        go.Bar(
            x=df[value_col],
            y=df[label_col],
            orientation="h",
            marker_color=colors,
            text=[f"{v:.1f}%" for v in df[value_col]],
            textposition="outside",
            textfont=dict(color="#f1f5f9"),
            hovertemplate="<b>%{y}</b><br>Taxa: %{x:.1f}%<extra></extra>",
        )
    )

    fig.add_vline(
        x=benchmark_mean,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"{benchmark_label}: {benchmark_mean:.1f}%",
        annotation_font_color="#ef4444",
    )

    max_x = df[value_col].max() if not df.empty else 20
    fig.update_layout(
        **BASE_PLOT_LAYOUT,
        title=title,
        xaxis=dict(range=[0, max_x * 1.3], gridcolor="#334155"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    )
    return fig


def build_northeast_time_series(df_northeast: pd.DataFrame, states: List[str]) -> go.Figure:
    """Builds time series comparing Paraíba with other Northeast states."""
    fig = go.Figure()

    for state in states:
        sub_df = df_northeast.loc[df_northeast["UF"] == state]
        if sub_df.empty:
            continue

        is_pb = state == "Paraíba"
        color = STATE_COLORS_NORTHEAST.get(state, "#475569")

        fig.add_trace(
            go.Scatter(
                x=sub_df["ANO_FLUXO"],
                y=sub_df["TOTAL"],
                name=state,
                mode="lines+markers",
                line=dict(color=color, width=4 if is_pb else 2),
                marker=dict(size=10 if is_pb else 6, color=color),
                opacity=1.0 if is_pb else 0.7,
                hovertemplate=f"<b>{state}</b><br>%{{x}}<br>Evasão: %{{y:.1f}}%<extra></extra>",
            )
        )

    return _apply_theme(
        fig,
        "Taxa de Evasão: Paraíba 🟡 vs Demais Estados do Nordeste",
        "Período",
        "Taxa de Evasão (%)",
    )


def build_drilldown_time_series(df_drill: pd.DataFrame) -> go.Figure:
    """Builds hierarchical line chart (Brazil -> State -> Campus)."""
    fig = go.Figure()

    for level, color in DRILLDOWN_COLORS.items():
        sub_df = df_drill.loc[df_drill["NIVEL"] == level]
        fig.add_trace(
            go.Scatter(
                x=sub_df["ANO"].astype(str),
                y=sub_df["TDA_MEDIA"],
                name=level,
                mode="lines+markers",
                line=dict(color=color, width=3),
                marker=dict(size=10, color=color, line=dict(color="#0f172a", width=2)),
                hovertemplate=f"<b>{level}</b><br>Ano: %{{x}}<br>TDA: %{{y:.1f}}%<extra></extra>",
            )
        )

    return _apply_theme(
        fig,
        "TDA Acumulada — Brasil 🔵 → Paraíba 🟡 → Rio Tinto 🔴",
        "Ano de Referência",
        "Taxa de Desistência Acumulada (%)",
    )


def build_course_trajectory_chart(df_cc: pd.DataFrame, df_si: pd.DataFrame) -> go.Figure:
    """Builds combined bar + line chart for Rio Tinto degree programs."""
    fig = go.Figure()

    # Licentiate in Computing (CC)
    if not df_cc.empty:
        fig.add_trace(
            go.Bar(
                x=df_cc["NU_ANO_REFERENCIA"].astype(str),
                y=df_cc["TDA"],
                name="TDA Acum. — Lic. CC",
                marker_color=COURSE_COLORS["Lic. CC"],
                opacity=0.85,
                hovertemplate="<b>Lic. CC</b><br>Ano: %{x}<br>TDA Acum.: %{y:.1f}%<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_cc["NU_ANO_REFERENCIA"].astype(str),
                y=df_cc["TADA"],
                name="TADA Anual — Lic. CC",
                mode="lines+markers",
                line=dict(color="#c7d2fe", width=2, dash="dot"),
                marker=dict(size=7, color="#c7d2fe"),
                hovertemplate="<b>Lic. CC</b><br>Ano: %{x}<br>TADA Anual: %{y:.1f}%<extra></extra>",
            )
        )

    # Information Systems (SI)
    if not df_si.empty:
        fig.add_trace(
            go.Bar(
                x=df_si["NU_ANO_REFERENCIA"].astype(str),
                y=df_si["TDA"],
                name="TDA Acum. — Sist. Info.",
                marker_color=COURSE_COLORS["Sist. Info."],
                opacity=0.85,
                hovertemplate="<b>Sist. Info.</b><br>Ano: %{x}<br>TDA Acum.: %{y:.1f}%<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_si["NU_ANO_REFERENCIA"].astype(str),
                y=df_si["TADA"],
                name="TADA Anual — Sist. Info.",
                mode="lines+markers",
                line=dict(color="#a7f3d0", width=2, dash="dot"),
                marker=dict(size=7, color="#a7f3d0"),
                hovertemplate="<b>Sist. Info.</b><br>Ano: %{x}<br>TADA Anual: %{y:.1f}%<extra></extra>",
            )
        )

    fig.update_layout(
        **BASE_PLOT_LAYOUT,
        title="Trajetória de Evasão — UFPB Rio Tinto (Coorte 2020)",
        xaxis_title="Ano de Referência",
        yaxis_title="Taxa (%)",
        barmode="group",
        xaxis=dict(gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155"),
    )
    return fig


def build_degree_comparison_chart(
    medias_grau: pd.DataFrame,
    rate_cc_2024: float,
    rate_si_2024: float,
) -> go.Figure:
    """Builds bar chart comparing state averages by degree with Rio Tinto course stars."""
    fig = go.Figure()

    # Vectorized traces for degree averages
    for _, row in medias_grau.iterrows():
        grau_name = row["GRAU"]
        color = COURSE_COLORS["Lic. CC"] if grau_name == "Licenciatura" else COURSE_COLORS["Sist. Info."]
        fig.add_trace(
            go.Bar(
                x=[grau_name],
                y=[row["TDA_MEDIA"]],
                name=grau_name,
                marker_color=color,
                text=[f"{row['TDA_MEDIA']:.1f}%"],
                textposition="outside",
                textfont=dict(color="#f1f5f9", size=14),
                width=0.4,
                hovertemplate=f"<b>{grau_name}</b><br>Média PB: {row['TDA_MEDIA']:.1f}%<extra></extra>",
            )
        )

    # Star markers for Rio Tinto benchmarks
    if rate_cc_2024 > 0:
        fig.add_trace(
            go.Scatter(
                x=["Licenciatura"],
                y=[rate_cc_2024],
                mode="markers",
                name="Lic. CC — Rio Tinto",
                marker=dict(size=18, color="#f59e0b", symbol="star", line=dict(color="#0f172a", width=2)),
                hovertemplate=f"<b>Lic. CC — Rio Tinto</b><br>TDA 2024: {rate_cc_2024:.1f}%<extra></extra>",
            )
        )

    if rate_si_2024 > 0:
        fig.add_trace(
            go.Scatter(
                x=["Bacharelado"],
                y=[rate_si_2024],
                mode="markers",
                name="Sist. Info. — Rio Tinto",
                marker=dict(size=18, color="#f59e0b", symbol="star", line=dict(color="#0f172a", width=2)),
                hovertemplate=f"<b>Sist. Info. — Rio Tinto</b><br>TDA 2024: {rate_si_2024:.1f}%<extra></extra>",
            )
        )

    fig.update_layout(
        **BASE_PLOT_LAYOUT,
        title="TDA Média — Bacharelado vs Licenciatura em TI na PB (2024)<br><sup>⭐ = Cursos Rio Tinto (UFPB)</sup>",
        yaxis_title="Taxa de Desistência Acumulada (%)",
        yaxis=dict(gridcolor="#334155", range=[0, 80]),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        showlegend=True,
    )
    return fig

