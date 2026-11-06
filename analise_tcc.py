import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

"""
=============================================================================
TCC - Análise de Evasão em Cursos de Tecnologia na Paraíba (2020-2024)
=============================================================================
Fontes de Dados:
  - INDIC_REGIAO_2010_2024(TX_EVASAO).csv   → Taxa de evasão por região
  - INDIC_UF_2010_2024(TX_EVASAO).csv       → Taxa de evasão por UF
  - indicadores_trajetoria_educacao_superior_2020_2024 2(INDICADORES_TRAJETORIA).csv
                                             → Trajetória por curso/IES (coorte 2020→2024)

Foco:
  - Cursos de Tecnologia (Bacharelado e Licenciatura)
  - Período: 2020 a 2024
  - Perspectiva geográfica: Brasil → Nordeste → Paraíba → Rio Tinto (UFPB)
=============================================================================
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# ==============================================================================
# CONSTANTES E CAMINHOS
# ==============================================================================
PASTA_PROJETO = r"C:\Users\Senec\Desktop\Estudos\Projeto TCC"
PASTA_DADOS_LOCAL = os.path.join(PASTA_PROJETO, "dados")
PASTA_SAIDA = os.path.join(PASTA_PROJETO, "graficos_evasao")
PASTA_CSV_SAIDA = os.path.join(PASTA_PROJETO, "dados_processados")

ARQ_REGIAO_XLSX = os.path.join(PASTA_DADOS_LOCAL, "regiao", "INDIC_REGIAO_2010_2024.xlsx")
ARQ_UF_XLSX = os.path.join(PASTA_DADOS_LOCAL, "uf", "INDIC_UF_2010_2024.xlsx")
ARQ_TRAJ = os.path.join(PASTA_DADOS_LOCAL, "INDICADORES_TRAJETORIA.csv")

# Municípios e cursos de interesse
CO_MUNICIPIO_RIO_TINTO = 2512903
CO_UF_PB = 25
CO_IES_UFPB = 579
CO_CURSO_LIC_CC = 98984      # Licenciatura em Ciência da Computação (UFPB Rio Tinto)
CO_CURSO_SI = 107360         # Sistemas de Informação - Bacharelado (UFPB Rio Tinto)

ANOS_FOCO = ["2020-2021", "2021-2022", "2022-2023", "2023-2024"]
REGIOES_BRASIL = ["Centro-Oeste", "Nordeste", "Norte", "Sudeste", "Sul"]
ESTADOS_NORDESTE = ["Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba",
                    "Pernambuco", "Piauí", "Rio Grande do Norte", "Sergipe"]

# Paleta de cores premium
CORES_REGIOES = {
    "Norte":        "#06b6d4",
    "Nordeste":     "#f59e0b",
    "Centro-Oeste": "#8b5cf6",
    "Sudeste":      "#3b82f6",
    "Sul":          "#10b981",
    "Brasil":       "#ef4444",
}
COR_PB_DESTAQUE = "#f59e0b"
COR_OUTROS = "#94a3b8"
COR_LIC = "#818cf8"
COR_SI  = "#34d399"

LAYOUT_BASE = dict(
    font_family="Inter, sans-serif",
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    font_color="#334155",
    title_font_size=28,
    title_font_color="#0f172a",
    legend_bgcolor="rgba(255,255,255,0.9)",
    legend_bordercolor="#cbd5e1",
    legend_borderwidth=1,
    margin=dict(t=100, b=80, l=80, r=40),
)

# ==============================================================================
# FUNÇÕES DE CARGA E LIMPEZA
# ==============================================================================

def carregar_regiao() -> pd.DataFrame:
    """Carrega e limpa o arquivo de evasão por região (2010-2024) a partir do XLSX."""
    print("  [->] Carregando dados de evasao por REGIAO (XLSX)...")
    xl = pd.ExcelFile(ARQ_REGIAO_XLSX)
    # Aba TX_EVASAO, sem cabeçalho, pular as 8 linhas de metadados
    df_raw = xl.parse("TX_EVASAO", header=None, skiprows=8)

    # Colunas relevantes: 0=AnoFluxo, 1=Região, 2=Total, 3=Fem, 4=Masc
    df = df_raw.iloc[:, :5].copy()
    df.columns = ["ANO_FLUXO", "REGIAO", "TOTAL", "FEMININO", "MASCULINO"]

    # Remover últimas linhas de rodapé (notas e fonte)
    df = df[df["REGIAO"].notna()].copy()
    df = df[~df["REGIAO"].astype(str).str.startswith(("Fonte", "Nota"))].copy()

    # Propagar o AnoFluxo para linhas filhas
    df["ANO_FLUXO"] = df["ANO_FLUXO"].ffill()

    # Remover linhas sem região ou completamente vazias
    df = df[df["REGIAO"].notna() & (df["REGIAO"].astype(str).str.strip() != "")].copy()

    for col in ["TOTAL", "FEMININO", "MASCULINO"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["REGIAO"] = df["REGIAO"].astype(str).str.strip()
    df["ANO_FLUXO"] = df["ANO_FLUXO"].astype(str).str.strip()
    return df.dropna(subset=["TOTAL"])


def carregar_uf() -> pd.DataFrame:
    """Carrega e limpa o arquivo de evasão por UF (2010-2024) a partir do XLSX."""
    print("  [→] Carregando dados de evasão por UF/Estado (XLSX)...")
    xl = pd.ExcelFile(ARQ_UF_XLSX)
    df_raw = xl.parse("TX_EVASAO", header=None, skiprows=8)

    # Colunas: 0=AnoFluxo, 1=UF, 2=Total, 3=Fem, 4=Masc, 5=PPI_Sim, 6=PPI_Nao
    df = df_raw.iloc[:, :7].copy()
    df.columns = ["ANO_FLUXO", "UF", "TOTAL", "FEMININO", "MASCULINO", "PPI_SIM", "PPI_NAO"]

    # Remover linhas de rodapé (fonte/notas)
    df = df[df["UF"].notna()].copy()
    df = df[~df["UF"].astype(str).str.startswith(("Fonte", "Nota"))].copy()

    df["ANO_FLUXO"] = df["ANO_FLUXO"].ffill()
    df = df[df["UF"].notna() & (df["UF"].astype(str).str.strip() != "")].copy()

    for col in ["TOTAL", "FEMININO", "MASCULINO", "PPI_SIM", "PPI_NAO"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["UF"] = df["UF"].astype(str).str.strip()
    df["ANO_FLUXO"] = df["ANO_FLUXO"].astype(str).str.strip()
    return df.dropna(subset=["TOTAL"])


def carregar_trajetoria() -> pd.DataFrame:
    """Carrega e limpa o arquivo de indicadores de trajetória por curso/IES."""
    print("  [→] Carregando indicadores de trajetória por curso (arquivo grande, aguarde)...")
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

    df = pd.read_csv(ARQ_TRAJ, sep=";", encoding="latin1",
                     header=None, skiprows=9, engine="python",
                     names=colunas, on_bad_lines="skip")

    # Converter código para numérico
    df["CO_IES"] = pd.to_numeric(df["CO_IES"], errors="coerce")
    df["CO_UF"] = pd.to_numeric(df["CO_UF"], errors="coerce")
    df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce")
    df["CO_CURSO"] = pd.to_numeric(df["CO_CURSO"], errors="coerce")
    df["TP_GRAU_ACADEMICO"] = pd.to_numeric(df["TP_GRAU_ACADEMICO"], errors="coerce")
    df["NU_ANO_REFERENCIA"] = pd.to_numeric(df["NU_ANO_REFERENCIA"], errors="coerce")
    df["QT_INGRESSANTE"] = pd.to_numeric(df["QT_INGRESSANTE"], errors="coerce")

    for col in ["TAP", "TCA", "TDA", "TCAN", "TADA"]:
        df[col] = df[col].astype(str).str.replace(",", ".").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remover linhas de cabeçalho residuais (onde CO_IES não é número válido)
    df = df.dropna(subset=["CO_IES", "CO_UF"]).copy()
    df = df[df["CO_IES"] > 0].copy()

    # Filtrar apenas coorte 2020 (NU_ANO_INGRESSO = 2020)
    df = df[df["NU_ANO_INGRESSO"] == 2020].copy()

    return df


# ==============================================================================
# FILTROS AUXILIARES
# ==============================================================================

def filtrar_area_tecnologia(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra cursos da área de TIC (CINE 6) e Licenciatura em Computação (CINE 0114C05)."""
    return df[
        ((df["CO_CINE_AREA_GERAL"] == 6) | (df["CO_CINE_ROTULO"] == "0114C05")) &
        (df["TP_GRAU_ACADEMICO"].isin([1, 2]))
    ].copy()


