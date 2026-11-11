"""
Pipeline de extração dos Microdados do Censo da Educação Superior (2020–2024)
para os cursos de TI do Campus IV da UFPB (Rio Tinto).

Produz dois CSVs processados:
  - dados/processados/perfil_riotinto_censo_anual.csv
  - dados/processados/perfil_riotinto_todas_ies_ti.csv (cursos de TI da PB para comparação)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import pandas as pd

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_SAIDA = os.path.join(PASTA_PROJETO, "dados", "processados")

# Código dos cursos alvo
CODIGO_CC = 98984   # Licenciatura em Ciência da Computação (UFPB Rio Tinto)
CODIGO_SI = 107360  # Sistemas de Informação - Bacharelado (UFPB Rio Tinto)

CENSO_FILES = {
    2020: os.path.join(PASTA_PROJETO, "microdados_censo_2020", "dados", "MICRODADOS_CADASTRO_CURSOS_2020.CSV"),
    2021: os.path.join(PASTA_PROJETO, "microdados_censo_2021", "dados", "MICRODADOS_CADASTRO_CURSOS_2021.CSV"),
    2022: os.path.join(PASTA_PROJETO, "microdados_censo_2022", "dados", "MICRODADOS_CADASTRO_CURSOS_2022.CSV"),
    2023: os.path.join(PASTA_PROJETO, "microdados_censo_da_educacao_superior_2023", "dados", "MICRODADOS_CADASTRO_CURSOS_2023.CSV"),
    2024: os.path.join(PASTA_PROJETO, "microdados_censo_da_educacao_superior_2024", "dados", "MICRODADOS_CADASTRO_CURSOS_2024.CSV"),
}

# Colunas de interesse (comuns a 2020–2024)
COLS_INTERESSE = [
    "NU_ANO_CENSO", "CO_CURSO", "NO_CURSO",
    # Totais
    "QT_ING", "QT_ING_FEM", "QT_ING_MASC",
    "QT_MAT", "QT_MAT_FEM", "QT_MAT_MASC",
    "QT_CONC", "QT_CONC_FEM", "QT_CONC_MASC",
    # Faixa etária (ingressantes)
    "QT_ING_0_17", "QT_ING_18_24", "QT_ING_25_29",
    "QT_ING_30_34", "QT_ING_35_39", "QT_ING_40_49",
    "QT_ING_50_59", "QT_ING_60_MAIS",
    # Faixa etária (matriculados)
    "QT_MAT_18_24", "QT_MAT_25_29", "QT_MAT_30_34",
    # Faixa etária (concluintes)
    "QT_CONC_18_24", "QT_CONC_25_29", "QT_CONC_30_34",
    # Escola de origem
    "QT_ING_PROCESCPUBLICA", "QT_ING_PROCESCPRIVADA",
    "QT_MAT_PROCESCPUBLICA", "QT_MAT_PROCESCPRIVADA",
    "QT_CONC_PROCESCPUBLICA", "QT_CONC_PROCESCPRIVADA",
    # Raça/Cor
    "QT_ING_BRANCA", "QT_ING_PRETA", "QT_ING_PARDA", "QT_ING_INDIGENA", "QT_ING_AMARELA",
    "QT_MAT_BRANCA", "QT_MAT_PRETA", "QT_MAT_PARDA", "QT_MAT_INDIGENA", "QT_MAT_AMARELA",
    "QT_CONC_BRANCA", "QT_CONC_PRETA", "QT_CONC_PARDA", "QT_CONC_INDIGENA",
    # Cotas e reservas de vagas
    "QT_ING_RESERVA_VAGA", "QT_ING_RVREDEPUBLICA", "QT_ING_RVSOCIAL_RF",
    "QT_MAT_RESERVA_VAGA", "QT_MAT_RVREDEPUBLICA", "QT_MAT_RVSOCIAL_RF",
    "QT_CONC_RESERVA_VAGA", "QT_CONC_RVREDEPUBLICA", "QT_CONC_RVSOCIAL_RF",
    # Apoio social / Auxílios estudantis
    "QT_APOIO_SOCIAL", "QT_ING_APOIO_SOCIAL", "QT_MAT_APOIO_SOCIAL", "QT_CONC_APOIO_SOCIAL",
    # Atividades extracurriculares
    "QT_ATIV_EXTRACURRICULAR", "QT_ING_ATIV_EXTRACURRICULAR",
    "QT_MAT_ATIV_EXTRACURRICULAR", "QT_CONC_ATIV_EXTRACURRICULAR",
    # Desligamentos
    "QT_SIT_TRANCADA", "QT_SIT_DESVINCULADO", "QT_SIT_TRANSFERIDO", "QT_SIT_FALECIDO",
    # Alunos com deficiência
    "QT_ING_DEFICIENTE", "QT_MAT_DEFICIENTE", "QT_CONC_DEFICIENTE",
    # Forma de ingresso
    "QT_ING_ENEM", "QT_ING_VESTIBULAR",
    # Turno
    "QT_ING_DIURNO", "QT_ING_NOTURNO", "QT_MAT_DIURNO", "QT_MAT_NOTURNO",
    "QT_CONC_DIURNO", "QT_CONC_NOTURNO",
]

# Colunas que só existem a partir de 2024
COLS_APENAS_2024 = [
    "QT_ING_RVPPI", "QT_MAT_RVPPI", "QT_CONC_RVPPI",
]


def extrair_cursos_riotinto(ano: int, path: str) -> pd.DataFrame:
    """Lê o microdado de um ano e filtra apenas os 2 cursos de Rio Tinto."""
    print(f"  [{ano}] Processando {os.path.basename(path)} ...", flush=True)

    # Leitura em chunks por ser arquivo grande
    chunks = pd.read_csv(
        path, sep=";", encoding="latin1", low_memory=False,
        chunksize=50_000
    )
    rows = [
        chunk[chunk["CO_CURSO"].isin([CODIGO_CC, CODIGO_SI])]
        for chunk in chunks
    ]
    df = pd.concat([r for r in rows if not r.empty])

    if df.empty:
        print(f"  [{ano}] AVISO: Nenhum registro encontrado!")
        return pd.DataFrame()

    # Selecionar apenas colunas de interesse que existem no arquivo
    cols_disponiveis = [c for c in COLS_INTERESSE if c in df.columns]
    df = df[cols_disponiveis].copy()

    # Adicionar colunas ausentes como NaN (compatibilidade entre anos)
    for col in COLS_INTERESSE:
        if col not in df.columns:
            df[col] = 0

    df["NU_ANO_CENSO"] = ano
    df = df.fillna(0)

    print(f"  [{ano}] {len(df)} cursos encontrados: {list(df['NO_CURSO'].values)}")
    return df


def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    frames = []

    for ano, path in CENSO_FILES.items():
        if not os.path.exists(path):
            print(f"  [{ano}] ARQUIVO NAO ENCONTRADO: {path}")
            continue
        df = extrair_cursos_riotinto(ano, path)
        if not df.empty:
            frames.append(df)

    if not frames:
        print("ERRO: Nenhum dado extraído!")
        return

    df_final = pd.concat(frames, ignore_index=True)
    df_final = df_final.astype({c: "int64" for c in df_final.select_dtypes("float").columns
                                 if c not in ["NU_ANO_CENSO"]}, errors="ignore")

    output_path = os.path.join(PASTA_SAIDA, "perfil_censal_riotinto_2020_2024.csv")
    df_final.to_csv(output_path, sep=";", index=False, encoding="utf-8")

    print(f"\nSalvo: {output_path}")
    print(f"Shape final: {df_final.shape}")
    print(f"\nAnos disponíveis: {sorted(df_final['NU_ANO_CENSO'].unique())}")
    print(f"Cursos: {df_final['NO_CURSO'].unique()}")
    print("\nAmostra final:")
    print(df_final[["NU_ANO_CENSO", "NO_CURSO", "QT_ING", "QT_MAT", "QT_CONC",
                     "QT_SIT_TRANCADA", "QT_SIT_DESVINCULADO",
                     "QT_MAT_APOIO_SOCIAL", "QT_MAT_ATIV_EXTRACURRICULAR"]].to_string(index=False))


if __name__ == "__main__":
    main()
