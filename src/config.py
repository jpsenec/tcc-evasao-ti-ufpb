"""Application configuration and design system constants."""

from pathlib import Path
from typing import Any, Dict, List

# ==============================================================================
# PATH CONFIGURATIONS (PORTABLE)
# ==============================================================================
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
RAW_DATA_DIR: Path = PROJECT_ROOT / "dados" / "brutos"
PROCESSED_DATA_DIR: Path = PROJECT_ROOT / "dados" / "processados"

REGION_DATA_FILE: Path = RAW_DATA_DIR / "regiao" / "INDIC_REGIAO_2010_2024.xlsx"
STATE_DATA_FILE: Path = RAW_DATA_DIR / "uf" / "INDIC_UF_2010_2024.xlsx"
TRAJECTORY_DATA_FILE: Path = RAW_DATA_DIR / "INDICADORES_TRAJETORIA.csv"
CENSUS_PROFILE_FILE: Path = PROCESSED_DATA_DIR / "perfil_censal_riotinto_2020_2024.csv"

# ==============================================================================
# BUSINESS CONSTANTS & CODES
# ==============================================================================
CODE_MUNICIPALITY_RIO_TINTO: int = 2512903
CODE_UF_PB: int = 25
CODE_COURSE_LIC_CC: int = 98984  # Licenciatura em Ciência da Computação (UFPB)
CODE_COURSE_SI: int = 107360     # Sistemas de Informação - Bacharelado (UFPB)

FOCUS_COHORT_YEAR: int = 2020
FOCUS_YEARS: List[str] = ["2020-2021", "2021-2022", "2022-2023", "2023-2024"]

NORTHEAST_STATES: List[str] = [
    "Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba",
    "Pernambuco", "Piauí", "Rio Grande do Norte", "Sergipe"
]

BRAZIL_REGIONS: List[str] = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

REGION_CODE_MAP: Dict[int, str] = {
    1: "Norte",
    2: "Nordeste",
    3: "Sudeste",
    4: "Sul",
    5: "Centro-Oeste",
}

# ==============================================================================
# DESIGN SYSTEM & COLOR PALETTES
# ==============================================================================
REGION_COLORS: Dict[str, str] = {
    "Norte": "#06b6d4",
    "Nordeste": "#f59e0b",
    "Centro-Oeste": "#8b5cf6",
    "Sudeste": "#3b82f6",
    "Sul": "#10b981",
}

STATE_COLORS_NORTHEAST: Dict[str, str] = {
    "Alagoas": "#3b82f6",
    "Bahia": "#ef4444",
    "Ceará": "#10b981",
    "Maranhão": "#8b5cf6",
    "Paraíba": "#f59e0b",
    "Pernambuco": "#ec4899",
    "Piauí": "#06b6d4",
    "Rio Grande do Norte": "#84cc16",
    "Sergipe": "#0ea5e9",
}

DRILLDOWN_COLORS: Dict[str, str] = {
    "Brasil (Cursos TI)": "#3b82f6",
    "Paraíba (Cursos TI)": "#f59e0b",
    "Rio Tinto — UFPB": "#ef4444",
}

COURSE_COLORS: Dict[str, str] = {
    "Lic. CC": "#818cf8",
    "Sist. Info.": "#34d399",
}

# Base layout for Plotly figures (Dark Theme)
BASE_PLOT_LAYOUT: Dict[str, Any] = {
    "font_family": "Inter, sans-serif",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "#1e293b",
    "font_color": "#e2e8f0",
    "title_font_size": 16,
    "title_font_color": "#f1f5f9",
    "legend_bgcolor": "rgba(30,41,59,0.8)",
    "legend_bordercolor": "#334155",
    "legend_borderwidth": 1,
    "margin": {"t": 60, "b": 50, "l": 50, "r": 30},
}