def agregar_tda_brasil_por_ano(df_traj: pd.DataFrame) -> pd.DataFrame:
    """Calcula a TDA média ponderada (por ingressante) do Brasil para cursos de TI."""
    df = filtrar_area_tecnologia(df_traj)
    df = df[df["NU_ANO_REFERENCIA"].between(2020, 2024)]
    
    # TDA ponderada = soma(TDA * ingressantes) / soma(ingressantes)
    agg = df.groupby("NU_ANO_REFERENCIA").apply(
        lambda g: pd.Series({
            "TDA_MEDIA": (g["TDA"] * g["QT_INGRESSANTE"]).sum() / g["QT_INGRESSANTE"].sum()
            if g["QT_INGRESSANTE"].sum() > 0 else 0
        })
    ).reset_index()
    agg.columns = ["ANO", "TDA_MEDIA"]
    agg["NIVEL"] = "Brasil"
    return agg


def agregar_tda_pb_por_ano(df_traj: pd.DataFrame) -> pd.DataFrame:
    """Calcula a TDA média ponderada da Paraíba para cursos de TI."""
    df = filtrar_area_tecnologia(df_traj)
    df = df[(df["CO_UF"] == CO_UF_PB) & df["NU_ANO_REFERENCIA"].between(2020, 2024)]
    
    agg = df.groupby("NU_ANO_REFERENCIA").apply(
        lambda g: pd.Series({
            "TDA_MEDIA": (g["TDA"] * g["QT_INGRESSANTE"]).sum() / g["QT_INGRESSANTE"].sum()
            if g["QT_INGRESSANTE"].sum() > 0 else 0
        })
    ).reset_index()
    agg.columns = ["ANO", "TDA_MEDIA"]
    agg["NIVEL"] = "Paraíba"
    return agg


