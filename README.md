# 📉 Análise de Evasão em Cursos de TI (UFPB - Campus IV Rio Tinto)

Este repositório contém a infraestrutura completa de dados, scripts de processamento (ETL), pipelines de auditoria de qualidade e dashboards interativos voltados para a análise de evasão e trajetórias acadêmicas no ensino superior, com foco especial nos cursos de Tecnologia da Informação (TI) da Paraíba e do Campus IV da UFPB (Rio Tinto), no período de 2020 a 2024.

---

## 💻 Os Dashboards do Projeto

O projeto disponibiliza duas interfaces visuais complementares para exploração dos dados:

### 1. Dashboard Web Interativo (`index.html` / `dashboard_interativo.html`)
Painel web moderno, responsivo e autocontido (HTML5, CSS3, JavaScript e Plotly.js). Não necessita de Python ou servidor instalado para funcionar — basta abrir o arquivo no navegador ou acessar via **GitHub Pages**.

*   🌐 **Aba 1: Cenário Nacional** — Série temporal por macrorregiões (2020–2024), ranking consolidado de encerramento do ciclo e linha de referência nacional oficial do Brasil.
*   🌵 **Aba 2: Paraíba vs. Nordeste** — Comparativo temporal da trajetória da Paraíba em relação aos outros 8 estados nordestinos.
*   👥 **Aba 3: Análise de Gênero** — Comparação das taxas de evasão entre o público feminino e masculino nos estados e regiões, revelando maior retenção discente feminina.
*   🎨 **Aba 4: Recorte Étnico-Racial (PPI)** — Comparativo de evasão entre estudantes Pretos, Pardos e Indígenas (PPI) e Não-PPI nos estados do Nordeste, demonstrando o impacto positivo das políticas de assistência e permanência estudantil.
*   🎓 **Aba 5: UFPB Campus Rio Tinto** — Análise longitudinal da Coorte de 2020 para os cursos do campus (Licenciatura em Ciência da Computação e Bacharelado em Sistemas de Informação), com:
    *   **Funil de Retenção:** Acompanhamento anual dos alunos ativos (permanência) a partir dos 93 ingressantes de Computação e 47 de Sistemas de Informação.
    *   **TDA Acumulada vs. TADA Anual:** Evidenciando o pico de desligamentos em 2022 com o retorno às aulas presenciais pós-pandemia.
    *   **Distribuição de Desfecho (2024):** Gráficos de rosca ilustrando concluídos, retidos e evadidos no 5º ano de integralização.
*   📋 **Aba 6: Tabela de Dados** — Consulta tabular interativa com busca textual instantânea, filtros por região e ano, e ordenação por colunas.

### 2. Dashboard Streamlit (`dashboard.py`)
Aplicação analítica em Python com barra lateral de filtros dinâmicos, métricas em tempo real e visualizações interativas com Plotly, ideal para exploração em profundidade e execução em nuvem (Streamlit Community Cloud).

---

## 🛠️ Tecnologias Utilizadas

