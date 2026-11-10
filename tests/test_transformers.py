"""
Unit tests for transformation and analytics functions.
Compatible with both pytest and python -m unittest.
"""

import unittest
import numpy as np
import pandas as pd

from src.data.transformers import (
    compute_weighted_tda,
    filter_technology_courses,
    get_course_kpis,
)


class TestTransformers(unittest.TestCase):
    """Test suite for analytics transformations."""

    def test_compute_weighted_tda_standard_case(self):
        """Validates weighted calculation of TDA: Sum(TDA * Ingressantes) / Sum(Ingressantes)."""
        data = {
            "NU_ANO_REFERENCIA": [2020, 2020, 2021, 2021],
            "TDA": [10.0, 30.0, 20.0, 40.0],
            "QT_INGRESSANTE": [100, 300, 200, 200],
        }
        df = pd.DataFrame(data)

        result = compute_weighted_tda(df, group_col="NU_ANO_REFERENCIA", level_label="Teste")

        # 2020: (10*100 + 30*300) / (100 + 300) = (1000 + 9000) / 400 = 25.0
        # 2021: (20*200 + 40*200) / (200 + 200) = (4000 + 8000) / 400 = 30.0
        self.assertEqual(len(result), 2)
        self.assertIn("ANO", result.columns)
        self.assertIn("TDA_MEDIA", result.columns)
        self.assertIn("NIVEL", result.columns)

        row_2020 = result.loc[result["ANO"] == 2020].iloc[0]
        row_2021 = result.loc[result["ANO"] == 2021].iloc[0]

        np.testing.assert_almost_equal(row_2020["TDA_MEDIA"], 25.0)
        self.assertEqual(row_2020["NIVEL"], "Teste")

        np.testing.assert_almost_equal(row_2021["TDA_MEDIA"], 30.0)
        self.assertEqual(row_2021["NIVEL"], "Teste")

    def test_compute_weighted_tda_empty_dataframe(self):
        """Ensures empty DataFrames return an empty DataFrame with valid schema."""
        df_empty = pd.DataFrame(columns=["NU_ANO_REFERENCIA", "TDA", "QT_INGRESSANTE"])
        result = compute_weighted_tda(df_empty, level_label="Vazio")

        self.assertTrue(result.empty)
        self.assertEqual(list(result.columns), ["ANO", "TDA_MEDIA", "NIVEL"])

    def test_compute_weighted_tda_zero_ingressantes_safe_division(self):
        """Guarantees zero division edge case returns 0.0 without Inf or NaN."""
        data = {
            "NU_ANO_REFERENCIA": [2022],
            "TDA": [50.0],
            "QT_INGRESSANTE": [0],
        }
        df = pd.DataFrame(data)
        result = compute_weighted_tda(df)

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["TDA_MEDIA"], 0.0)
        self.assertFalse(np.isnan(result.iloc[0]["TDA_MEDIA"]))
        self.assertFalse(np.isinf(result.iloc[0]["TDA_MEDIA"]))

    def test_filter_technology_courses(self):
        """Validates filtering of CINE Area 06 + Licenciatura em Computação (0114C05)."""
        data = {
            "CO_CINE_AREA_GERAL": [6, 1, 1, 3],
            "CO_CINE_ROTULO": ["0613C01", "0114C05", "0114P01", "0311E01"],
            "TP_GRAU_ACADEMICO": [1, 2, 2, 1],  # 1=Bacharelado, 2=Licenciatura
        }
        df = pd.DataFrame(data)
        filtered = filter_technology_courses(df)

        # Expected: row 0 (Area 6) and row 1 (Area 1 with label 0114C05)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(set(filtered["CO_CINE_ROTULO"]), {"0613C01", "0114C05"})

    def test_get_course_kpis(self):
        """Validates KPI extraction for a specific cohort and year."""
        data = {
            "NU_ANO_REFERENCIA": [2020, 2024],
            "QT_INGRESSANTE": [40, 40],
            "TDA": [12.5, 57.5],
            "QT_PERMANENCIA": [35, 17],
        }
        df_course = pd.DataFrame(data)
        kpis = get_course_kpis(df_course, target_year=2024)

        self.assertEqual(kpis["ingressantes"], 40)
        self.assertEqual(kpis["tda"], 57.5)
        self.assertEqual(kpis["permanencia"], 17)


if __name__ == "__main__":
    unittest.main()