# ==============================================================================
# GERAÇÃO DOS GRÁFICOS
# ==============================================================================

def grafico1_serie_temporal_regioes(df_reg: pd.DataFrame, pasta: str):
    """
    Gráfico 1 — Série Temporal: Evasão por Região (2020-2024)
    Mostra como cada região evoluiu no período.
    """
    print("  [→] Gerando Gráfico 1: Série temporal por região...")
    df = df_reg[df_reg["ANO_FLUXO"].isin(ANOS_FOCO)].copy()

    fig = go.Figure()
    for regiao in REGIOES_BRASIL:
        d = df[df["REGIAO"] == regiao]
        cor = CORES_REGIOES.get(regiao, "#94a3b8")
        largura = 5 if regiao == "Nordeste" else 3
        dash = "solid" if regiao == "Nordeste" else "dot"

        fig.add_trace(go.Scatter(
            x=d["ANO_FLUXO"],
            y=d["TOTAL"],
            name=regiao,
            mode="lines+markers",
            line=dict(color=cor, width=largura, dash=dash),
            marker=dict(size=12, color=cor),
            hovertemplate=f"<b>{regiao}</b><br>Período: %{{x}}<br>Taxa: %{{y:.1f}}%<extra></extra>"
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title="📈 Evolução da Taxa de Evasão por Região Geográfica (2020–2024)",
        xaxis_title="<b>Período (Fluxo Anual)</b>",
        yaxis_title="<b>Taxa de Evasão (%)</b>",
        yaxis=dict(gridcolor="#e2e8f0", zeroline=False, title_font_size=22, tickfont_size=20),
        xaxis=dict(gridcolor="#e2e8f0", title_font_size=22, tickfont_size=20),
        legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=20)),
        annotations=[dict(
            text="<b>🔶 Nordeste em destaque</b>",
            x=0.02, y=0.97, xref="paper", yref="paper",
            showarrow=False, font=dict(size=22, color=CORES_REGIOES["Nordeste"])
        )]
    )

    fig.write_html(os.path.join(pasta, "grafico1_serie_temporal_regioes.html"))
    print("     ✓ Salvo: grafico1_serie_temporal_regioes.html")


