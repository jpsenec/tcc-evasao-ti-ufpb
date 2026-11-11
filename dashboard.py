"""
TCC — Dashboard Interativo: Evasão em Cursos de Tecnologia (2020–2024)
UFPB Campus IV (Rio Tinto)

Entrypoint da aplicação Streamlit.
Execute com:
    streamlit run dashboard.py
"""

import streamlit as st

from src.ui.styles import get_custom_css
from src.ui.components import render_sidebar_header
from src.data.loader import (
    load_regional_data,
    load_state_data,
    load_trajectory_data,
    load_census_profile_data,
)
from src.views.national import render_national_view
from src.views.regional import render_regional_view
from src.views.local import render_local_view
from src.views.profile import render_profile_view


def main() -> None:
    """Main application orchestrator."""
    st.set_page_config(
        page_title="Evasão em TI — TCC Paraíba",
        page_icon="📉",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject custom styling
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # Sidebar navigation
    selected_tab = render_sidebar_header()

    # Cached data ingestion
    with st.spinner("🔄 Carregando bases de dados do INEP..."):
        df_regional   = load_regional_data()
        df_state      = load_state_data()
        df_trajectory = load_trajectory_data()
        try:
            df_census = load_census_profile_data()
        except FileNotFoundError:
            df_census = None

    # Route views
    if selected_tab == "🌎 Nacional & Regiões":
        render_national_view(df_regional, df_trajectory)
    elif selected_tab == "📍 Paraíba no Nordeste":
        render_regional_view(df_state, df_trajectory)
    elif selected_tab == "🎓 Rio Tinto (UFPB)":
        render_local_view(df_trajectory)
    elif selected_tab == "🔬 Perfil Campus IV":
        if df_census is not None:
            render_profile_view(df_census)
        else:
            st.error(
                "Arquivo de perfil censal não encontrado. "
                "Execute `python scripts/extrair_perfil_censal_riotinto.py` para gerá-lo."
            )


if __name__ == "__main__":
    main()
