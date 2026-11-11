"""
View module for the Campus IV Sociodemographic Profile & Permanence Factors section.

This view renders longitudinal analysis (2020–2024) of the two IT courses at
UFPB Campus IV (Rio Tinto), based on INEP Census microdata aggregated at course level.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.config import BASE_PLOT_LAYOUT, COURSE_COLORS
from src.ui.components import render_highlight_box
from src.data.transformers_census import (
    derive_ppi_counts,
    derive_percentages,
    compute_age_distribution,
    compute_school_origin,
    compute_quota_breakdown,
    compute_protection_factors,
)

# ---------------------------------------------------------------------------
# Design constants for this view
# ---------------------------------------------------------------------------
_COURSE_OPTIONS = ["Lic. Ciência da Computação", "Sistemas de Informação", "Ambos os Cursos"]

_COLOR_CC = COURSE_COLORS["Lic. CC"]           # purple-blue
_COLOR_SI = COURSE_COLORS["Sist. Info."]        # emerald green
_COLOR_PUBLIC = "#f59e0b"                        # amber
_COLOR_PRIVATE = "#64748b"                       # slate
_COLOR_COTISTAS = "#818cf8"                      # indigo
_COLOR_PPI = "#f97316"                           # orange
_COLOR_LOW_INCOME = "#10b981"                    # green
_COLOR_PROTECTION_MAT = "#475569"               # slate-600
_COLOR_PROTECTION_CONC = "#f59e0b"              # amber


# ---------------------------------------------------------------------------
# Internal chart builders (private to this view)
# ---------------------------------------------------------------------------

def _apply_local_theme(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    """Applies the standard dark theme to a figure in this view."""
    fig.update_layout(
        **BASE_PLOT_LAYOUT,
        title=title,
        height=height,
        margin=dict(t=50, b=40, l=50, r=30),
    )
    return fig


def _build_situation_donut(df_course: pd.DataFrame, year: int) -> go.Figure:
    """Donut chart: distribution of student situations (mat / trancada / desvinculado / conc)."""
    row = df_course[df_course["NU_ANO_CENSO"] == year]
    if row.empty:
        return go.Figure()
    row = row.iloc[0]

    total_mat   = int(row.get("QT_MAT", 0))
    trancados   = int(row.get("QT_SIT_TRANCADA", 0))
    desvinc     = int(row.get("QT_SIT_DESVINCULADO", 0))
    concluintes = int(row.get("QT_CONC", 0))
    # active = enrolled minus those who left or graduated (approximate)
    ativos = max(total_mat - trancados - desvinc - concluintes, 0)

    labels = ["Ativos", "Trancados", "Desvinculados", "Concluintes"]
    values = [ativos, trancados, desvinc, concluintes]
    colors = ["#3b82f6", "#f59e0b", "#ef4444", "#10b981"]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker_colors=colors,
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Qtd: %{value}<br>%{percent}<extra></extra>",
    ))
    return _apply_local_theme(fig, f"Situação dos Estudantes — {year}", height=340)


def _build_age_bars(df_course: pd.DataFrame, moment: str) -> go.Figure:
    """Grouped bar chart: age bands across census years for a given moment."""
    df_tidy = compute_age_distribution(df_course, moment)
    if df_tidy.empty:
        return go.Figure()

    moment_label = {"ING": "Ingressantes", "MAT": "Matriculados", "CONC": "Concluintes"}[moment]
    years = sorted(df_tidy["NU_ANO_CENSO"].unique())
    faixas = df_tidy["faixa_etaria"].unique()

    palette = ["#818cf8", "#34d399", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899", "#84cc16", "#0ea5e9"]

    fig = go.Figure()
    for i, faixa in enumerate(faixas):
        sub = df_tidy[df_tidy["faixa_etaria"] == faixa]
        fig.add_trace(go.Bar(
            x=[str(y) for y in sub["NU_ANO_CENSO"]],
            y=sub["quantidade"],
            name=faixa,
            marker_color=palette[i % len(palette)],
            hovertemplate=f"<b>{faixa}</b><br>Ano: %{{x}}<br>Qtd: %{{y}}<extra></extra>",
        ))

    fig.update_layout(barmode="stack")
    return _apply_local_theme(
        fig,
        f"Distribuição por Faixa Etária — {moment_label} (2020–2024)",
        height=380,
    )


def _build_school_origin_bars(df_course: pd.DataFrame) -> go.Figure:
    """Grouped bar chart: public vs private school origin across years and moments."""
    df_tidy = compute_school_origin(df_course)
    if df_tidy.empty:
        return go.Figure()

    # Restrict to Ingressantes for readability; most relevant for context
    df_ing = df_tidy[df_tidy["momento"] == "Ingressantes"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[str(y) for y in df_ing["NU_ANO_CENSO"]],
        y=df_ing["Escola Pública"],
        name="Escola Pública",
        marker_color=_COLOR_PUBLIC,
        text=df_ing["Escola Pública"],
        textposition="auto",
        hovertemplate="<b>Escola Pública</b><br>Ano: %{x}<br>Qtd: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=[str(y) for y in df_ing["NU_ANO_CENSO"]],
        y=df_ing["Escola Privada"],
        name="Escola Privada",
        marker_color=_COLOR_PRIVATE,
        text=df_ing["Escola Privada"],
        textposition="auto",
        hovertemplate="<b>Escola Privada</b><br>Ano: %{x}<br>Qtd: %{y}<extra></extra>",
    ))

    fig.update_layout(barmode="group")
    return _apply_local_theme(fig, "Escola de Origem dos Ingressantes (2020–2024)", height=360)


def _build_quota_bars(df_course: pd.DataFrame, year: int) -> go.Figure:
    """Horizontal grouped bars: quota type breakdown for the selected year."""
    df_tidy = compute_quota_breakdown(df_course)
    df_year = df_tidy[df_tidy["NU_ANO_CENSO"] == year]
    if df_year.empty:
        return go.Figure()

    momentos = ["Ingressantes", "Matriculados", "Concluintes"]
    tipos = ["Total Cotas", "Esc. Pública", "Baixa Renda", "PPI"]
    colors_quota = {
        "Total Cotas":  _COLOR_COTISTAS,
        "Esc. Pública": _COLOR_PUBLIC,
        "Baixa Renda":  _COLOR_LOW_INCOME,
        "PPI":          _COLOR_PPI,
    }

    fig = go.Figure()
    for tipo in tipos:
        sub = df_year.set_index("momento").reindex(momentos)
        fig.add_trace(go.Bar(
            x=sub[tipo].fillna(0).values,
            y=momentos,
            orientation="h",
            name=tipo,
            marker_color=colors_quota[tipo],
            text=[f"{v:.0f}" for v in sub[tipo].fillna(0).values],
            textposition="auto",
            hovertemplate=f"<b>{tipo}</b><br>%{{y}}: %{{x}}<extra></extra>",
        ))

    fig.update_layout(barmode="group")
    return _apply_local_theme(fig, f"Reservas de Vagas por Tipo — {year}", height=360)


def _build_protection_factors_chart(df_course: pd.DataFrame) -> go.Figure:
    """
    Side-by-side grouped bars: % Matriculados vs % Concluintes for
    the two key protective factors (social support and extracurricular activity).
    """
    df_pct = derive_ppi_counts(df_course)
    df_pct = derive_percentages(df_pct)
    df_tidy = compute_protection_factors(df_pct)
    if df_tidy.empty:
        return go.Figure()

    # Aggregate across years for a longitudinal mean
    df_avg = (
        df_tidy
        .groupby("fator")[["Matriculados", "Concluintes"]]
        .mean()
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_avg["fator"],
        y=df_avg["Matriculados"],
        name="Matriculados (média)",
        marker_color=_COLOR_PROTECTION_MAT,
        text=[f"{v:.1f}%" for v in df_avg["Matriculados"]],
        textposition="outside",
        hovertemplate="<b>Matriculados</b><br>%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df_avg["fator"],
        y=df_avg["Concluintes"],
        name="Concluintes (média)",
        marker_color=_COLOR_PROTECTION_CONC,
        text=[f"{v:.1f}%" for v in df_avg["Concluintes"]],
        textposition="outside",
        hovertemplate="<b>Concluintes</b><br>%{x}: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(barmode="group")
    return _apply_local_theme(
        fig,
        "Fatores Protetivos — % Matriculados vs % Concluintes (Média 2020–2024)",
        height=380,
    )


def _build_gender_trend(df_course: pd.DataFrame) -> go.Figure:
    """Line chart: % female among entrants, enrolled, and graduates across years."""
    df_pct = derive_ppi_counts(df_course)
    df_pct = derive_percentages(df_pct)
    if df_pct.empty:
        return go.Figure()

    anos = df_pct["NU_ANO_CENSO"].astype(str).tolist()
    fig = go.Figure()
    for col, label, color in [
        ("PCT_ING_FEM",  "Ingressantes",  "#818cf8"),
        ("PCT_MAT_FEM",  "Matriculados",  "#34d399"),
        ("PCT_CONC_FEM", "Concluintes",   "#f59e0b"),
    ]:
        if col in df_pct.columns:
            fig.add_trace(go.Scatter(
                x=anos,
                y=df_pct[col].tolist(),
                name=label,
                mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=8, color=color),
                hovertemplate=f"<b>% Feminino — {label}</b><br>Ano: %{{x}}<br>%{{y:.1f}}%<extra></extra>",
            ))

    return _apply_local_theme(fig, "Participação Feminina ao Longo do Curso (% Mulheres)", height=360)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def render_profile_view(df_census: pd.DataFrame) -> None:
    """
    Renders the full Campus IV Sociodemographic Profile & Permanence Factors page.

    Parameters
    ----------
    df_census : pre-loaded perfil_censal_riotinto_2020_2024.csv (from load_census_profile_data)
    """
    st.title("🔬 Perfil e Fatores de Permanência — Campus IV (Rio Tinto)")
    st.caption(
        "Análise longitudinal baseada nos Microdados do Censo da Educação Superior (INEP, 2020–2024). "
        "Dados agregados no nível de curso — fonte: MICRODADOS_CADASTRO_CURSOS."
    )

    # ---- Selector controls ------------------------------------------------
    col_course, col_year = st.columns([2, 1])
    with col_course:
        selected_course = st.selectbox("Curso:", _COURSE_OPTIONS, index=0)
    with col_year:
        available_years = sorted(df_census["NU_ANO_CENSO"].unique(), reverse=True)
        selected_year = st.selectbox("Ano base (para análises pontuais):", available_years)

    # Build filtered DataFrames
    if selected_course == "Ambos os Cursos":
        df_cc = df_census[df_census["NO_CURSO"] == "Lic. Ciência da Computação"].copy()
        df_si = df_census[df_census["NO_CURSO"] == "Sistemas de Informação"].copy()
        df_view = df_census.copy()
    elif selected_course == "Lic. Ciência da Computação":
        df_cc = df_census[df_census["NO_CURSO"] == "Lic. Ciência da Computação"].copy()
        df_si = pd.DataFrame()
        df_view = df_cc
    else:
        df_cc = pd.DataFrame()
        df_si = df_census[df_census["NO_CURSO"] == "Sistemas de Informação"].copy()
        df_view = df_si

    if df_view.empty:
        st.warning("Sem dados para o curso selecionado.")
        return

    st.markdown("---")

    # ---- Section 1: KPI summary row --------------------------------------
    st.subheader(f"📊 Visão Geral — {selected_year}")

    df_pct = derive_ppi_counts(df_view)
    df_pct = derive_percentages(df_pct)
    df_year_view = df_pct[df_pct["NU_ANO_CENSO"] == selected_year]

    if not df_year_view.empty:
        # Aggregate (sum) in case "Ambos" is selected
        agg = df_year_view.agg({
            "QT_ING": "sum", "QT_MAT": "sum", "QT_CONC": "sum",
            "QT_SIT_TRANCADA": "sum", "QT_SIT_DESVINCULADO": "sum",
            "QT_ING_RESERVA_VAGA": "sum",
        }).to_dict()

        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("👥 Ingressantes", int(agg.get("QT_ING", 0)))
        kpi2.metric("📚 Matriculados", int(agg.get("QT_MAT", 0)))
        kpi3.metric("🎓 Concluintes", int(agg.get("QT_CONC", 0)))
        kpi4.metric("⏸️ Trancamentos", int(agg.get("QT_SIT_TRANCADA", 0)))
        kpi5.metric("❌ Desvinculados", int(agg.get("QT_SIT_DESVINCULADO", 0)))

    st.markdown("---")

    # ---- Section 2: Situação atual (donut) + Escola de origem (bar) ------
    st.subheader("🧩 Situação dos Estudantes e Perfil de Origem")

    col_donut, col_escola = st.columns(2)

    with col_donut:
        # If "Ambos", show CC by default for the donut (can't sum a donut cleanly)
        df_donut_src = df_cc if not df_cc.empty else df_si
        st.plotly_chart(
            _build_situation_donut(df_donut_src, selected_year),
            use_container_width=True,
        )

    with col_escola:
        st.plotly_chart(_build_school_origin_bars(df_view), use_container_width=True)

    render_highlight_box(
        "💡 A maioria dos ingressantes em Rio Tinto vem de <b>escolas públicas</b>, "
        "reforçando o perfil periférico do campus e a importância de políticas de permanência."
    )

    st.markdown("---")

    # ---- Section 3: Faixa etária -----------------------------------------
    st.subheader("🎂 Distribuição Etária dos Ingressantes (2020–2024)")
    st.plotly_chart(_build_age_bars(df_view, "ING"), use_container_width=True)

    with st.expander("Ver distribuição etária dos concluintes"):
        st.plotly_chart(_build_age_bars(df_view, "CONC"), use_container_width=True)
        render_highlight_box(
            "💡 Os concluintes concentram-se na faixa <b>25–29 anos</b> — evidência de que "
            "o curso leva mais tempo do que o prazo mínimo para a maioria dos formandos."
        )

    st.markdown("---")

    # ---- Section 4: Cotas e Reservas de Vagas ----------------------------
    st.subheader(f"🏷️ Cotas e Reservas de Vagas — {selected_year}")
    st.plotly_chart(_build_quota_bars(df_view, selected_year), use_container_width=True)
    render_highlight_box(
        "💡 Em 2024, <b>100% dos ingressantes de Sistemas de Informação</b> entraram via algum tipo de cota — "
        "dado que revela o perfil socioeconômico do campus e deve ser considerado no planejamento pedagógico."
    )

    st.markdown("---")

    # ---- Section 5: Fatores protetivos -----------------------------------
    st.subheader("🛡️ Fatores Protetivos: Apoio Social e Atividades Extracurriculares")
    st.caption(
        "Comparação entre a taxa de adesão aos programas de apoio entre **todos os matriculados** "
        "e apenas os **concluintes**. Diferença positiva indica fator protetor da permanência."
    )
    st.plotly_chart(_build_protection_factors_chart(df_view), use_container_width=True)

    render_highlight_box(
        "⭐ <b>Principal achado:</b> Concluintes participam de atividades extracurriculares em taxa "
        "<b>2–3× maior</b> que a média dos matriculados. Fomento à iniciação científica e estágio "
        "pode ser uma alavanca efetiva de retenção.",
        is_warning=False,
    )

    st.markdown("---")

    # ---- Section 6: Participação feminina --------------------------------
    st.subheader("♀️ Participação Feminina ao Longo da Jornada Acadêmica")
    st.plotly_chart(_build_gender_trend(df_view), use_container_width=True)
    render_highlight_box(
        "💡 A participação feminina tende a ser maior entre concluintes do que entre ingressantes — "
        "sugerindo que, embora as mulheres entrem em menor número em TI, têm <b>melhor taxa de permanência</b>."
    )