def grafico2_ranking_regioes_2024(df_reg: pd.DataFrame, pasta: str):
    """
    Gráfico 2 — Ranking de Regiões por Evasão em 2023-2024
    Barras horizontais com destaque para o Nordeste.
    """
    print("  [→] Gerando Gráfico 2: Ranking de regiões em 2023-2024...")
    df = df_reg[df_reg["ANO_FLUXO"] == "2023-2024"].copy()
    df = df.sort_values("TOTAL", ascending=True)

    cores = [CORES_REGIOES.get(r, COR_OUTROS) for r in df["REGIAO"]]

    fig = go.Figure(go.Bar(
        x=df["TOTAL"],
        y=df["REGIAO"],
        orientation="h",
        marker_color=cores,
        text=[f"<b>{v:.1f}%</b>" for v in df["TOTAL"]],
        textposition="outside",
        textfont=dict(color="#0f172a", size=20),
        hovertemplate="<b>%{y}</b><br>Taxa de Evasão: %{x:.1f}%<extra></extra>"
    ))

    # Linha de média nacional
    media_nacional = df["TOTAL"].mean()
    fig.add_vline(x=media_nacional, line_dash="dash", line_color="#ef4444", line_width=3,
                  annotation_text=f"<b>Média: {media_nacional:.1f}%</b>",
                  annotation_font_color="#ef4444", annotation_font_size=20, annotation_position="top right")

    fig.update_layout(
        **LAYOUT_BASE,
        title="🏆 Ranking de Regiões por Taxa de Evasão — Período 2023–2024",
        xaxis_title="<b>Taxa de Evasão (%)</b>",
        yaxis_title="",
        xaxis=dict(gridcolor="#e2e8f0", range=[0, df["TOTAL"].max() * 1.25], title_font_size=22, tickfont_size=20),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont_size=20),
    )

    fig.write_html(os.path.join(pasta, "grafico2_ranking_regioes_2024.html"))
    print("     ✓ Salvo: grafico2_ranking_regioes_2024.html")


