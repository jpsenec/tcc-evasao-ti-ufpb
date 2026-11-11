"""Pure transformation and business logic functions for educational metrics."""

from typing import Dict, Tuple, Any
import numpy as np
import pandas as pd

from src.config import (
    CODE_UF_PB,
    CODE_MUNICIPALITY_RIO_TINTO,
    CODE_COURSE_LIC_CC,
    CODE_COURSE_SI,
    FOCUS_YEARS,
    REGION_CODE_MAP,
)


def filter_technology_courses(df_trajectory: pd.DataFrame) -> pd.DataFrame:
    """Filters STEM/IT courses: CINE Area 06 (ICT) + Licentiate in Computing (0114C05)."""
    is_ict_area = df_trajectory["CO_CINE_AREA_GERAL"] == 6
    is_lic_computing = df_trajectory["CO_CINE_ROTULO"] == "0114C05"
    is_degree_level = df_trajectory["TP_GRAU_ACADEMICO"].isin([1, 2])

    return df_trajectory.loc[(is_ict_area | is_lic_computing) & is_degree_level].copy()


def compute_weighted_tda(
    df: pd.DataFrame,
    group_col: str = "NU_ANO_REFERENCIA",
    level_label: str = "",
) -> pd.DataFrame:
    """
    Vectorized calculation of weighted accumulated dropout rate (TDA).
    Weighting formula: Sum(TDA * Ingressantes) / Sum(Ingressantes).
    """
    if df.empty:
        return pd.DataFrame(columns=["ANO", "TDA_MEDIA", "NIVEL"])

    working_df = df.copy()
    working_df["WEIGHTED_DROPOUT"] = working_df["TDA"] * working_df["QT_INGRESSANTE"]

    aggregated = (
        working_df.groupby(group_col, as_index=False)[["WEIGHTED_DROPOUT", "QT_INGRESSANTE"]]
        .sum()
    )

    aggregated["TDA_MEDIA"] = np.where(
        aggregated["QT_INGRESSANTE"] > 0,
        aggregated["WEIGHTED_DROPOUT"] / aggregated["QT_INGRESSANTE"],
        0.0,
    )

    result = aggregated.rename(columns={group_col: "ANO"})[["ANO", "TDA_MEDIA"]].copy()
    if level_label:
        result["NIVEL"] = level_label

    return result


def build_hierarchical_drilldown(df_trajectory: pd.DataFrame) -> pd.DataFrame:
    """Builds comparative drilldown dataset across Brazil, Paraíba and Rio Tinto."""
    ti_courses = filter_technology_courses(df_trajectory)
    ti_focal = ti_courses[ti_courses["NU_ANO_REFERENCIA"].between(2020, 2024)]

    # Vectorized multi-level aggregation
    brazil_agg = compute_weighted_tda(
        ti_focal,
        level_label="Brasil (Cursos TI)"
    )

    pb_agg = compute_weighted_tda(
        ti_focal.loc[ti_focal["CO_UF"] == CODE_UF_PB],
        level_label="Paraíba (Cursos TI)"
    )

    rt_agg = compute_weighted_tda(
        ti_focal.loc[ti_focal["CO_MUNICIPIO"] == CODE_MUNICIPALITY_RIO_TINTO],
        level_label="Rio Tinto — UFPB"
    )

    return pd.concat([brazil_agg, pb_agg, rt_agg], ignore_index=True)


def get_regional_kpis(df_regional: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """Calculates final rate and delta vs baseline (2020) for each region."""
    kpis: Dict[str, Tuple[float, float]] = {}

    df_indexed = df_regional.set_index(["REGIAO", "ANO_FLUXO"])["TOTAL"]

    for region in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]:
        val_2024 = df_indexed.get((region, "2023-2024"), np.nan)
        val_2020 = df_indexed.get((region, "2020-2021"), np.nan)

        final_rate = float(val_2024) if pd.notna(val_2024) else 0.0
        delta_rate = float(val_2024 - val_2020) if pd.notna(val_2024) and pd.notna(val_2020) else 0.0

        kpis[region] = (final_rate, delta_rate)

    return kpis


