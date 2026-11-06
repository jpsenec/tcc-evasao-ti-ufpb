"""
=============================================================================
TCC — Dashboard Interativo: Evasão em Cursos de Tecnologia (2020–2024)
=============================================================================
Execute com:
    streamlit run dashboard.py
=============================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Evasão em TI — TCC Paraíba",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado premium
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main { background-color: #0f172a; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

h1 { color: #f1f5f9 !important; font-weight: 700; }
h2 { color: #e2e8f0 !important; font-weight: 600; }
h3 { color: #cbd5e1 !important; }

.metric-card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
}

.stMetric {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 1rem;
}

.stMetric label { color: #94a3b8 !important; }
.stMetric [data-testid="metric-container"] { color: #f1f5f9; }

.highlight-box {
    background: linear-gradient(135deg, #1e40af20, #0f172a);
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    color: #e2e8f0;
}

.highlight-box-warning {
    background: linear-gradient(135deg, #92400e20, #0f172a);
    border-left: 4px solid #f59e0b;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    color: #e2e8f0;
}

.sidebar .sidebar-content { background-color: #1e293b; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CAMINHOS DAS FONTES (DINÂMICOS E PORTÁVEIS)
# ==============================================================================
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS_LOCAL = os.path.join(PASTA_PROJETO, "dados", "brutos")

ARQ_REGIAO_XLSX = os.path.join(PASTA_DADOS_LOCAL, "regiao", "INDIC_REGIAO_2010_2024.xlsx")
ARQ_UF_XLSX = os.path.join(PASTA_DADOS_LOCAL, "uf", "INDIC_UF_2010_2024.xlsx")
ARQ_TRAJ = os.path.join(PASTA_DADOS_LOCAL, "INDICADORES_TRAJETORIA.csv")

CO_MUNICIPIO_RIO_TINTO = 2512903
CO_UF_PB = 25
CO_CURSO_LIC_CC = 98984
CO_CURSO_SI = 107360
ANOS_FOCO = ["2020-2021", "2021-2022", "2022-2023", "2023-2024"]
ESTADOS_NORDESTE = ["Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba",
                    "Pernambuco", "Piauí", "Rio Grande do Norte", "Sergipe"]

CORES_REGIOES = {
    "Norte": "#06b6d4", "Nordeste": "#f59e0b",
    "Centro-Oeste": "#8b5cf6", "Sudeste": "#3b82f6", "Sul": "#10b981",
}
LAYOUT_BASE = dict(
    font_family="Inter, sans-serif",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#1e293b",
    font_color="#e2e8f0",
    title_font_size=16,
    title_font_color="#f1f5f9",
    legend_bgcolor="rgba(30,41,59,0.8)",
    legend_bordercolor="#334155",
    legend_borderwidth=1,
    margin=dict(t=60, b=50, l=50, r=30),
)

# ==============================================================================
# CARGA DE DADOS (COM CACHE)
# ==============================================================================

@st.cache_data
def carregar_regiao():
    xl = pd.ExcelFile(ARQ_REGIAO_XLSX)
    df_raw = xl.parse("TX_EVASAO", header=None, skiprows=8)
    df = df_raw.iloc[:, :5].copy()
    df.columns = ["ANO_FLUXO", "REGIAO", "TOTAL", "FEMININO", "MASCULINO"]
    df = df[df["REGIAO"].notna()].copy()
    df = df[~df["REGIAO"].astype(str).str.startswith(("Fonte", "Nota"))].copy()
    df["ANO_FLUXO"] = df["ANO_FLUXO"].ffill()
    df = df[df["REGIAO"].notna() & (df["REGIAO"].astype(str).str.strip() != "")].copy()
    for col in ["TOTAL", "FEMININO", "MASCULINO"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["REGIAO"] = df["REGIAO"].astype(str).str.strip()
    df["ANO_FLUXO"] = df["ANO_FLUXO"].astype(str).str.strip()
    return df.dropna(subset=["TOTAL"])


@st.cache_data
def carregar_uf():
    xl = pd.ExcelFile(ARQ_UF_XLSX)
    df_raw = xl.parse("TX_EVASAO", header=None, skiprows=8)
    df = df_raw.iloc[:, :7].copy()
    df.columns = ["ANO_FLUXO", "UF", "TOTAL", "FEMININO", "MASCULINO", "PPI_SIM", "PPI_NAO"]
    df = df[df["UF"].notna()].copy()
    df = df[~df["UF"].astype(str).str.startswith(("Fonte", "Nota"))].copy()
    df["ANO_FLUXO"] = df["ANO_FLUXO"].ffill()
    df = df[df["UF"].notna() & (df["UF"].astype(str).str.strip() != "")].copy()
    for col in ["TOTAL", "FEMININO", "MASCULINO", "PPI_SIM", "PPI_NAO"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["UF"] = df["UF"].astype(str).str.strip()
    df["ANO_FLUXO"] = df["ANO_FLUXO"].astype(str).str.strip()
    return df.dropna(subset=["TOTAL"])


@st.cache_data
def carregar_trajetoria():
    colunas = [
        "CO_IES", "NO_IES", "TP_CATEGORIA_ADMINISTRATIVA", "TP_ORGANIZACAO_ACADEMICA",
        "CO_CURSO", "NO_CURSO", "CO_REGIAO", "CO_UF", "CO_MUNICIPIO",
        "TP_GRAU_ACADEMICO", "TP_MODALIDADE_ENSINO",
        "CO_CINE_ROTULO", "NO_CINE_ROTULO", "CO_CINE_AREA_GERAL", "NO_CINE_AREA_GERAL",
        "NU_ANO_INGRESSO", "NU_ANO_REFERENCIA", "NU_PRAZO_INTEGRALIZACAO",
        "NU_ANO_INTEGRALIZACAO", "NU_PRAZO_ACOMPANHAMENTO", "NU_ANO_MAXIMO_ACOMPANHAMENTO",
        "QT_INGRESSANTE", "QT_PERMANENCIA", "QT_CONCLUINTE", "QT_DESISTENCIA", "QT_FALECIDO",
        "TAP", "TCA", "TDA", "TCAN", "TADA"
    ]
    df = pd.read_csv(ARQ_TRAJ, sep=";", encoding="latin1", header=None,
                     skiprows=9, engine="python", names=colunas, on_bad_lines="skip")
    for col in ["CO_IES", "CO_UF", "CO_MUNICIPIO", "CO_CURSO",
                "TP_GRAU_ACADEMICO", "NU_ANO_REFERENCIA", "QT_INGRESSANTE",
                "NU_ANO_INGRESSO", "CO_CINE_AREA_GERAL"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["TAP", "TCA", "TDA", "TCAN", "TADA"]:
        df[col] = df[col].astype(str).str.replace(",", ".").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["CO_IES", "CO_UF"]).copy()
    df = df[df["CO_IES"] > 0].copy()
    df = df[df["NU_ANO_INGRESSO"] == 2020].copy()
    return df


# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("## 📉 TCC — Evasão em TI")
    st.markdown("**Paraíba · 2020–2024**")
    st.markdown("---")
    aba = st.radio(
        "Navegação:",
        ["🌎 Nacional & Regiões", "📍 Paraíba no Nordeste", "🎓 Rio Tinto (UFPB)"],
        index=0
    )
    st.markdown("---")
    st.markdown("""
    **Fontes:**
    - INEP/MEC — Censo da Educação Superior
    - Indicadores de Trajetória 2020–2024 (INEP)
    - Taxa de Evasão por Região e UF (INEP)
    """)

# ==============================================================================
# CARREGAMENTO
# ==============================================================================
with st.spinner("🔄 Carregando bases de dados... (primeira vez pode demorar)"):
    df_reg = carregar_regiao()
    df_uf = carregar_uf()
    df_traj = carregar_trajetoria()

# ==============================================================================
# ABA 1 — NACIONAL & REGIÕES
# ==============================================================================
if aba == "🌎 Nacional & Regiões":
    st.title("🌎 Evasão em Cursos de Tecnologia — Panorama Nacional (2020–2024)")

    df_foco = df_reg[df_reg["ANO_FLUXO"].isin(ANOS_FOCO)]

    # Métricas rápidas
    col1, col2, col3, col4, col5 = st.columns(5)
    for col, regiao in zip([col1, col2, col3, col4, col5],
                            ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]):
        val_2024 = df_foco[(df_foco["REGIAO"] == regiao) & (df_foco["ANO_FLUXO"] == "2023-2024")]["TOTAL"]
        val_2020 = df_foco[(df_foco["REGIAO"] == regiao) & (df_foco["ANO_FLUXO"] == "2020-2021")]["TOTAL"]
        v = float(val_2024.iloc[0]) if not val_2024.empty else 0
        d = float(val_2024.iloc[0] - val_2020.iloc[0]) if (not val_2024.empty and not val_2020.empty) else 0
        col.metric(regiao, f"{v:.1f}%", f"{d:+.1f}% vs 2020")

    st.markdown("---")

    # Gráfico 1: Série temporal por região
    st.subheader("📈 Evolução da Taxa de Evasão por Região (2020–2024)")
    fig1 = go.Figure()
    for regiao in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]:
        d = df_foco[df_foco["REGIAO"] == regiao]
        cor = CORES_REGIOES.get(regiao, "#94a3b8")
        is_ne = (regiao == "Nordeste")
        fig1.add_trace(go.Scatter(
            x=d["ANO_FLUXO"], y=d["TOTAL"],
            name=regiao, mode="lines+markers",
            line=dict(color=cor, width=4 if is_ne else 2),
            marker=dict(size=9 if is_ne else 6, color=cor),
            hovertemplate=f"<b>{regiao}</b><br>%{{x}}<br>Evasão: %{{y:.1f}}%<extra></extra>"
        ))
    fig1.update_layout(**LAYOUT_BASE, title="Série Temporal por Região",
                       xaxis_title="Período", yaxis_title="Taxa de Evasão (%)",
                       yaxis=dict(gridcolor="#334155"), xaxis=dict(gridcolor="#334155"))
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown('<div class="highlight-box">💡 <b>O Nordeste</b> apresenta trajetória acima da média nacional no período recente, reforçando a necessidade de políticas específicas de retenção.</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Gráfico 2: Ranking 2023-2024
    st.subheader("🏆 Ranking de Regiões — Período 2023–2024")
    df_rank = df_foco[df_foco["ANO_FLUXO"] == "2023-2024"].sort_values("TOTAL")
    cores_rank = [CORES_REGIOES.get(r, "#94a3b8") for r in df_rank["REGIAO"]]
    fig2 = go.Figure(go.Bar(
        x=df_rank["TOTAL"], y=df_rank["REGIAO"], orientation="h",
        marker_color=cores_rank,
        text=[f"{v:.1f}%" for v in df_rank["TOTAL"]],
        textposition="outside", textfont=dict(color="#f1f5f9"),
        hovertemplate="<b>%{y}</b><br>Taxa: %{x:.1f}%<extra></extra>"
    ))
    media = df_rank["TOTAL"].mean()
    fig2.add_vline(x=media, line_dash="dash", line_color="#ef4444",
                   annotation_text=f"Média: {media:.1f}%", annotation_font_color="#ef4444")
    fig2.update_layout(**LAYOUT_BASE, title="Ranking por Taxa de Evasão (2023–2024)",
                       xaxis=dict(range=[0, df_rank["TOTAL"].max() * 1.3], gridcolor="#334155"),
                       yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig2, use_container_width=True)


# ==============================================================================
# ABA 2 — PARAÍBA NO NORDESTE
# ==============================================================================
elif aba == "📍 Paraíba no Nordeste":
    st.title("📍 Paraíba no Contexto do Nordeste (2020–2024)")

    df_foco_uf = df_uf[df_uf["ANO_FLUXO"].isin(ANOS_FOCO)]

    # Métricas da Paraíba
    pb_2024 = df_foco_uf[(df_foco_uf["UF"] == "Paraíba") & (df_foco_uf["ANO_FLUXO"] == "2023-2024")]
    pb_2020 = df_foco_uf[(df_foco_uf["UF"] == "Paraíba") & (df_foco_uf["ANO_FLUXO"] == "2020-2021")]

    val_pb24 = float(pb_2024["TOTAL"].iloc[0]) if not pb_2024.empty else 0
    val_pb20 = float(pb_2020["TOTAL"].iloc[0]) if not pb_2020.empty else 0
    fem_pb24 = float(pb_2024["FEMININO"].iloc[0]) if not pb_2024.empty else 0
    masc_pb24 = float(pb_2024["MASCULINO"].iloc[0]) if not pb_2024.empty else 0

    ne_2024 = df_foco_uf[(df_foco_uf["UF"].isin(ESTADOS_NORDESTE)) & (df_foco_uf["ANO_FLUXO"] == "2023-2024")]
    media_ne = ne_2024["TOTAL"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 Evasão PB (2023-24)", f"{val_pb24:.1f}%", f"{val_pb24 - val_pb20:+.1f}% vs 2020")
    c2.metric("📊 Média Nordeste", f"{media_ne:.1f}%")
    c3.metric("👩 Taxa Feminina (PB)", f"{fem_pb24:.1f}%")
    c4.metric("👨 Taxa Masculina (PB)", f"{masc_pb24:.1f}%")

    st.markdown("---")

    # Gráfico 3: PB vs Nordeste
    st.subheader("📊 Paraíba vs Estados do Nordeste — Série Temporal")
    df_ne_foco = df_foco_uf[df_foco_uf["UF"].isin(ESTADOS_NORDESTE)]
    fig3 = go.Figure()
    for uf in ESTADOS_NORDESTE:
        d = df_ne_foco[df_ne_foco["UF"] == uf]
        if d.empty:
            continue
        is_pb = (uf == "Paraíba")
        
        # Paleta de cores para os estados do Nordeste
        cores_ne = {
            "Alagoas": "#3b82f6", "Bahia": "#ef4444", "Ceará": "#10b981",
            "Maranhão": "#8b5cf6", "Paraíba": "#f59e0b", "Pernambuco": "#ec4899",
            "Piauí": "#06b6d4", "Rio Grande do Norte": "#84cc16", "Sergipe": "#0ea5e9"
        }
        cor_uf = cores_ne.get(uf, "#475569")
        
        fig3.add_trace(go.Scatter(
            x=d["ANO_FLUXO"], y=d["TOTAL"],
            name=uf, mode="lines+markers",
            line=dict(color=cor_uf, width=4 if is_pb else 2),
            marker=dict(size=10 if is_pb else 6, color=cor_uf),
            opacity=1.0 if is_pb else 0.7,
            hovertemplate=f"<b>{uf}</b><br>%{{x}}<br>Evasão: %{{y:.1f}}%<extra></extra>"
        ))
    fig3.update_layout(**LAYOUT_BASE, title="Taxa de Evasão: Paraíba 🟡 vs Demais Estados do Nordeste",
                       xaxis_title="Período", yaxis_title="Taxa de Evasão (%)",
                       yaxis=dict(gridcolor="#334155"), xaxis=dict(gridcolor="#334155"))
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # Ranking Nordeste em 2023-2024
    st.subheader("🏅 Ranking Nordeste — 2023–2024")
    df_rank_ne = ne_2024.sort_values("TOTAL", ascending=True)
    cores_ne = ["#f59e0b" if u == "Paraíba" else "#475569" for u in df_rank_ne["UF"]]
    fig_rank = go.Figure(go.Bar(
        x=df_rank_ne["TOTAL"], y=df_rank_ne["UF"], orientation="h",
        marker_color=cores_ne,
        text=[f"{v:.1f}%" for v in df_rank_ne["TOTAL"]],
        textposition="outside", textfont=dict(color="#f1f5f9"),
        hovertemplate="<b>%{y}</b><br>Taxa: %{x:.1f}%<extra></extra>"
    ))
    fig_rank.add_vline(x=media_ne, line_dash="dash", line_color="#ef4444",
                       annotation_text=f"Média NE: {media_ne:.1f}%", annotation_font_color="#ef4444")
    fig_rank.update_layout(**LAYOUT_BASE, title="Ranking Nordeste por Taxa de Evasão (2023–2024)",
                           xaxis=dict(range=[0, df_rank_ne["TOTAL"].max() * 1.3], gridcolor="#334155"),
                           yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_rank, use_container_width=True)

    # Drilldown Brasil->PB->Rio Tinto
    st.markdown("---")
    st.subheader("🔍 Drilldown: Brasil → Paraíba → Rio Tinto")

    # Filtra cursos da área de TIC (CINE 6) e Licenciatura em Computação (CINE 0114C05)
    df_ti = df_traj[
        ((df_traj["CO_CINE_AREA_GERAL"] == 6) | (df_traj["CO_CINE_ROTULO"] == "0114C05")) &
        (df_traj["TP_GRAU_ACADEMICO"].isin([1, 2]))
    ].copy()

    df_ti_foco = df_ti[df_ti["NU_ANO_REFERENCIA"].between(2020, 2024)].copy()

    # Função vetorizada para calcular média ponderada por grupo
    def calc_tda_ponderada(g):
        pesos = g["QT_INGRESSANTE"].sum()
        if pesos > 0:
            return (g["TDA"] * g["QT_INGRESSANTE"]).sum() / pesos
        return 0.0

    # Nível Brasil
    br_agg = df_ti_foco.groupby("NU_ANO_REFERENCIA").apply(
        lambda g: pd.Series({"TDA_MEDIA": calc_tda_ponderada(g), "NIVEL": "Brasil (Cursos TI)"})
    ).reset_index()
    br_agg.rename(columns={"NU_ANO_REFERENCIA": "ANO"}, inplace=True)

    # Nível Paraíba
    pb_agg = df_ti_foco[df_ti_foco["CO_UF"] == CO_UF_PB].groupby("NU_ANO_REFERENCIA").apply(
        lambda g: pd.Series({"TDA_MEDIA": calc_tda_ponderada(g), "NIVEL": "Paraíba (Cursos TI)"})
    ).reset_index()
    pb_agg.rename(columns={"NU_ANO_REFERENCIA": "ANO"}, inplace=True)

    # Nível Rio Tinto (apenas cursos de TI)
    rt_agg = df_ti_foco[df_ti_foco["CO_MUNICIPIO"] == CO_MUNICIPIO_RIO_TINTO].groupby("NU_ANO_REFERENCIA").apply(
        lambda g: pd.Series({"TDA_MEDIA": calc_tda_ponderada(g), "NIVEL": "Rio Tinto — UFPB"})
    ).reset_index()
    rt_agg.rename(columns={"NU_ANO_REFERENCIA": "ANO"}, inplace=True)

    df_drill = pd.concat([br_agg, pb_agg, rt_agg], ignore_index=True)

    cores_drill = {"Brasil (Cursos TI)": "#3b82f6", "Paraíba (Cursos TI)": "#f59e0b", "Rio Tinto — UFPB": "#ef4444"}
    fig_drill = go.Figure()
    for nivel, cor in cores_drill.items():
        d = df_drill[df_drill["NIVEL"] == nivel]
        fig_drill.add_trace(go.Scatter(
            x=d["ANO"].astype(str), y=d["TDA_MEDIA"],
            name=nivel, mode="lines+markers",
            line=dict(color=cor, width=3),
            marker=dict(size=10, color=cor, line=dict(color="#0f172a", width=2)),
            hovertemplate=f"<b>{nivel}</b><br>Ano: %{{x}}<br>TDA: %{{y:.1f}}%<extra></extra>"
        ))
    fig_drill.update_layout(**LAYOUT_BASE,
                            title="TDA Acumulada — Brasil 🔵 → Paraíba 🟡 → Rio Tinto 🔴",
                            xaxis_title="Ano de Referência",
                            yaxis_title="Taxa de Desistência Acumulada (%)",
                            yaxis=dict(gridcolor="#334155"),
                            xaxis=dict(gridcolor="#334155"))
    st.plotly_chart(fig_drill, use_container_width=True)

    st.markdown('<div class="highlight-box-warning">⚠️ <b>Perspectiva Hierárquica:</b> Este gráfico mostra como a evasão acumulada cresce ao longo dos anos de referência da coorte 2020, comparando o comportamento nacional, estadual e local.</div>', unsafe_allow_html=True)


# ==============================================================================
# ABA 3 — RIO TINTO (UFPB)
# ==============================================================================
elif aba == "🎓 Rio Tinto (UFPB)":
    st.title("🎓 Análise dos Cursos de TI — UFPB Campus Rio Tinto")

    df_rt = df_traj[df_traj["CO_MUNICIPIO"] == CO_MUNICIPIO_RIO_TINTO].copy()
    df_cc = df_rt[df_rt["CO_CURSO"] == CO_CURSO_LIC_CC].sort_values("NU_ANO_REFERENCIA")
    df_si = df_rt[df_rt["CO_CURSO"] == CO_CURSO_SI].sort_values("NU_ANO_REFERENCIA")

    # Métricas dos cursos
    st.markdown("### 📊 Métricas da Coorte 2020 (Acompanhamento até 2024)")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🟣 Licenciatura em Ciência da Computação**")
        if not df_cc.empty:
            ing = int(df_cc["QT_INGRESSANTE"].iloc[0])
            tda_24 = float(df_cc[df_cc["NU_ANO_REFERENCIA"] == 2024]["TDA"].values[0]) if 2024 in df_cc["NU_ANO_REFERENCIA"].values else 0
            perm_24 = int(df_cc[df_cc["NU_ANO_REFERENCIA"] == 2024]["QT_PERMANENCIA"].values[0]) if 2024 in df_cc["NU_ANO_REFERENCIA"].values else 0
            c1a, c1b, c1c = st.columns(3)
            c1a.metric("Ingressantes (2020)", ing)
            c1b.metric("TDA em 2024", f"{tda_24:.1f}%")
            c1c.metric("Ainda ativos (2024)", perm_24)

    with col2:
        st.markdown("**🟢 Sistemas de Informação (Bacharelado)**")
        if not df_si.empty:
            ing_si = int(df_si["QT_INGRESSANTE"].iloc[0])
            tda_si = float(df_si[df_si["NU_ANO_REFERENCIA"] == 2024]["TDA"].values[0]) if 2024 in df_si["NU_ANO_REFERENCIA"].values else 0
            perm_si = int(df_si[df_si["NU_ANO_REFERENCIA"] == 2024]["QT_PERMANENCIA"].values[0]) if 2024 in df_si["NU_ANO_REFERENCIA"].values else 0
            c2a, c2b, c2c = st.columns(3)
            c2a.metric("Ingressantes (2020)", ing_si)
            c2b.metric("TDA em 2024", f"{tda_si:.1f}%")
            c2c.metric("Ainda ativos (2024)", perm_si)

    st.markdown("---")

    # Gráfico 5: Trajetória comparada dos dois cursos
    st.subheader("📉 Trajetória de Desistência — TDA Acumulada e Anual")

    fig5 = go.Figure()

    # Licenciatura CC
    if not df_cc.empty:
        fig5.add_trace(go.Bar(
            x=df_cc["NU_ANO_REFERENCIA"].astype(str), y=df_cc["TDA"],
            name="TDA Acum. — Lic. CC", marker_color="#818cf8", opacity=0.8,
            hovertemplate="<b>Lic. CC</b><br>Ano: %{x}<br>TDA Acum.: %{y:.1f}%<extra></extra>"
        ))
        fig5.add_trace(go.Scatter(
            x=df_cc["NU_ANO_REFERENCIA"].astype(str), y=df_cc["TADA"],
            name="TADA Anual — Lic. CC", mode="lines+markers",
            line=dict(color="#c7d2fe", width=2, dash="dot"),
            marker=dict(size=7, color="#c7d2fe"),
            hovertemplate="<b>Lic. CC</b><br>Ano: %{x}<br>TADA Anual: %{y:.1f}%<extra></extra>"
        ))

    # Sistemas de Informação
    if not df_si.empty:
        fig5.add_trace(go.Bar(
            x=df_si["NU_ANO_REFERENCIA"].astype(str), y=df_si["TDA"],
            name="TDA Acum. — Sist. Info.", marker_color="#34d399", opacity=0.8,
            hovertemplate="<b>Sist. Info.</b><br>Ano: %{x}<br>TDA Acum.: %{y:.1f}%<extra></extra>"
        ))
        fig5.add_trace(go.Scatter(
            x=df_si["NU_ANO_REFERENCIA"].astype(str), y=df_si["TADA"],
            name="TADA Anual — Sist. Info.", mode="lines+markers",
            line=dict(color="#a7f3d0", width=2, dash="dot"),
            marker=dict(size=7, color="#a7f3d0"),
            hovertemplate="<b>Sist. Info.</b><br>Ano: %{x}<br>TADA Anual: %{y:.1f}%<extra></extra>"
        ))

    fig5.update_layout(**LAYOUT_BASE,
                       title="Trajetória de Evasão — UFPB Rio Tinto (Coorte 2020)",
                       xaxis_title="Ano de Referência",
                       yaxis_title="Taxa (%)",
                       barmode="group",
                       yaxis=dict(gridcolor="#334155"),
                       xaxis=dict(gridcolor="#334155"))
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("---")

    # Gráfico 6: Licenciatura vs Bacharelado no contexto da PB
    st.subheader("🎯 Contexto: Licenciatura vs Bacharelado em TI na Paraíba (2024)")

    df_ti_pb = df_traj[
        (df_traj["CO_CINE_AREA_GERAL"] == 6) &
        (df_traj["TP_GRAU_ACADEMICO"].isin([1, 2])) &
        (df_traj["CO_UF"] == CO_UF_PB) &
        (df_traj["NU_ANO_REFERENCIA"] == 2024)
    ].copy()

    df_ti_pb["GRAU"] = df_ti_pb["TP_GRAU_ACADEMICO"].map({1: "Bacharelado", 2: "Licenciatura"})

    # Médias ponderadas por grau
    medias_grau = df_ti_pb.groupby("GRAU").apply(
        lambda g: pd.Series({"TDA_MEDIA": (g["TDA"] * g["QT_INGRESSANTE"]).sum() / g["QT_INGRESSANTE"].sum()
                             if g["QT_INGRESSANTE"].sum() > 0 else 0})
    ).reset_index()

    fig6 = go.Figure()
    for _, row in medias_grau.iterrows():
        cor = "#818cf8" if row["GRAU"] == "Licenciatura" else "#34d399"
        fig6.add_trace(go.Bar(
            x=[row["GRAU"]], y=[row["TDA_MEDIA"]],
            name=row["GRAU"], marker_color=cor,
            text=[f"{row['TDA_MEDIA']:.1f}%"], textposition="outside",
            textfont=dict(color="#f1f5f9", size=15),
            width=0.4,
            hovertemplate=f"<b>{row['GRAU']}</b><br>TDA Média (PB): {row['TDA_MEDIA']:.1f}%<extra></extra>"
        ))

    # Adicionar ponto dos cursos de Rio Tinto para contexto
    if not df_cc.empty and 2024 in df_cc["NU_ANO_REFERENCIA"].values:
        tda_cc_24 = float(df_cc[df_cc["NU_ANO_REFERENCIA"] == 2024]["TDA"].values[0])
        fig6.add_trace(go.Scatter(
            x=["Licenciatura"], y=[tda_cc_24],
            mode="markers", name="Lic. CC — Rio Tinto",
            marker=dict(size=18, color="#f59e0b", symbol="star",
                        line=dict(color="#0f172a", width=2)),
            hovertemplate=f"<b>Lic. CC — Rio Tinto</b><br>TDA 2024: {tda_cc_24:.1f}%<extra></extra>"
        ))

    if not df_si.empty and 2024 in df_si["NU_ANO_REFERENCIA"].values:
        tda_si_24 = float(df_si[df_si["NU_ANO_REFERENCIA"] == 2024]["TDA"].values[0])
        fig6.add_trace(go.Scatter(
            x=["Bacharelado"], y=[tda_si_24],
            mode="markers", name="Sist. Info. — Rio Tinto",
            marker=dict(size=18, color="#f59e0b", symbol="star",
                        line=dict(color="#0f172a", width=2)),
            hovertemplate=f"<b>Sist. Info. — Rio Tinto</b><br>TDA 2024: {tda_si_24:.1f}%<extra></extra>"
        ))

    fig6.update_layout(**LAYOUT_BASE,
                       title="TDA Média — Bacharelado vs Licenciatura em TI na PB (2024)\n⭐ = Cursos Rio Tinto (UFPB)",
                       yaxis_title="Taxa de Desistência Acumulada (%)",
                       yaxis=dict(gridcolor="#334155", range=[0, 80]),
                       xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                       showlegend=True)
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown("""
<div class="highlight-box-warning">
⭐ <b>As estrelas amarelas</b> marcam onde os cursos de Rio Tinto se situam em relação à média
da Paraíba — esse posicionamento é central para a análise do seu TCC.
</div>
""", unsafe_allow_html=True)

    # Tabela de dados brutos
    st.markdown("---")
    st.subheader("📋 Dados Detalhados — Cursos de Rio Tinto")
    cols_show = ["NO_CURSO", "NU_ANO_REFERENCIA", "QT_INGRESSANTE",
                 "QT_PERMANENCIA", "QT_CONCLUINTE", "QT_DESISTENCIA",
                 "TAP", "TDA", "TCA", "TADA"]
    df_show = df_rt[cols_show].copy() if not df_rt.empty else pd.DataFrame()
    if not df_show.empty:
        df_show = df_show.sort_values(["NO_CURSO", "NU_ANO_REFERENCIA"])
        st.dataframe(df_show.style.background_gradient(subset=["TDA"], cmap="Reds"),
                     use_container_width=True)