def grafico3_paraiba_vs_nordeste(df_uf: pd.DataFrame, pasta: str):
    """
    Gráfico 3 — Paraíba vs Estados do Nordeste (Série Temporal 2020-2024)
    """
    print("  [→] Gerando Gráfico 3: Paraíba vs Nordeste...")
    df = df_uf[
        (df_uf["ANO_FLUXO"].isin(ANOS_FOCO)) &
        (df_uf["UF"].isin(ESTADOS_NORDESTE))
    ].copy()

    fig = go.Figure()
    for uf in ESTADOS_NORDESTE:
        d = df[df["UF"] == uf]
        if d.empty:
            continue
        is_pb = uf == "Paraíba"
        
        # Paleta de cores para diferenciar os outros estados
        cores_ne = {
            "Alagoas": "#3b82f6", "Bahia": "#ef4444", "Ceará": "#10b981",
            "Maranhão": "#8b5cf6", "Paraíba": COR_PB_DESTAQUE, "Pernambuco": "#ec4899",
            "Piauí": "#06b6d4", "Rio Grande do Norte": "#84cc16", "Sergipe": "#0ea5e9"
        }
        cor_uf = cores_ne.get(uf, COR_OUTROS)
        
        fig.add_trace(go.Scatter(
            x=d["ANO_FLUXO"],
            y=d["TOTAL"],
            name=uf,
            mode="lines+markers",
            line=dict(
                color=cor_uf,
                width=6 if is_pb else 3,
            ),
            marker=dict(size=14 if is_pb else 8, color=cor_uf),
            opacity=1.0 if is_pb else 0.7,
            hovertemplate=f"<b>{uf}</b><br>%{{x}}<br>Evasão: %{{y:.1f}}%<extra></extra>"
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title="📍 Taxa de Evasão: Paraíba vs Estados do Nordeste (2020–2024)",
        xaxis_title="<b>Período</b>",
        yaxis_title="<b>Taxa de Evasão (%)</b>",
        yaxis=dict(gridcolor="#e2e8f0", title_font_size=22, tickfont_size=20),
        xaxis=dict(gridcolor="#e2e8f0", title_font_size=22, tickfont_size=20),
        legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=20)),
        annotations=[dict(
            text="<b>🟡 Paraíba em destaque</b>",
            x=0.02, y=0.97, xref="paper", yref="paper",
            showarrow=False, font=dict(size=22, color=COR_PB_DESTAQUE)
        )]
    )

    fig.write_html(os.path.join(pasta, "grafico3_paraiba_vs_nordeste.html"))
    print("     ✓ Salvo: grafico3_paraiba_vs_nordeste.html")


def grafico4_drilldown_brasil_pb_riotinto(df_reg: pd.DataFrame, df_uf: pd.DataFrame,
                                           df_traj: pd.DataFrame, pasta: str):
    """
    Gráfico 4 — Drilldown: Brasil → Paraíba → Rio Tinto
    Compara a TDA acumulada nos 3 níveis geográficos.
    """
    print("  [→] Gerando Gráfico 4: Drilldown Brasil → PB → Rio Tinto...")

    # --- Nível BRASIL (média dos cursos de TI) ---
    brasil_agg = agregar_tda_brasil_por_ano(df_traj)

    # --- Nível PARAÍBA ---
    pb_agg = agregar_tda_pb_por_ano(df_traj)

    # --- Nível RIO TINTO (apenas cursos de TI) ---
    df_ti = filtrar_area_tecnologia(df_traj)
    rt = df_ti[
        (df_ti["CO_MUNICIPIO"] == CO_MUNICIPIO_RIO_TINTO) &
        (df_ti["NU_ANO_REFERENCIA"].between(2020, 2024))
    ].copy()

    if not rt.empty:
        rt_agg = rt.groupby("NU_ANO_REFERENCIA").apply(
            lambda g: pd.Series({
                "TDA_MEDIA": (g["TDA"] * g["QT_INGRESSANTE"]).sum() / g["QT_INGRESSANTE"].sum()
                if g["QT_INGRESSANTE"].sum() > 0 else 0
            })
        ).reset_index()
        rt_agg.columns = ["ANO", "TDA_MEDIA"]
        rt_agg["NIVEL"] = "Rio Tinto (UFPB)"
    else:
        rt_agg = pd.DataFrame(columns=["ANO", "TDA_MEDIA", "NIVEL"])

    df_plot = pd.concat([brasil_agg, pb_agg, rt_agg], ignore_index=True)
    df_plot = df_plot[df_plot["ANO"].between(2020, 2024)]

    cores_niveis = {
        "Brasil": "#3b82f6",
        "Paraíba": COR_PB_DESTAQUE,
        "Rio Tinto (UFPB)": "#ef4444"
    }

    fig = go.Figure()
    for nivel, cor in cores_niveis.items():
        d = df_plot[df_plot["NIVEL"] == nivel]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["ANO"].astype(str),
            y=d["TDA_MEDIA"],
            name=nivel,
            mode="lines+markers",
            line=dict(color=cor, width=5),
            marker=dict(size=14, color=cor,
                        line=dict(color="#ffffff", width=2)),
            fill="tozeroy" if nivel == "Rio Tinto (UFPB)" else None,
            fillcolor=f"rgba(239,68,68,0.08)" if nivel == "Rio Tinto (UFPB)" else None,
            hovertemplate=f"<b>{nivel}</b><br>Ano: %{{x}}<br>TDA Acumulada: %{{y:.1f}}%<extra></extra>"
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title="🔍 Drilldown de Evasão Acumulada: Brasil → Paraíba → Rio Tinto (2020–2024)",
        xaxis_title="<b>Ano de Referência</b>",
        yaxis_title="<b>Taxa de Desistência Acumulada — TDA (%)</b>",
        yaxis=dict(gridcolor="#e2e8f0", title_font_size=22, tickfont_size=20),
        xaxis=dict(gridcolor="#e2e8f0", title_font_size=22, tickfont_size=20),
        legend=dict(orientation="h", x=0.5, y=-0.2, xanchor="center", font=dict(size=20)),
    )

    fig.write_html(os.path.join(pasta, "grafico4_drilldown_brasil_pb_riotinto.html"))
    print("     ✓ Salvo: grafico4_drilldown_brasil_pb_riotinto.html")