def get_course_kpis(df_course: pd.DataFrame, target_year: int = 2024) -> Dict[str, Any]:
    """Extracts summary metrics for a specific degree program cohort."""
    if df_course.empty:
        return {"ingressantes": 0, "tda": 0.0, "permanencia": 0}

    initial_ingressantes = int(df_course["QT_INGRESSANTE"].iloc[0])
    target_row = df_course.loc[df_course["NU_ANO_REFERENCIA"] == target_year]

    if not target_row.empty:
        tda_val = float(target_row["TDA"].iloc[0])
        perm_val = int(target_row["QT_PERMANENCIA"].iloc[0])
    else:
        tda_val = 0.0
        perm_val = 0

    return {
        "ingressantes": initial_ingressantes,
        "tda": tda_val,
        "permanencia": perm_val,
    }


def compute_degree_comparison(
    df_trajectory: pd.DataFrame,
    target_year: int = 2024,
) -> pd.DataFrame:
    """Computes weighted average TDA by academic degree (Bacharelado vs Licenciatura)."""
    pb_it_courses = df_trajectory.loc[
        (df_trajectory["CO_CINE_AREA_GERAL"] == 6)
        & (df_trajectory["TP_GRAU_ACADEMICO"].isin([1, 2]))
        & (df_trajectory["CO_UF"] == CODE_UF_PB)
        & (df_trajectory["NU_ANO_REFERENCIA"] == target_year)
    ].copy()

    pb_it_courses["GRAU"] = pb_it_courses["TP_GRAU_ACADEMICO"].map(
        {1: "Bacharelado", 2: "Licenciatura"}
    )

    return compute_weighted_tda(pb_it_courses, group_col="GRAU").rename(
        columns={"ANO": "GRAU"}
    )


def compute_regional_cycle_ranking(df_regional: pd.DataFrame) -> pd.DataFrame:
    """Computes average transversal dropout rate across all cycle periods (2020-2024)."""
    df_cycle = df_regional.loc[df_regional["ANO_FLUXO"].isin(FOCUS_YEARS)]
    if df_cycle.empty:
        return pd.DataFrame(columns=["REGIAO", "TOTAL"])

    ranking = (
        df_cycle.groupby("REGIAO", as_index=False)["TOTAL"]
        .mean()
        .sort_values("TOTAL", ascending=True)
    )
    return ranking.reset_index(drop=True)


def compute_regional_cohort_tda(
    df_trajectory: pd.DataFrame,
    target_year: int = 2024,
) -> pd.DataFrame:
    """Computes weighted accumulated dropout rate (TDA) for 2020 cohort in IT courses by region."""
    ti_courses = filter_technology_courses(df_trajectory)
    ti_target = ti_courses.loc[ti_courses["NU_ANO_REFERENCIA"] == target_year].copy()

    if ti_target.empty:
        return pd.DataFrame(columns=["REGIAO", "TOTAL"])

    ti_target["REGIAO"] = ti_target["CO_REGIAO"].map(REGION_CODE_MAP)
    ti_target = ti_target.dropna(subset=["REGIAO"]).copy()

    ti_target["WEIGHTED_DROPOUT"] = ti_target["TDA"] * ti_target["QT_INGRESSANTE"]
    aggregated = (
        ti_target.groupby("REGIAO", as_index=False)[["WEIGHTED_DROPOUT", "QT_INGRESSANTE"]]
        .sum()
    )

    aggregated["TOTAL"] = np.where(
        aggregated["QT_INGRESSANTE"] > 0,
        aggregated["WEIGHTED_DROPOUT"] / aggregated["QT_INGRESSANTE"],
        0.0,
    )

    return aggregated.sort_values("TOTAL", ascending=True)[["REGIAO", "TOTAL"]].reset_index(drop=True)


