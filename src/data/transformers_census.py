"""
Pure transformation functions for Census microdata (perfil censal longitudinal).

All functions are side-effect-free: they receive DataFrames and return new ones.
Input DataFrames are never mutated.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Column derivation helpers
# ---------------------------------------------------------------------------

def derive_ppi_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives PPI (Preto, Pardo, Indígena) aggregate columns for all moments.

    The official RVPPI column only exists from 2024 onward; for 2020–2023
    we sum the individual race/color counts as a proxy.
    """
    df = df.copy()

    for moment in ("ING", "MAT", "CONC"):
        preta  = f"QT_{moment}_PRETA"
        parda  = f"QT_{moment}_PARDA"
        indigena = f"QT_{moment}_INDIGENA"
        dest   = f"QT_{moment}_PPI"

        if all(c in df.columns for c in [preta, parda, indigena]):
            df[dest] = df[preta] + df[parda] + df[indigena]
        else:
            df[dest] = 0

    return df


def derive_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives key percentage columns from raw counts.

    Adds columns for:
    - % of enrolled students with social support
    - % of graduates with social support
    - % of enrolled students with extracurricular activities
    - % of graduates with extracurricular activities
    - % of cotistas (quota students) among entrants
    - % female among entrants / enrolled / graduates
    - % public school origin among entrants
    """
    df = df.copy()

    def safe_pct(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
        return (numerator / denominator.replace(0, pd.NA) * 100).round(1)

    # Social support rates
    df["PCT_MAT_APOIO_SOCIAL"]  = safe_pct(df["QT_MAT_APOIO_SOCIAL"],  df["QT_MAT"])
    df["PCT_CONC_APOIO_SOCIAL"] = safe_pct(df["QT_CONC_APOIO_SOCIAL"], df["QT_CONC"])

    # Extracurricular activity rates
    df["PCT_MAT_ATIV_EXTRA"]  = safe_pct(df["QT_MAT_ATIV_EXTRACURRICULAR"],  df["QT_MAT"])
    df["PCT_CONC_ATIV_EXTRA"] = safe_pct(df["QT_CONC_ATIV_EXTRACURRICULAR"], df["QT_CONC"])

    # Quota rate among entrants
    df["PCT_ING_COTISTAS"] = safe_pct(df["QT_ING_RESERVA_VAGA"], df["QT_ING"])

    # Gender (female) rates
    df["PCT_ING_FEM"]  = safe_pct(df["QT_ING_FEM"],  df["QT_ING"])
    df["PCT_MAT_FEM"]  = safe_pct(df["QT_MAT_FEM"],  df["QT_MAT"])
    df["PCT_CONC_FEM"] = safe_pct(df["QT_CONC_FEM"], df["QT_CONC"])

    # Public school origin rate
    df["PCT_ING_ESC_PUBLICA"] = safe_pct(df["QT_ING_PROCESCPUBLICA"], df["QT_ING"])

    # PPI rates (derived above)
    if "QT_ING_PPI" in df.columns:
        df["PCT_ING_PPI"] = safe_pct(df["QT_ING_PPI"], df["QT_ING"])
    if "QT_MAT_PPI" in df.columns:
        df["PCT_MAT_PPI"] = safe_pct(df["QT_MAT_PPI"], df["QT_MAT"])
    if "QT_CONC_PPI" in df.columns:
        df["PCT_CONC_PPI"] = safe_pct(df["QT_CONC_PPI"], df["QT_CONC"])

    return df


def compute_age_distribution(df: pd.DataFrame, moment: str) -> pd.DataFrame:
    """
    Returns a tidy DataFrame with age-band distribution for a given moment.

    Parameters
    ----------
    df      : DataFrame with one row per course/year (perfil censal)
    moment  : 'ING', 'MAT' or 'CONC'

    Returns
    -------
    DataFrame with columns: [NU_ANO_CENSO, NO_CURSO, faixa_etaria, quantidade]
    """
    FAIXAS_ING = [
        ("Até 17 anos",  f"QT_{moment}_0_17"),
        ("18–24 anos",   f"QT_{moment}_18_24"),
        ("25–29 anos",   f"QT_{moment}_25_29"),
        ("30–34 anos",   f"QT_{moment}_30_34"),
        ("35–39 anos",   f"QT_{moment}_35_39"),
        ("40–49 anos",   f"QT_{moment}_40_49"),
        ("50–59 anos",   f"QT_{moment}_50_59"),
        ("60+ anos",     f"QT_{moment}_60_MAIS"),
    ]
    FAIXAS_SHORT = [
        ("18–24 anos",  f"QT_{moment}_18_24"),
        ("25–29 anos",  f"QT_{moment}_25_29"),
        ("30–34 anos",  f"QT_{moment}_30_34"),
    ]
    faixas = FAIXAS_ING if moment == "ING" else FAIXAS_SHORT

    rows = []
    for _, record in df.iterrows():
        for label, col in faixas:
            if col in df.columns:
                rows.append({
                    "NU_ANO_CENSO": record["NU_ANO_CENSO"],
                    "NO_CURSO":     record["NO_CURSO"],
                    "faixa_etaria": label,
                    "quantidade":   record.get(col, 0),
                })

    return pd.DataFrame(rows)


def compute_school_origin(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a tidy DataFrame comparing public vs. private school origin
    across ING / MAT / CONC for each course-year.
    """
    rows = []
    for _, record in df.iterrows():
        for moment, label in [("ING", "Ingressantes"), ("MAT", "Matriculados"), ("CONC", "Concluintes")]:
            publica  = record.get(f"QT_{moment}_PROCESCPUBLICA",  0)
            privada  = record.get(f"QT_{moment}_PROCESCPRIVADA",  0)
            rows.append({
                "NU_ANO_CENSO": record["NU_ANO_CENSO"],
                "NO_CURSO":     record["NO_CURSO"],
                "momento":      label,
                "Escola Pública":  publica,
                "Escola Privada":  privada,
            })

    return pd.DataFrame(rows)