def grafico5_trajetoria_cursos_riotinto(df_traj: pd.DataFrame, pasta: str):
    """
    Gráfico 5 — Trajetória dos Cursos de Rio Tinto (2020→2024)
    Mostra TDA ano a ano para Licenciatura CC e Sistemas de Informação.
    """
    print("  [→] Gerando Gráfico 5: Trajetória dos cursos de Rio Tinto...")

    cursos = {
        CO_CURSO_LIC_CC: ("Lic. Ciência da Computação", COR_LIC),
        CO_CURSO_SI:     ("Sistemas de Informação (Bach.)", COR_SI),
    }

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=list(c[0] for c in cursos.values()),
        shared_yaxes=True,
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title="🎓 Trajetória de Evasão — Cursos UFPB Rio Tinto (Coorte 2020, Ref. 2020–2024)",
    )

    col_idx = 1
    for co_curso, (nome, cor) in cursos.items():
        d = df_traj[
            (df_traj["CO_CURSO"] == co_curso) &
            (df_traj["NU_ANO_REFERENCIA"].between(2020, 2024))
        ].sort_values("NU_ANO_REFERENCIA")

        if d.empty:
            col_idx += 1
            continue

        # TDA acumulada
        fig.add_trace(go.Bar(
            x=d["NU_ANO_REFERENCIA"].astype(str),
            y=d["TDA"],
            name=f"{nome} — TDA Acum.",
            marker_color=cor,
            opacity=0.85,
            showlegend=True,
            hovertemplate=f"<b>{nome}</b><br>Ano: %{{x}}<br>TDA Acumulada: %{{y:.1f}}%<extra></extra>"
        ), row=1, col=col_idx)

        # TADA anual (linha sobre as barras)
        fig.add_trace(go.Scatter(
            x=d["NU_ANO_REFERENCIA"].astype(str),
            y=d["TADA"],
            name=f"{nome} — TADA Anual",
            mode="lines+markers",
            line=dict(color="#1e293b", width=3, dash="dot"),
            marker=dict(size=10, color="#1e293b"),
            showlegend=True,
            hovertemplate=f"<b>{nome}</b><br>Ano: %{{x}}<br>TADA Anual: %{{y:.1f}}%<extra></extra>"
        ), row=1, col=col_idx)

        # Adiciona anotação com ingressantes
        ingressantes = int(d["QT_INGRESSANTE"].iloc[0]) if not d.empty else 0
        xref_val = "x domain" if col_idx == 1 else f"x{col_idx} domain"
        fig.add_annotation(
            text=f"<b>Coorte: {ingressantes} alunos</b>",
            x=0.5, y=1.12,
            xref=xref_val, yref="paper",
            showarrow=False,
            font=dict(size=18, color="#475569"),
        )

        col_idx += 1

    fig.update_xaxes(gridcolor="#e2e8f0", title_font_size=20, tickfont_size=18)
    fig.update_yaxes(gridcolor="#e2e8f0", title_text="<b>Taxa (%)</b>", title_font_size=20, tickfont_size=18, col=1)

    fig.write_html(os.path.join(pasta, "grafico5_trajetoria_cursos_riotinto.html"))
    print("     ✓ Salvo: grafico5_trajetoria_cursos_riotinto.html")


