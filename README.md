# 📉 Análise de Evasão em Cursos de TI (UFPB - Campus IV Rio Tinto)

Este repositório contém a infraestrutura de dados, scripts de processamento, pipelines de auditoria de qualidade e um painel interativo (dashboard) voltado para a análise de evasão e trajetórias acadêmicas no ensino superior, com foco especial nos cursos de Tecnologia da Informação (TI) da Paraíba e do Campus IV da UFPB (Rio Tinto).

---

## 🛠️ Tecnologias Utilizadas

A pilha tecnológica foi estruturada para garantir eficiência, reprodutibilidade e visualização moderna de dados:

*   **Linguagem Principal:** Python 3.10+
*   **Manipulação e Limpeza de Dados:** [Pandas](https://pandas.pydata.org/) & [Numpy](https://numpy.org/) (processamento eficiente de microdados e dados consolidados)
*   **Visualização Interativa:** [Plotly](https://plotly.com/python/) (criação de gráficos interativos HTML ricos em dados) e [Streamlit](https://streamlit.io/) (construção do painel web ágil e esteticamente premium)
*   **Leitura de Planilhas:** `openpyxl` (integração direta com relatórios originais em formato Excel do INEP)
*   **Auditoria e Qualidade:** Pipeline automatizado de testes de consistência estatística e lógica de dados.

---

## 📊 Metodologia e Indicadores Utilizados

Uma das contribuições metodológicas cruciais deste projeto é a diferenciação e correta interpretação de dois indicadores distintos disponibilizados pelo INEP:

### 1. Taxa de Evasão Anual (Indicador Transversal)
*   **O que é:** Uma métrica instantânea calculada anualmente que estima o fluxo de evasão geral em um determinado ano letivo.
*   **Como funciona:** Compara a quantidade de alunos que se desligaram do sistema em relação ao total de matriculados naquele ano específico. Mistura alunos que estão no início, meio e fim do curso.
*   **Uso no projeto:** Utilizado para fornecer o panorama macrogeográfico (Nível Regiões e Estados/UF), demonstrando a evolução temporal de fluxo anual.

### 2. Taxa de Desistência Acumulada - TDA (Indicador Longitudinal / Coorte)
*   **O que é:** Um indicador que acompanha um grupo específico de estudantes que ingressaram no mesmo ano (**Coorte de 2020**) ao longo do tempo (referência de 2020 a 2024).
*   **Como funciona:** Acumula as desistências reais de forma sequencial. Após 5 anos de acompanhamento (em 2024), mede de forma exata a porcentagem de alunos daquela turma que desistiram do curso.
*   **Uso no projeto:** Utilizado na análise microgeográfica e de trajetórias de cursos individuais (Brasil, Paraíba e Campus Rio Tinto da UFPB), permitindo identificar o comportamento específico em TI e STEM.
*   **Particularidade do Censo:** O curso de *Licenciatura em Ciência da Computação* de Rio Tinto é classificado na CINE-MEC como área geral de **Educação (01)** (formação de professores), enquanto *Sistemas de Informação* é classificado em **Computação/TIC (06)**. O projeto trata essa distinção de forma que ambos os cursos sejam analisados adequadamente em Rio Tinto.

---

## 📉 Explicação dos Gráficos Gerados

Os gráficos foram desenhados sob uma identidade visual moderna (modo escuro, paleta HSL harmoniosa e micro-interações via cursor).

### Gráfico 1: Série Temporal de Evasão por Região (2020–2024)
*   **Tipo:** Linhas com Marcadores (`go.Scatter`).
*   **Finalidade:** Demonstrar o comportamento anual da evasão em todo o país. Destaca a trajetória da Região Nordeste, que se mantém acima da média nacional no período recente.

### Gráfico 2: Ranking de Regiões (2023–2024)
*   **Tipo:** Barras Horizontais (`go.Bar`).
*   **Finalidade:** Ordenar de forma clara quais regiões do país sofreram maior índice de evasão transversal no último ano de análise, incluindo uma linha média de referência.

### Gráfico 3: Série Temporal - Paraíba vs Estados do Nordeste (2020–2024)
*   **Tipo:** Linhas com Destaque de Cor (`go.Scatter`).
*   **Finalidade:** Posicionar o comportamento da Paraíba em relação aos seus vizinhos regionais. Destaca que, apesar de flutuações, a Paraíba encerrou 2024 com uma taxa de evasão de **13.0%**, abaixo da média nordestina de **16.0%**.

### Gráfico 4: Drilldown de Evasão Acumulada (Brasil → Paraíba → Rio Tinto)
*   **Tipo:** Linhas de Coorte com Preenchimento de Área (`go.Scatter` com `fill="tozeroy"`).
*   **Finalidade:** Demonstrar visualmente a hierarquia geográfica da TDA acumulada para a coorte de 2020. Exibe a acumulação de desistências ano a ano de referência, revelando que a curva acumulada local de Rio Tinto se alinha à tendência nacional/estadual de alta evasão em exatas/TI ao longo do ciclo de graduação.

### Gráfico 5: Trajetória dos Cursos de Rio Tinto (Coorte 2020)
*   **Tipo:** Gráfico Multi-painel/Subplots de Barras e Linhas Pontilhadas (`make_subplots`, `go.Bar` e `go.Scatter`).
*   **Finalidade:** Contrastar a **TDA** (Taxa de Desistência Acumulada) com a **TADA** (Taxa de Desistência Anualizada da Coorte) para os dois principais cursos de TI do Campus IV (Licenciatura em Ciência da Computação e Sistemas de Informação), evidenciando a evolução temporal de perdas de cada turma.

### Gráfico 6: Distribuição da TDA por Grau Acadêmico na Paraíba (TI, 2024)
*   **Tipo:** Gráficos de Violino e Boxplot integrados (`go.Violin`).
*   **Finalidade:** Exibir a distribuição estatística (médias, quartis, densidade e outliers) das TDAs acumuladas em 2024 para cursos de TI no estado da Paraíba, segmentando entre Bacharelados e Licenciaturas, sinalizando o posicionamento individual dos cursos de Rio Tinto no cenário estadual.

---

## 🗂️ Estrutura do Repositório

*   [dashboard_interativo.html](file:///C:/Users/Senec/Desktop/Estudos/Projeto%20TCC/dashboard_interativo.html): Dashboard interativo autocontido (HTML/CSS/JS/Plotly) com filtros por abas, gráficos de gênero, recorte PPI, funil de coortes e rankings, pronto para visualização direta no navegador.
*   [dashboard.py](file:///C:/Users/Senec/Desktop/Estudos/Projeto%20TCC/dashboard.py): Aplicação interativa completa construída com Streamlit e Plotly.
*   [analise_tcc.py](file:///C:/Users/Senec/Desktop/Estudos/Projeto%20TCC/analise_tcc.py): Pipeline de ETL, limpeza de dados, fusão de bases do INEP e exportação automatizada de gráficos HTML e tabelas processadas.
*   [audit_pipeline.py](file:///C:/Users/Senec/Desktop/Estudos/Projeto%20TCC/audit_pipeline.py): Pipeline de testes que executa validação de checksums MD5, consistência matemática entre as taxas (ex: $TAP + TCA + TDA \le 100\%$) e integridade lógica dos filtros.
*   [requirements.txt](file:///C:/Users/Senec/Desktop/Estudos/Projeto%20TCC/requirements.txt): Relação de dependências do Python necessárias para a execução do projeto.
*   `.gitignore`: Filtro de exclusão para arquivos pesados (>100 MB) e temporários.
*   `dados/`: Diretório contendo as bases consolidadas de indicadores de região, UF e trajetória de cursos obtidas junto ao INEP.
*   `dados_processados/`: Tabelas tratadas e filtradas com os recortes geográficos e locais analisados.
*   `graficos_evasao/`: Gráficos interativos exportados em HTML prontos para consulta ou captura para o artigo.

---

## 🚀 Como Executar o Projeto

1.  **Instalar Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Executar a Auditoria de Qualidade dos Dados:**
    ```bash
    python audit_pipeline.py
    ```

3.  **Processar e Gerar os Gráficos:**
    ```bash
    python analise_tcc.py
    ```

4.  **Visualizar os Dashboards:**
    *   **Opção A — Dashboard Web Standalone (Navegador):**  
        Basta abrir o arquivo `dashboard_interativo.html` diretamente em qualquer navegador (Google Chrome, Edge, Firefox). Não requer Python em execução.
    *   **Opção B — Dashboard Streamlit:**  
        ```bash
        streamlit run dashboard.py
        ```
