"""
=============================================================================
TCC -- PIPELINE DE QUALIDADE DE DADOS & SANITY CHECK
=============================================================================
Execute com:
    python audit_pipeline.py

Blocos de verificacao:
  1. Integridade dos arquivos-fonte (existencia, hash MD5, tamanho)
  2. Leitura do Excel de Regioes  (skiprows, colunas, ffill, completude)
  3. Leitura do Excel de UFs      (skiprows, colunas, ffill, Paraiba)
  4. Parsing do CSV de Trajetoria (encoding, separador, linhas descartadas)
  5. Conformidade com dicionario de dados INEP (tipos, dominios fixos)
  6. Sanity checks estatisticos   (TAP+TCA+TDA<=100, TDA monotona, TADA<=TDA)
  7. Validacao dos filtros do dashboard (CO_MUNICIPIO, CO_CURSO, CO_UF)
  8. Cross-check entre bases      (consistencia temporal, plausibilidade)
  9. Snapshot dos valores exatos usados nos graficos (para conferencia manual)
 10. Analise de risco do ffill nos Excels mesclados
=============================================================================
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import hashlib
import warnings
from datetime import datetime

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# ==============================================================================
# CONSTANTES (DINÂMICAS E PORTÁVEIS)
# ==============================================================================
DIRETORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_PROJETO    = os.path.dirname(DIRETORIO_SCRIPT)
PASTA_DADOS      = os.path.join(PASTA_PROJETO, "dados", "brutos")
PASTA_RELATORIOS = os.path.join(PASTA_PROJETO, "relatorios")
ARQ_REGIAO_XLSX  = os.path.join(PASTA_DADOS, "regiao", "INDIC_REGIAO_2010_2024.xlsx")
ARQ_UF_XLSX      = os.path.join(PASTA_DADOS, "uf",     "INDIC_UF_2010_2024.xlsx")
ARQ_TRAJ         = os.path.join(PASTA_DADOS, "INDICADORES_TRAJETORIA.csv")
MD5_REGIAO       = os.path.join(PASTA_DADOS, "regiao", "md5_INDIC_REGIAO_2010_2024.txt")
MD5_UF           = os.path.join(PASTA_DADOS, "uf",     "md5_INDIC_UF_2010_2024.txt")

CO_MUNICIPIO_RIO_TINTO = 2512903
CO_UF_PB               = 25
CO_CURSO_LIC_CC        = 98984
CO_CURSO_SI            = 107360
ANOS_FOCO  = ["2020-2021", "2021-2022", "2022-2023", "2023-2024"]
NORDESTE   = ["Alagoas", "Bahia", "Cear\u00e1", "Maranh\u00e3o", "Para\u00edba",
              "Pernambuco", "Piau\u00ed", "Rio Grande do Norte", "Sergipe"]
REGIOES    = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

DOMINIOS = {
    "CO_REGIAO":                   {1,2,3,4,5},
    "TP_CATEGORIA_ADMINISTRATIVA": {1,2,3,4,5,7},
    "TP_ORGANIZACAO_ACADEMICA":    {1,2,3,4,5},
    "TP_GRAU_ACADEMICO":           {1,2,3},
    "TP_MODALIDADE_ENSINO":        {1,2},
}
ANOS_REF_OK = [2020,2021,2022,2023,2024]
COLUNAS_TRAJ = [
    "CO_IES","NO_IES","TP_CATEGORIA_ADMINISTRATIVA","TP_ORGANIZACAO_ACADEMICA",
    "CO_CURSO","NO_CURSO","CO_REGIAO","CO_UF","CO_MUNICIPIO",
    "TP_GRAU_ACADEMICO","TP_MODALIDADE_ENSINO",
    "CO_CINE_ROTULO","NO_CINE_ROTULO","CO_CINE_AREA_GERAL","NO_CINE_AREA_GERAL",
    "NU_ANO_INGRESSO","NU_ANO_REFERENCIA","NU_PRAZO_INTEGRALIZACAO",
    "NU_ANO_INTEGRALIZACAO","NU_PRAZO_ACOMPANHAMENTO","NU_ANO_MAXIMO_ACOMPANHAMENTO",
    "QT_INGRESSANTE","QT_PERMANENCIA","QT_CONCLUINTE","QT_DESISTENCIA","QT_FALECIDO",
    "TAP","TCA","TDA","TCAN","TADA",
]

# ==============================================================================
# RELATORIO
# ==============================================================================
class AuditReport:
    PASS, WARN, FAIL = "OK  ", "WARN", "FAIL"

    def __init__(self):
        self._items = []
        self._section = ""
        self._n = 0

    def section(self, title):
        self._n += 1
        self._section = title
        print(f"\n{'─'*70}")
        print(f"  BLOCO {self._n}: {title}")
        print(f"{'─'*70}")

    def add(self, status, check, detail="", value=None):
        self._items.append(dict(section=self._section, status=status,
                                check=check, detail=detail, value=value))
        icon = {"OK  ":"✅","WARN":"⚠️ ","FAIL":"❌"}.get(status,"?")
        vs   = f"  =>  {value}" if value is not None else ""
        ds   = f"\n          {detail}" if detail else ""
        print(f"  {icon} [{status}]  {check}{vs}{ds}")

    def summary(self):
        total  = len(self._items)
        passed = sum(1 for i in self._items if i["status"]==self.PASS)
        warned = sum(1 for i in self._items if i["status"]==self.WARN)
        failed = sum(1 for i in self._items if i["status"]==self.FAIL)
        print(f"\n{'='*70}")
        print(f"  RESUMO  —  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"  Total verificacoes : {total}")
        print(f"  ✅ PASS            : {passed}")
        print(f"  ⚠️  WARN            : {warned}")
        print(f"  ❌ FAIL            : {failed}")
        print(f"{'='*70}")
        if failed:
            print(f"\n  ⛔  {failed} verificacao(oes) critica(s):")
            for i in self._items:
                if i["status"]==self.FAIL:
                    print(f"     • [{i['section']}] {i['check']}")
                    if i["detail"]: print(f"       {i['detail']}")
        if warned:
            print(f"\n  ⚠️   {warned} aviso(s) para atencao manual:")
            for i in self._items:
                if i["status"]==self.WARN:
                    print(f"     • [{i['section']}] {i['check']}")
                    if i["detail"]: print(f"       {i['detail']}")
        if not failed and not warned:
            print("\n  🎉  Todos os dados passaram! Base confiavel para o TCC.")
        return failed, warned

    def save(self, path):
        rows = [{"Secao":i["section"],"Status":i["status"].strip(),
                 "Verificacao":i["check"],"Detalhe":i["detail"],
                 "Valor":str(i["value"]) if i["value"] is not None else ""}
                for i in self._items]
        pd.DataFrame(rows).to_csv(path,index=False,sep=";",encoding="utf-8-sig")
        print(f"\n  📄 Relatorio CSV salvo em: {path}")


audit = AuditReport()

# ==============================================================================
# B1 — INTEGRIDADE DOS ARQUIVOS
# ==============================================================================
def _md5(path):
    h = hashlib.md5()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _md5_ref(path):
    if not os.path.exists(path): return None
    txt = open(path,"r",encoding="utf-8",errors="ignore").read().strip()
    for t in txt.split():
        if len(t)==32 and all(c in "0123456789abcdefABCDEF" for c in t):
            return t.lower()
    return None

def bloco1():
    audit.section("INTEGRIDADE DOS ARQUIVOS-FONTE")
    arqs = {
        "INDIC_REGIAO_2010_2024.xlsx": (ARQ_REGIAO_XLSX, MD5_REGIAO, 0.01),
        "INDIC_UF_2010_2024.xlsx":     (ARQ_UF_XLSX,     MD5_UF,     0.05),
        "INDICADORES_TRAJETORIA.csv":  (ARQ_TRAJ,         None,       10.0),
    }
    for nome,(caminho,md5p,min_mb) in arqs.items():
        if not os.path.exists(caminho):
            audit.add(audit.FAIL,f"Existe: {nome}",f"Nao encontrado: {caminho}"); continue
        mb = os.path.getsize(caminho)/(1024*1024)
        audit.add(audit.PASS,f"Existe: {nome}",value=f"{mb:.2f} MB")
        audit.add(audit.PASS if mb>=min_mb else audit.FAIL,
                  f"Tamanho razoavel: {nome}",
                  detail=f"Arquivo pequeno demais ({mb:.2f} MB < {min_mb} MB)" if mb<min_mb else "",
                  value=f"{mb:.2f} MB")
        if md5p:
            ref = _md5_ref(md5p)
            if ref:
                atual = _md5(caminho)
                audit.add(audit.PASS if atual==ref else audit.FAIL,
                          f"MD5 integro: {nome}",
                          detail="" if atual==ref else f"Esperado {ref[:12]}... | Atual {atual[:12]}...",
                          value=atual[:12]+"...")
            else:
                audit.add(audit.WARN,f"MD5 verificavel: {nome}","Hash nao extraido do .txt")
        else:
            audit.add(audit.WARN,f"MD5 verificavel: {nome}","Sem arquivo de referencia MD5")

# ==============================================================================
# B2 — EXCEL REGIOES
# ==============================================================================
def bloco2():
    audit.section("EXCEL DE REGIOES (TX_EVASAO)")
    if not os.path.exists(ARQ_REGIAO_XLSX):
        audit.add(audit.FAIL,"Arquivo acessivel","Nao encontrado"); return None
    xl = pd.ExcelFile(ARQ_REGIAO_XLSX)
    tem = "TX_EVASAO" in xl.sheet_names
    audit.add(audit.PASS if tem else audit.FAIL,"Aba TX_EVASAO existe",value=str(xl.sheet_names))
    if not tem: return None

    # Detectar skiprows
    drf = xl.parse("TX_EVASAO",header=None)
    skip_det = None
    for idx,row in drf.iterrows():
        vals=[str(v) for v in row if pd.notna(v) and str(v).strip()]
        if any(r in v for r in REGIOES for v in vals): skip_det=idx; break
    audit.add(audit.PASS if skip_det==8 else audit.WARN,
              "skiprows=8 verificado",
              detail=f"Auto-detectado linha {skip_det}, codigo usa 8" if skip_det!=8 else "",
              value=f"Dados iniciam na linha {skip_det}")

    dr=xl.parse("TX_EVASAO",header=None,skiprows=8)
    df=dr.iloc[:,:5].copy()
    df.columns=["ANO_FLUXO","REGIAO","TOTAL","FEMININO","MASCULINO"]
    nulos=df["ANO_FLUXO"].isna().sum()
    audit.add(audit.PASS if nulos>0 else audit.WARN,
              "ANO_FLUXO tem NaN antes do ffill (padrao de Excel mesclado)",
              value=f"{nulos} nulos serao preenchidos")
    df["ANO_FLUXO"]=df["ANO_FLUXO"].ffill()
    df=df[df["REGIAO"].notna()].copy()
    df=df[~df["REGIAO"].astype(str).str.startswith(("Fonte","Nota"))].copy()
    df=df[df["REGIAO"].astype(str).str.strip()!=""].copy()
    for c in ["TOTAL","FEMININO","MASCULINO"]:
        df[c]=pd.to_numeric(df[c],errors="coerce")
    df["REGIAO"]=df["REGIAO"].astype(str).str.strip()
    df["ANO_FLUXO"]=df["ANO_FLUXO"].astype(str).str.strip()
    df=df.dropna(subset=["TOTAL"])

    enc=set(df["REGIAO"].unique()); esp=set(REGIOES)
    falt=esp-enc; ext=enc-esp
    audit.add(audit.PASS if not falt else audit.FAIL,"5 regioes presentes",
              detail=str(falt) if falt else "",value=sorted(enc))
    if ext: audit.add(audit.WARN,"Regioes extras (lixo parsing?)",value=sorted(ext))
    falt_a=set(ANOS_FOCO)-set(df["ANO_FLUXO"].unique())
    audit.add(audit.PASS if not falt_a else audit.FAIL,"4 periodos 2020-2024 presentes",
              detail=str(falt_a) if falt_a else "",value=sorted(ANOS_FOCO))
    mn,mx=df["TOTAL"].min(),df["TOTAL"].max()
    audit.add(audit.PASS if 0<=mn and mx<=100 else audit.FAIL,
              "Taxas em [0%, 100%]",value=f"min={mn:.1f}%, max={mx:.1f}%")
    df2=df[df["ANO_FLUXO"].isin(ANOS_FOCO)].copy()
    df2["SG"]=df2["FEMININO"]+df2["MASCULINO"]
    df2["D"]=(df2["SG"]-df2["TOTAL"]).abs()
    erros=df2[df2["D"]>0.5]
    audit.add(audit.PASS if erros.empty else audit.WARN,
              "FEMININO+MASCULINO aprox TOTAL (tol 0.5 p.p.)",
              detail="" if erros.empty else erros[["ANO_FLUXO","REGIAO","TOTAL","SG","D"]].to_string(index=False))
    ne=len(REGIOES)*len(ANOS_FOCO); nr=len(df2)
    audit.add(audit.PASS if nr==ne else audit.WARN,
              f"Completude: {nr}/{ne} registros no periodo focal")
    return df

# ==============================================================================
# B3 — EXCEL UFs
# ==============================================================================
def bloco3():
    audit.section("EXCEL DE UFs / ESTADOS (TX_EVASAO)")
    if not os.path.exists(ARQ_UF_XLSX):
        audit.add(audit.FAIL,"Arquivo acessivel","Nao encontrado"); return None
    xl=pd.ExcelFile(ARQ_UF_XLSX)
    tem="TX_EVASAO" in xl.sheet_names
    audit.add(audit.PASS if tem else audit.FAIL,"Aba TX_EVASAO existe",value=str(xl.sheet_names))
    if not tem: return None
    dr=xl.parse("TX_EVASAO",header=None,skiprows=8)
    df=dr.iloc[:,:7].copy()
    df.columns=["ANO_FLUXO","UF","TOTAL","FEMININO","MASCULINO","PPI_SIM","PPI_NAO"]
    df=df[df["UF"].notna()].copy()
    df=df[~df["UF"].astype(str).str.startswith(("Fonte","Nota"))].copy()
    df["ANO_FLUXO"]=df["ANO_FLUXO"].ffill()
    df=df[df["UF"].astype(str).str.strip()!=""].copy()
    for c in ["TOTAL","FEMININO","MASCULINO","PPI_SIM","PPI_NAO"]:
        df[c]=pd.to_numeric(df[c],errors="coerce")
    df["UF"]=df["UF"].astype(str).str.strip()
    df["ANO_FLUXO"]=df["ANO_FLUXO"].astype(str).str.strip()
    df=df.dropna(subset=["TOTAL"])
    nu=df["UF"].nunique()
    audit.add(audit.PASS if nu>=27 else audit.WARN,f"27 UFs presentes",value=f"{nu} UFs")
    ufs=set(df["UF"].unique())
    ne_falt=set(NORDESTE)-ufs
    audit.add(audit.PASS if not ne_falt else audit.FAIL,"9 estados Nordeste presentes",
              detail=str(ne_falt) if ne_falt else "")
    pb_k="Para\u00edba" if "Para\u00edba" in ufs else "Paraiba"
    pbr=df[(df["UF"]==pb_k)&(df["ANO_FLUXO"].isin(ANOS_FOCO))]
    audit.add(audit.PASS if len(pbr)==4 else audit.FAIL,
              "Paraiba: 4 periodos completos",
              value=pbr[["ANO_FLUXO","TOTAL"]].set_index("ANO_FLUXO")["TOTAL"].to_dict() if not pbr.empty else "vazio")
    if not pbr.empty:
        v=pbr["TOTAL"].values
        audit.add(audit.PASS if all(0<x<100 for x in v) else audit.FAIL,
                  "Taxa evasao PB em [0%, 100%]",value=v.tolist())
    df2=df[df["ANO_FLUXO"].isin(ANOS_FOCO)].copy()
    df2["SP"]=df2["PPI_SIM"].fillna(0)+df2["PPI_NAO"].fillna(0)
    df2["D"]=(df2["SP"]-df2["TOTAL"]).abs()
    ep=df2[(df2["D"]>1.0)&(df2["SP"]>0)]
    audit.add(audit.PASS if ep.empty else audit.WARN,
              "PPI_SIM+PPI_NAO aprox TOTAL (tol 1 p.p.)",
              detail=f"{len(ep)} discrepancias" if not ep.empty else "")
    return df

# ==============================================================================
# B4 — CSV TRAJETORIA
# ==============================================================================
def bloco4():
    audit.section("CSV DE INDICADORES DE TRAJETORIA")
    if not os.path.exists(ARQ_TRAJ):
        audit.add(audit.FAIL,"Arquivo acessivel",f"Nao encontrado: {ARQ_TRAJ}"); return None
    print("  [->] Contando linhas do CSV (pode demorar)...")
    total=sum(1 for _ in open(ARQ_TRAJ,"rb"))
    audit.add(audit.PASS,"Contagem de linhas brutas",value=f"{total:,} linhas")
    primeiras=open(ARQ_TRAJ,"rb").read(2048)
    tem_bom=primeiras[:3]==b"\xef\xbb\xbf"
    audit.add(audit.PASS if not tem_bom else audit.WARN,"Encoding: sem BOM UTF-8 (esperado latin1)",
              value="BOM presente — conflito potencial" if tem_bom else "Sem BOM, ok")
    l0=primeiras.decode("latin1",errors="replace").split("\n")[0]
    npv=l0.count(";"); nvc=l0.count(",")
    audit.add(audit.PASS if npv>nvc else audit.FAIL,"Separador ; dominante",
              value=f"{npv} ; vs {nvc} ,")
    print("  [->] Carregando CSV com on_bad_lines='skip' (identico ao dashboard)...")
    df_skip=pd.read_csv(ARQ_TRAJ,sep=";",encoding="latin1",header=None,
                        skiprows=9,engine="python",names=COLUNAS_TRAJ,on_bad_lines="skip")
    print("  [->] Contando linhas com campos incorretos...")
    ne=len(COLUNAS_TRAJ); bad=0; good=0
    with open(ARQ_TRAJ,"r",encoding="latin1",errors="replace") as f:
        for i,ln in enumerate(f):
            if i<9: continue
            campos=ln.rstrip("\n\r").split(";")
            if len(campos)==ne: good+=1
            else: bad+=1
    pct=bad/max(good+bad,1)*100
    audit.add(audit.PASS if pct<0.1 else (audit.WARN if pct<1.0 else audit.FAIL),
              "Linhas descartadas por on_bad_lines",
              detail=f"{bad} linhas ({pct:.2f}%) — verifique se sao rodapes" if bad else "",
              value=f"{bad} linhas ({pct:.3f}%)")
    audit.add(audit.PASS if df_skip.shape[1]==ne else audit.FAIL,
              "Numero de colunas correto",value=f"{df_skip.shape[1]} colunas")
    return df_skip

# ==============================================================================
# B5 — DICIONARIO DE DADOS INEP
# ==============================================================================
def _conv(df):
    df=df.copy()
    for c in ["CO_IES","CO_UF","CO_MUNICIPIO","CO_CURSO","TP_GRAU_ACADEMICO",
              "TP_CATEGORIA_ADMINISTRATIVA","TP_ORGANIZACAO_ACADEMICA",
              "TP_MODALIDADE_ENSINO","CO_REGIAO","NU_ANO_REFERENCIA","NU_ANO_INGRESSO",
              "QT_INGRESSANTE","QT_PERMANENCIA","QT_CONCLUINTE","QT_DESISTENCIA",
              "QT_FALECIDO","CO_CINE_AREA_GERAL"]:
        if c in df.columns: df[c]=pd.to_numeric(df[c],errors="coerce")
    for c in ["TAP","TCA","TDA","TCAN","TADA"]:
        if c in df.columns:
            df[c]=df[c].astype(str).str.replace(",",".").str.strip()
            df[c]=pd.to_numeric(df[c],errors="coerce")
    return df.dropna(subset=["CO_IES","CO_UF"]).copy()

def bloco5(df_raw):
    audit.section("CONFORMIDADE COM DICIONARIO DE DADOS INEP")
    df=_conv(df_raw)
    df=df[df["CO_IES"]>0].copy()
    df2020=df[df["NU_ANO_INGRESSO"]==2020].copy()
    audit.add(audit.PASS if len(df2020)>0 else audit.FAIL,
              "Registros coorte 2020 (NU_ANO_INGRESSO=2020)",value=f"{len(df2020):,} registros")
    for campo,dom in DOMINIOS.items():
        if campo not in df2020.columns:
            audit.add(audit.WARN,f"Campo {campo} ausente"); continue
        vals=set(df2020[campo].dropna().astype(int).unique())
        inv=vals-dom
        audit.add(audit.PASS if not inv else audit.FAIL,
                  f"Dominio {campo} correto",
                  detail=f"Invalidos: {inv}" if inv else "",value=sorted(vals))
    anos=set(df2020["NU_ANO_REFERENCIA"].dropna().astype(int).unique())
    falt=set(ANOS_REF_OK)-anos
    audit.add(audit.PASS if not falt else audit.FAIL,
              "NU_ANO_REFERENCIA cobre 2020-2024",
              detail=str(falt) if falt else "",value=sorted(anos))
    neg=df2020[df2020["QT_INGRESSANTE"]<=0]
    audit.add(audit.PASS if neg.empty else audit.FAIL,"QT_INGRESSANTE sempre > 0",
              detail=f"{len(neg)} registros com valor <= 0" if not neg.empty else "")
    dc=df2020[["QT_INGRESSANTE","QT_PERMANENCIA","QT_CONCLUINTE",
               "QT_DESISTENCIA","QT_FALECIDO"]].dropna().copy()
    dc["SOMA"]=dc["QT_PERMANENCIA"]+dc["QT_CONCLUINTE"]+dc["QT_DESISTENCIA"]+dc["QT_FALECIDO"]
    dc["EXC"]=dc["SOMA"]-dc["QT_INGRESSANTE"]
    erros=dc[dc["EXC"]>0.5]
    audit.add(audit.PASS if erros.empty else audit.WARN,
              "Conservacao: QT_PERM+CONC+DESIST+FAL <= QT_INGRESSANTE",
              detail=f"{len(erros)} registros excedem (arredondamento INEP?)" if not erros.empty else "")
    for c in ["TAP","TCA","TDA","TCAN","TADA"]:
        if c not in df2020.columns: continue
        s=df2020[c].dropna()
        fora=s[(s<0)|(s>100)]
        audit.add(audit.PASS if fora.empty else audit.FAIL,
                  f"{c} em [0%, 100%]",
                  detail=f"{len(fora)} registros fora (min={fora.min():.1f}%, max={fora.max():.1f}%)" if not fora.empty else "",
                  value=f"min={s.min():.1f}%, max={s.max():.1f}%, media={s.mean():.1f}%")
    return df2020

# ==============================================================================
# B6 — SANITY CHECKS ESTATISTICOS
# ==============================================================================
def bloco6(df):
    audit.section("SANITY CHECKS ESTATISTICOS (RELACOES ENTRE INDICADORES)")
    TOL=2.0
    dc=df[["QT_INGRESSANTE","QT_PERMANENCIA","QT_CONCLUINTE","QT_DESISTENCIA","TAP","TCA","TDA"]].dropna().copy()
    dc["SOMA"]=dc["TAP"]+dc["TCA"]+dc["TDA"]
    dc["TAP_C"]=dc["QT_PERMANENCIA"]/dc["QT_INGRESSANTE"]*100
    dc["TDA_C"]=dc["QT_DESISTENCIA"]/dc["QT_INGRESSANTE"]*100
    dc["TCA_C"]=dc["QT_CONCLUINTE"]/dc["QT_INGRESSANTE"]*100

    errs=dc[dc["SOMA"]>100+TOL]
    audit.add(audit.PASS if errs.empty else audit.WARN,
              f"TAP+TCA+TDA <= 100% (tol {TOL} p.p.)",
              detail=f"{len(errs)} registros excedem (max={errs['SOMA'].max():.1f}%)" if not errs.empty else "",
              value=f"Media da soma: {dc['SOMA'].mean():.1f}%")

    for lbl,col_d,col_c in [("TAP","TAP","TAP_C"),("TDA","TDA","TDA_C"),("TCA","TCA","TCA_C")]:
        dc[f"D_{lbl}"]=(dc[col_d]-dc[col_c]).abs()
        gr=dc[dc[f"D_{lbl}"]>TOL]
        pct=len(gr)/max(len(dc),1)*100
        audit.add(audit.PASS if pct<1.0 else audit.WARN,
                  f"{lbl} declarado aprox {lbl} calculado por QT (tol {TOL} p.p.)",
                  detail=f"{pct:.1f}% dos registros divergem (verifique separador decimal)" if pct>=1 else "",
                  value=f"Divergencia > {TOL}p.p. em {pct:.2f}% dos registros")

    print("  [->] Verificando monotonicidade de TDA acumulada por curso...")
    dord=df.sort_values(["CO_CURSO","NU_ANO_REFERENCIA"]).copy()
    dord["TDA_PREV"]=dord.groupby("CO_CURSO")["TDA"].shift(1)
    dord["DELTA"]=dord["TDA"]-dord["TDA_PREV"]
    reg=dord[(dord["DELTA"]<-TOL)&dord["TDA_PREV"].notna()]
    pct=len(reg)/max(len(dord),1)*100
    audit.add(audit.PASS if pct<0.5 else audit.WARN,
              "TDA acumulada: monotonicamente nao-decrescente",
              detail=f"{len(reg)} regressoes ({pct:.1f}%) — pode ser reclassificacao INEP" if pct>=0.5 else "",
              value=f"{len(reg)} regressoes ({pct:.2f}%)")

    dt=df[["TDA","TADA"]].dropna()
    etada=dt[dt["TADA"]>dt["TDA"]+TOL]
    audit.add(audit.PASS if etada.empty else audit.WARN,
              "TADA anual <= TDA acumulada (sempre)",
              detail=f"{len(etada)} registros com TADA > TDA" if not etada.empty else "")

# ==============================================================================
# B7 — FILTROS DO DASHBOARD
# ==============================================================================
def bloco7(df):
    audit.section("VALIDACAO DOS FILTROS DO DASHBOARD")
    drt=df[df["CO_MUNICIPIO"]==CO_MUNICIPIO_RIO_TINTO]
    audit.add(audit.PASS if len(drt)>0 else audit.FAIL,
              f"CO_MUNICIPIO={CO_MUNICIPIO_RIO_TINTO} (Rio Tinto)",value=f"{len(drt)} registros")

    for co,nome in [(CO_CURSO_LIC_CC,"Lic. CC"),(CO_CURSO_SI,"Sist. Info.")]:
        d=df[df["CO_CURSO"]==co]
        anos=sorted(d["NU_ANO_REFERENCIA"].dropna().astype(int).unique().tolist())
        if len(d)>0:
            audit.add(audit.PASS,f"CO_CURSO={co} ({nome}) encontrado",
                      value=f"{len(d)} registros | anos: {anos}")
            ies=d["CO_IES"].dropna().astype(int).unique().tolist()
            audit.add(audit.PASS if 579 in ies else audit.WARN,
                      f"  {nome}: CO_IES=579 (UFPB)",value=f"IES: {ies}")
            uf=d["CO_UF"].dropna().astype(int).unique().tolist()
            audit.add(audit.PASS if CO_UF_PB in uf else audit.FAIL,
                      f"  {nome}: CO_UF={CO_UF_PB} (Paraiba)",value=f"UFs: {uf}")
            mun=d["CO_MUNICIPIO"].dropna().astype(int).unique().tolist()
            audit.add(audit.PASS if CO_MUNICIPIO_RIO_TINTO in mun else audit.FAIL,
                      f"  {nome}: CO_MUNICIPIO={CO_MUNICIPIO_RIO_TINTO}",value=f"Municipios: {mun}")
            ing=sorted(d["QT_INGRESSANTE"].dropna().astype(int).unique().tolist())
            audit.add(audit.PASS if len(ing)==1 else audit.WARN,
                      f"  {nome}: QT_INGRESSANTE constante na coorte",
                      value=str(ing[0]) if len(ing)==1 else f"Variou: {ing}")
        else:
            audit.add(audit.FAIL,f"CO_CURSO={co} ({nome}) NAO encontrado",
                      detail="Verifique o codigo do curso")

    dti=df[(df["CO_CINE_AREA_GERAL"]==6)&(df["TP_GRAU_ACADEMICO"].isin([1,2]))]
    audit.add(audit.PASS if len(dti)>0 else audit.FAIL,
              "Filtro TI (CO_CINE_AREA_GERAL=6 + Grad/Lic)",
              value=f"{len(dti)} registros | {dti['CO_UF'].nunique()} UFs")
    dpb=df[(df["CO_UF"]==CO_UF_PB)&(df["CO_CINE_AREA_GERAL"]==6)]
    audit.add(audit.PASS if len(dpb)>0 else audit.FAIL,
              f"Filtro CO_UF={CO_UF_PB} (Paraiba) + TI",
              value=f"{len(dpb)} registros | {dpb['CO_CURSO'].nunique()} cursos")
    anos_ing=df["NU_ANO_INGRESSO"].dropna().astype(int).unique().tolist()
    audit.add(audit.PASS if set(anos_ing)=={2020} else audit.FAIL,
              "NU_ANO_INGRESSO==2020 (filtro aplicado corretamente)",
              value=f"Anos: {sorted(anos_ing)}")

# ==============================================================================
# B8 — CROSS-CHECK ENTRE BASES
# ==============================================================================
def bloco8(df_reg,df_uf,df_traj):
    audit.section("CROSS-CHECK ENTRE BASES (CONSISTENCIA CRUZADA)")
    for lbl,d in [("REGIAO",df_reg),("UF",df_uf),("TRAJETORIA",df_traj)]:
        audit.add(audit.PASS if d is not None and not d.empty else audit.FAIL,
                  f"Base {lbl} carregada",value=f"{len(d) if d is not None else 0} registros")
    if any(x is None for x in [df_reg,df_uf,df_traj]):
        audit.add(audit.WARN,"Cross-check impossivel: base(s) nao carregada(s)"); return
    for co,nome in [(CO_CURSO_LIC_CC,"Lic. CC"),(CO_CURSO_SI,"SI")]:
        d=df_traj[df_traj["CO_CURSO"]==co].sort_values("NU_ANO_REFERENCIA")
        if len(d)>=2:
            ini=d["TDA"].iloc[0]; fim=d["TDA"].iloc[-1]
            audit.add(audit.PASS if fim>ini else audit.WARN,
                      f"{nome}: TDA cresce de {int(d['NU_ANO_REFERENCIA'].iloc[0])} a {int(d['NU_ANO_REFERENCIA'].iloc[-1])}",
                      value=f"{ini:.1f}% -> {fim:.1f}% ({'cresceu' if fim>ini else 'NAO cresceu!'})")
    ufs=set(df_uf["UF"].unique())
    pb_k="Para\u00edba" if "Para\u00edba" in ufs else "Paraiba"
    pb_uf=df_uf[df_uf["UF"]==pb_k]; pb_tj=df_traj[df_traj["CO_UF"]==CO_UF_PB]
    audit.add(audit.PASS if not pb_uf.empty else audit.FAIL,"Paraiba na base UF",value=f"{len(pb_uf)} registros")
    audit.add(audit.PASS if not pb_tj.empty else audit.FAIL,"Paraiba (CO_UF=25) na base TRAJ",value=f"{len(pb_tj)} cursos")
    ne24=df_reg[(df_reg["REGIAO"]=="Nordeste")&(df_reg["ANO_FLUXO"]=="2023-2024")]
    if not ne24.empty:
        audit.add(audit.PASS,"Taxa evasao NE 2023-2024 (base REGIAO) recuperavel",
                  value=f"{float(ne24['TOTAL'].iloc[0]):.1f}%")
    for co,nome in [(CO_CURSO_LIC_CC,"Lic. CC"),(CO_CURSO_SI,"SI")]:
        d24=df_traj[(df_traj["CO_CURSO"]==co)&(df_traj["NU_ANO_REFERENCIA"]==2024)]
        if not d24.empty:
            tda=float(d24["TDA"].iloc[0]); tap=d24["TAP"].iloc[0]
            tap_s=f"  TAP={float(tap):.1f}%" if pd.notna(tap) else ""
            audit.add(audit.PASS if 0<tda<100 else audit.FAIL,
                      f"{nome}: TDA(2024) plausivel",value=f"TDA={tda:.1f}%{tap_s}")

# ==============================================================================
# B9 — SNAPSHOT DE VALORES DOS GRAFICOS
# ==============================================================================
def bloco9(df_reg,df_uf,df_traj):
    audit.section("SNAPSHOT DE VALORES-CHAVE USADOS NOS GRAFICOS")
    print()
    print("  ┌──────────────────────────────────────────────────────────────────┐")
    print("  │   VALORES NOS GRAFICOS DO DASHBOARD — CONFIRA MANUALMENTE!      │")
    print("  └──────────────────────────────────────────────────────────────────┘")
    if df_reg is not None:
        d=df_reg[df_reg["ANO_FLUXO"]=="2023-2024"].set_index("REGIAO")["TOTAL"]
        print("\n  📊 Grafico 1/2 — Taxa de Evasao por Regiao (2023-2024):")
        for r in REGIOES:
            v=d.get(r,"N/A")
            fl="  <- NORDESTE (destaque)" if r=="Nordeste" else ""
            print(f"     {r:<15}: {v:.1f}%{fl}" if isinstance(v,float) else f"     {r:<15}: {v}")
        audit.add(audit.PASS,"Snapshot Regioes 2023-2024 exibido acima")
    if df_uf is not None:
        ufs=set(df_uf["UF"].unique())
        pb_k="Para\u00edba" if "Para\u00edba" in ufs else "Paraiba"
        dpb=df_uf[(df_uf["UF"]==pb_k)&(df_uf["ANO_FLUXO"].isin(ANOS_FOCO))]
        print("\n  📊 Grafico 3 — Taxa de Evasao Paraiba:")
        for _,row in dpb.sort_values("ANO_FLUXO").iterrows():
            print(f"     {row['ANO_FLUXO']}: Total={row['TOTAL']:.1f}%  Fem={row['FEMININO']:.1f}%  Masc={row['MASCULINO']:.1f}%")
        audit.add(audit.PASS,"Snapshot Paraiba exibido acima")
    if df_traj is not None:
        print("\n  📊 Graficos 5/6 — Trajetoria Cursos Rio Tinto (coorte 2020):")
        hdr=f"{'Ano':<6} {'Ingress.':<10} {'Perman.':<10} {'Concl.':<10} {'Desist.':<10} {'TAP':>6} {'TDA':>6} {'TCA':>6} {'TADA':>6}"
        def si(v):
            try: return int(v)
            except: return "?"
        def sf(v):
            try: return f"{float(v):.1f}"
            except: return "?"
        for co,nome in [(CO_CURSO_LIC_CC,"Lic. CC"),(CO_CURSO_SI,"Sist. Info.")]:
            d=df_traj[df_traj["CO_CURSO"]==co].sort_values("NU_ANO_REFERENCIA")
            print(f"\n     [{nome}]")
            if d.empty:
                print("       NENHUM REGISTRO ENCONTRADO")
                audit.add(audit.FAIL,f"Dados {nome} ausentes na coorte 2020")
            else:
                print(f"     {hdr}")
                for _,row in d.iterrows():
                    print(f"     {si(row['NU_ANO_REFERENCIA']):<6} {si(row['QT_INGRESSANTE']):<10} {si(row['QT_PERMANENCIA']):<10} {si(row['QT_CONCLUINTE']):<10} {si(row['QT_DESISTENCIA']):<10} {sf(row['TAP']):>6} {sf(row['TDA']):>6} {sf(row['TCA']):>6} {sf(row['TADA']):>6}")
                audit.add(audit.PASS,f"Snapshot {nome} exibido acima")
    print()

# ==============================================================================
# B10 — RISCO DO ffill
# ==============================================================================
def bloco10():
    audit.section("ANALISE DE RISCO DO ffill NOS EXCELS")
    for nome,caminho,nreg in [("REGIAO",ARQ_REGIAO_XLSX,5),("UF",ARQ_UF_XLSX,27)]:
        if not os.path.exists(caminho): continue
        xl=pd.ExcelFile(caminho)
        dr=xl.parse("TX_EVASAO",header=None,skiprows=8)
        col=dr.iloc[:,0]
        nulos=col.isna().sum(); tot=len(col); pct=nulos/max(tot,1)*100
        audit.add(audit.PASS if pct<80 else audit.WARN,
                  f"{nome}: celulas mescladas (ffill)",
                  value=f"{nulos}/{tot} ({pct:.1f}%) com ANO_FLUXO nulo antes ffill")
        cf=col.ffill()
        anos_ok=[a for a in ANOS_FOCO if a in [str(v).strip() for v in cf.dropna().unique()]]
        audit.add(audit.PASS if len(anos_ok)==4 else audit.FAIL,
                  f"{nome}: ffill produz os 4 periodos esperados",
                  detail=f"Encontrados {anos_ok}" if len(anos_ok)<4 else "",
                  value=anos_ok)
        dr2=dr.copy(); dr2["ANO"]=cf
        g=dr2.copy(); g["GRP"]=dr2.iloc[:,1].astype(str)
        g=g[g["GRP"].str.strip()!=""]
        g=g[~g["GRP"].str.startswith(("Fonte","Nota","nan"))]
        mx=g.groupby("ANO")["GRP"].nunique().max() if not g.empty else 0
        audit.add(audit.PASS if mx<=nreg else audit.WARN,
                  f"{nome}: sem vazamento ffill entre grupos",
                  detail=f"Max {mx} grupos/ano (esperado <= {nreg})" if mx>nreg else "",
                  value=f"Max {mx} grupos/ano")

# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("="*70)
    print("  TCC — PIPELINE DE QUALIDADE DE DADOS & SANITY CHECK")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*70)
    bloco1()
    df_reg  = bloco2()
    df_uf   = bloco3()
    df_raw  = bloco4()
    df_traj = None
    if df_raw is not None:
        df_traj = bloco5(df_raw)
    if df_traj is not None:
        bloco6(df_traj)
        bloco7(df_traj)
    bloco8(df_reg, df_uf, df_traj)
    bloco9(df_reg, df_uf, df_traj)
    bloco10()
    falhas, _ = audit.summary()
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    audit.save(os.path.join(PASTA_RELATORIOS, "audit_report.csv"))
    sys.exit(0 if falhas==0 else 1)

if __name__ == "__main__":
    main()