def grafico6_licenciatura_vs_bacharelado_pb(df_traj: pd.DataFrame, pasta: str):
    """
    Gráfico 6 — Licenciatura vs Bacharelado em TI na Paraíba
    Compara a TDA acumulada por grau acadêmico em 2024.
    """
    print("  [→] Gerando Gráfico 6: Licenciatura vs Bacharelado em TI na PB...")

    df = filtrar_area_tecnologia(df_traj)
    df = df[
        (df["CO_UF"] == CO_UF_PB) &
        (df["NU_ANO_REFERENCIA"] == 2024)
    ].copy()

    df["GRAU"] = df["TP_GRAU_ACADEMICO"].map({1: "Bacharelado", 2: "Licenciatura"})
    df = df.dropna(subset=["GRAU", "TDA"])

    # Gráfico de violino + boxplot combinado para ver distribuição
    fig = go.Figure()
    cores_grau = {"Bacharelado": "#3b82f6", "Licenciatura": "#8b5cf6"}

    for grau, cor in cores_grau.items():
        d = df[df["GRAU"] == grau]["TDA"]
        if d.empty:
            continue

        fig.add_trace(go.Violin(
            y=d,
            name=grau,
            box_visible=True,
            meanline_visible=True,
            points="all",
            jitter=0.3,
            marker=dict(color=cor, size=6, opacity=0.7),
            line_color=cor,
            fillcolor=f"rgba({int(cor[1:3], 16)},{int(cor[3:5], 16)},{int(cor[5:7], 16)},0.25)",
            hovertemplate=f"<b>{grau}</b><br>TDA: %{{y:.1f}}%<extra></extra>",
        ))

    # Linha de média do Brasil (estimada para comparação)
    df_brasil_tec = filtrar_area_tecnologia(df_traj)
    df_brasil_2024 = df_brasil_tec[df_brasil_tec["NU_ANO_REFERENCIA"] == 2024]
    media_brasil = (df_brasil_2024["TDA"] * df_brasil_2024["QT_INGRESSANTE"]).sum() / df_brasil_2024["QT_INGRESSANTE"].sum() if len(df_brasil_2024) > 0 else 0

    fig.add_hline(y=media_brasil, line_dash="dash", line_color="#ef4444", line_width=3,
                  annotation_text=f"<b>Média Brasil TI: {media_brasil:.1f}%</b>",
                  annotation_font_color="#ef4444", annotation_font_size=20)

    fig.update_layout(
        **LAYOUT_BASE,
        title="🎯 Distribuição da TDA por Grau Acadêmico em Cursos de TI — Paraíba (ref. 2024)",
        yaxis_title="<b>Taxa de Desistência Acumulada — TDA (%)</b>",
        yaxis=dict(gridcolor="#e2e8f0", title_font_size=22, tickfont_size=20),
        xaxis=dict(gridcolor="#e2e8f0", title_font_size=22, tickfont_size=20),
        violinmode="group",
    )

    fig.write_html(os.path.join(pasta, "grafico6_licenciatura_vs_bacharelado_pb.html"))
    print("     ✓ Salvo: grafico6_licenciatura_vs_bacharelado_pb.html")