def compute_quota_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a tidy DataFrame with quota type counts across ING / MAT / CONC.
    """
    rows = []
    for _, record in df.iterrows():
        base = {
            "NU_ANO_CENSO": record["NU_ANO_CENSO"],
            "NO_CURSO":     record["NO_CURSO"],
        }
        for moment, label in [("ING", "Ingressantes"), ("MAT", "Matriculados"), ("CONC", "Concluintes")]:
            rows.append({
                **base,
                "momento":          label,
                "Total Cotas":      record.get(f"QT_{moment}_RESERVA_VAGA",   0),
                "Esc. Pública":     record.get(f"QT_{moment}_RVREDEPUBLICA",  0),
                "Baixa Renda":      record.get(f"QT_{moment}_RVSOCIAL_RF",    0),
                "PPI":              record.get(f"QT_{moment}_PPI",             0),
            })

    return pd.DataFrame(rows)


def compute_protection_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a tidy DataFrame comparing the % of enrolled vs. graduates who
    received social support and participated in extracurricular activities.

    These are the two 'protective factors' most strongly associated with
    course completion in the dataset.
    """
    rows = []
    for _, record in df.iterrows():
        base = {
            "NU_ANO_CENSO": record["NU_ANO_CENSO"],
            "NO_CURSO":     record["NO_CURSO"],
        }
        rows.append({
            **base,
            "fator":    "Apoio Social",
            "Matriculados": record.get("PCT_MAT_APOIO_SOCIAL",  0),
            "Concluintes":  record.get("PCT_CONC_APOIO_SOCIAL", 0),
        })
        rows.append({
            **base,
            "fator":    "Atividade Extracurricular",
            "Matriculados": record.get("PCT_MAT_ATIV_EXTRA",  0),
            "Concluintes":  record.get("PCT_CONC_ATIV_EXTRA", 0),
        })

    return pd.DataFrame(rows)
