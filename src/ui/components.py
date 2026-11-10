"""Reusable UI layout components and notification cards."""

import streamlit as st


def render_highlight_box(message: str, is_warning: bool = False) -> None:
    """Renders a styled notification card with left accent border."""
    css_class = "highlight-box-warning" if is_warning else "highlight-box"
    html = f'<div class="{css_class}">{message}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_sidebar_header() -> str:
    """Renders standardized sidebar navigation and metadata."""
    with st.sidebar:
        st.markdown("## 📉 TCC — Evasão em TI")
        st.markdown("**Paraíba · 2020–2024**")
        st.markdown("---")

        active_tab = st.radio(
            "Navegação:",
            ["🌎 Nacional & Regiões", "📍 Paraíba no Nordeste", "🎓 Rio Tinto (UFPB)"],
            index=0,
        )

        st.markdown("---")
        st.markdown(
            """
            **Fontes de Dados:**
            - INEP/MEC — Censo da Educação Superior
            - Indicadores de Trajetória (2020–2024)
            - Taxa de Evasão por Região e UF (INEP)
            """
        )

    return active_tab