# ==============================================================================
# EXPORTAÇÃO DE CSVs LIMPOS
# ==============================================================================

def exportar_csvs(df_reg, df_uf, df_traj, pasta_csv):
    """Exporta versões limpas e filtradas das bases para uso no dashboard."""
    os.makedirs(pasta_csv, exist_ok=True)

    # Evasão regional 2020-2024
    df_reg[df_reg["ANO_FLUXO"].isin(ANOS_FOCO)].to_csv(
        os.path.join(pasta_csv, "evasao_regiao_2020_2024.csv"),
        index=False, sep=";", encoding="utf-8-sig"
    )

    # Evasão UF 2020-2024
    df_uf[df_uf["ANO_FLUXO"].isin(ANOS_FOCO)].to_csv(
        os.path.join(pasta_csv, "evasao_uf_2020_2024.csv"),
        index=False, sep=";", encoding="utf-8-sig"
    )

    # Trajetória PB - cursos TI
    df_pb_ti = filtrar_area_tecnologia(df_traj)
    df_pb_ti = df_pb_ti[df_pb_ti["CO_UF"] == CO_UF_PB]
    df_pb_ti.to_csv(
        os.path.join(pasta_csv, "trajetoria_ti_pb_2020_2024.csv"),
        index=False, sep=";", encoding="utf-8-sig"
    )

    # Trajetória Rio Tinto especificamente
    df_traj[df_traj["CO_MUNICIPIO"] == CO_MUNICIPIO_RIO_TINTO].to_csv(
        os.path.join(pasta_csv, "trajetoria_riotinto_2020_2024.csv"),
        index=False, sep=";", encoding="utf-8-sig"
    )

    print(f"  [→] CSVs limpos exportados para '{pasta_csv}'")


# ==============================================================================
# FLUXO PRINCIPAL
# ==============================================================================

def main():
    print("=" * 65)
    print(" TCC — ANÁLISE DE EVASÃO EM CURSOS DE TECNOLOGIA (2020–2024)")
    print("=" * 65)

    os.makedirs(PASTA_SAIDA, exist_ok=True)

    print("\n[1/3] CARREGANDO BASES DE DADOS...")
    df_reg = carregar_regiao()
    df_uf = carregar_uf()
    df_traj = carregar_trajetoria()

    print(f"\n  Resumo dos dados carregados:")
    print(f"    Regiões: {len(df_reg)} registros ({df_reg['REGIAO'].nunique()} regiões)")
    print(f"    UFs:     {len(df_uf)} registros ({df_uf['UF'].nunique()} estados)")
    print(f"    Traj.:   {len(df_traj)} registros de cursos (coorte 2020)")

    # Verificar dados de Rio Tinto
    rt_check = df_traj[df_traj["CO_MUNICIPIO"] == CO_MUNICIPIO_RIO_TINTO]
    print(f"    Rio Tinto: {len(rt_check)} registros de cursos encontrados")

    print("\n[2/3] GERANDO GRÁFICOS...")
    grafico1_serie_temporal_regioes(df_reg, PASTA_SAIDA)
    grafico2_ranking_regioes_2024(df_reg, PASTA_SAIDA)
    grafico3_paraiba_vs_nordeste(df_uf, PASTA_SAIDA)
    grafico4_drilldown_brasil_pb_riotinto(df_reg, df_uf, df_traj, PASTA_SAIDA)
    grafico5_trajetoria_cursos_riotinto(df_traj, PASTA_SAIDA)
    grafico6_licenciatura_vs_bacharelado_pb(df_traj, PASTA_SAIDA)

    print("\n[3/3] EXPORTANDO CSVs LIMPOS...")
    exportar_csvs(df_reg, df_uf, df_traj, PASTA_CSV_SAIDA)

    print("\n" + "=" * 65)
    print(" ANÁLISE CONCLUÍDA! 6 gráficos gerados em:")
    print(f"  {PASTA_SAIDA}")
    print("=" * 65)


if __name__ == "__main__":
    main()