*   **Linguagem Principal:** Python 3.10+
*   **Manipulação e Limpeza de Dados:** [Pandas](https://pandas.pydata.org/) & [Numpy](https://numpy.org/)
*   **Visualização Interativa:** [Plotly](https://plotly.com/python/) (gráficos HTML) e [Streamlit](https://streamlit.io/) (aplicação web)
*   **Leitura de Relatórios:** `openpyxl` (processamento direto de planilhas do INEP)
*   **Auditoria e Qualidade:** Pipeline automatizado com validação de checksums MD5, consistência matemática ($TAP + TCA + TDA \le 100\%$) e testes de regras censitárias.

---

## 📊 Metodologia e Indicadores Utilizados

O estudo fundamenta-se na diferenciação conceitual de dois indicadores oficiais do INEP/MEC:

### 1. Taxa de Evasão Anual (Indicador Transversal)
*   **O que é:** Métrica instantânea calculada anualmente que estima a evasão global do sistema em um determinado ano letivo.
*   **Uso:** Fornece o panorama macrogeográfico (Nacional, Macrorregiões e Estados/UFs), com recortes adicionais por gênero e raça/cor.

### 2. Taxa de Desistência Acumulada - TDA (Indicador Longitudinal por Coorte)
*   **O que é:** Acompanhamento longitudinal da mesma turma de ingressantes (**Coorte de 2020**) ao longo de 5 anos (2020 a 2024).
*   **Uso:** Análise microinstitucional dos cursos de TI no Campus IV da UFPB (Rio Tinto) e contrastes setoriais com o estado e o país.
*   **Nota sobre Classificação CINE-MEC:** O curso de *Licenciatura em Ciência da Computação* é classificado na área de **Educação (01)** (formação docente), enquanto *Sistemas de Informação* pertence a **Computação e TIC (06)**. O projeto trata essa distinção para que ambos sejam avaliados no escopo de TI do campus.

---

## 🗂️ Estrutura Organizada do Repositório

```text
tcc-evasao-ti-ufpb/
│
├── index.html                      # Dashboard Web Interativo (pronto para GitHub Pages)
├── dashboard_interativo.html       # Cópia standalone do Dashboard Web
├── dashboard.py                    # Entrypoint da Aplicação Web Streamlit
├── requirements.txt                # Dependências Python do ecossistema
├── README.md                       # Documentação técnica do repositório
├── .gitignore                      # Regras de exclusão de arquivos (>100MB e temporários)
│
├── src/                            # Arquitetura modularizada da aplicação Streamlit
│   ├── config.py                   # Configurações globais, paths e tokens visuais
│   ├── data/                       # Ingestão em cache e transformações puras vetorizadas
│   │   ├── loader.py
│   │   └── transformers.py
│   ├── ui/                         # Design system, CSS customizado e builders do Plotly
│   │   ├── styles.py
│   │   ├── components.py
│   │   └── charts.py
│   └── views/                      # Visões isoladas do dashboard (Nacional, PB e Rio Tinto)
│       ├── national.py
│       ├── regional.py
│       └── local.py
│
├── tests/                          # Suíte de testes unitários automatizados
│   └── test_transformers.py        # Testes das transformações e métricas analíticas
│
├── scripts/                        # Pipelines de código Python
│   ├── analise_tcc.py              # Pipeline de ETL, tratamento e geração de gráficos
│   └── audit_pipeline.py           # Pipeline de auditoria e testes de qualidade de dados
│
├── dados/                          # Bases de dados organizadas por estágio
│   ├── brutos/                     # Dados originais do INEP (Trajetória, Regiões, UFs)
│   │   ├── INDICADORES_TRAJETORIA.csv
│   │   ├── regiao/
│   │   └── uf/
│   └── processados/                # Datasets limpos e agregados prontos para análise
│       ├── evasao_regiao_2020_2024.csv
│       ├── evasao_uf_2020_2024.csv
│       ├── trajetoria_riotinto_2020_2024.csv
│       └── trajetoria_ti_pb_2020_2024.csv
│
├── graficos/                       # Gráficos interativos em HTML para o artigo
│   ├── grafico1_serie_temporal_regioes.html
│   ├── grafico2_ranking_regioes_2024.html
│   ├── grafico3_paraiba_vs_nordeste.html
│   ├── grafico4_drilldown_brasil_pb_riotinto.html
│   ├── grafico5_trajetoria_cursos_riotinto.html
│   ├── grafico6_licenciatura_vs_bacharelado_pb.html
│   ├── grafico_extra_genero_nordeste_2024.html
│   └── grafico_extra_ppi_nordeste_2024.html
│
└── relatorios/                     # Relatórios de conformidade e qualidade
    └── audit_report.csv            # Diagnóstico da execução do pipeline de auditoria
```

---

## 🚀 Como Executar o Projeto

### 1. Clonar o Repositório e Instalar Dependências
```bash
git clone https://github.com/jpsenec/tcc-evasao-ti-ufpb.git
cd tcc-evasao-ti-ufpb
pip install -r requirements.txt
```

### 2. Executar a Auditoria de Qualidade dos Dados
Valida a integridade matemática das taxas, integridade referencial dos municípios e consistência dos microdados:
```bash
python scripts/audit_pipeline.py
```
*(O resultado será salvo automaticamente em `relatorios/audit_report.csv`).*

### 3. Executar o Pipeline de Análise e Gerar Gráficos
Executa a limpeza, as agregações e exporta os 8 gráficos interativos em formato HTML:
```bash
python scripts/analise_tcc.py
```

### 4. Executar os Testes Unitários
Valida as funções de transformação analítica, cálculos ponderados e filtros censitários:
```bash
pytest tests/test_transformers.py
# ou usando o runner nativo do Python:
python -m unittest tests/test_transformers.py
```

### 5. Abrir os Dashboards
*   **Dashboard Web Standalone:** Dê dois cliques em `index.html` (ou abra no navegador). Funciona instantaneamente sem necessidade de rodar nenhum comando de terminal.
*   **Dashboard Streamlit:**
    ```bash
    streamlit run dashboard.py
    ```
