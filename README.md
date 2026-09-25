# Queimadas, clima e internações respiratórias no Amazonas

Projeto de análise de dados desenvolvido a partir de um briefing de portfólio EBAC/Semantix.

## Entrega final

- 📄 [Relatório final consolidado em PDF](Relatorio_Final_Queimadas_Internacoes_Amazonas.pdf)
- 📊 [Dashboard de resultados](visualizations/dashboard_resultados.html)
- 📈 [Resultados detalhados](docs/resultados.md)
- ✅ [Conclusões](docs/conclusoes.md)
- 🧪 [Metodologia e modelagem](docs/modelagem.md)
- 🗂️ [Coleta de dados](docs/coleta.md)

O PDF consolida os tópicos solicitados na atividade — **coleta de dados, modelagem e conclusões** — e o restante do repositório mantém o código e os resultados reproduzíveis.

## Pergunta

Existe associação entre focos de queimadas, condições meteorológicas e internações por doenças do aparelho respiratório entre residentes dos municípios do Amazonas?

## Escopo

- 62 municípios do Amazonas;
- janeiro/2015 a novembro/2025;
- internações SIH/SUS com diagnóstico principal CID-10 J00–J99;
- focos do satélite de referência do INPE;
- população do IBGE;
- temperatura, umidade e precipitação da NASA POWER;
- unidade de análise: município × mês.

O painel final possui **8.122 observações**.

## Resultado em uma frase

**A contagem mensal municipal de focos não apresentou relação simples nem ganho preditivo robusto para explicar as internações respiratórias; município, população, meteorologia e sazonalidade tiveram maior peso no modelo.**

Isso não significa que fumaça de queimadas seja inofensiva. Significa que **contagem de focos por município e mês é uma proxy limitada de exposição humana**.

## Principais números

- internações J00–J99 no painel: **186.529**;
- focos na série anual completa 2015–2025: **162.838**;
- pico anual de focos: **25.499 em 2024**;
- correlação Spearman município–mês entre focos e taxa: **0,012**;
- melhor R² no teste temporal: **0,084** — Random Forest;
- R² do baseline sazonal: **0,051**.

## Modelos

| Modelo | MAE | RMSE | R² — teste 2024–2025 |
|---|---:|---:|---:|
| Regressão Linear | 25,45 | 37,73 | 0,072 |
| Random Forest | 25,43 | 37,48 | 0,084 |
| Baseline município × mês | 25,65 | 38,15 | 0,051 |

## Estrutura

```text
data/
  raw/          dados coletados
  processed/    painel e resultados derivados
  validation/   série usada para validação do INPE

docs/
  coleta.md
  metodologia.md
  modelagem.md
  resultados.md
  conclusoes.md
  limitacoes.md
  referencias.md

src/
  collect_geography.py
  collect_bigquery.py
  collect_inpe_official.py
  collect_weather.py
  build_dataset.py
  eda.py
  model.py
  additional_analysis.py
  make_dashboard.py

visualizations/
  dashboard_resultados.html
  *.png
```

## Como executar

### 1. Ambiente

```bash
python -m venv .venv
pip install -r requirements.txt
```

### 2. BigQuery

Crie `.env` a partir de `.env.example`:

```text
BILLING_PROJECT_ID=seu-projeto-gcp
```

A autenticação do Google Cloud continua sendo necessária no ambiente de execução.

### 3. Pipeline

```bash
python run_pipeline.py
```

O pipeline:

1. obtém as sedes municipais;
2. consulta SIH/SUS e população no BigQuery;
3. coleta os arquivos anuais oficiais do satélite de referência do INPE;
4. consulta NASA POWER;
5. integra e valida o painel;
6. executa EDA;
7. treina os modelos;
8. executa baseline, ablação e sensibilidades;
9. cria o dashboard.

## Visualizações

Abra:

`visualizations/dashboard_resultados.html`

Arquivos principais:

- `01_focos_serie_temporal.png`
- `02_internacoes_serie_temporal.png`
- `03_sazonalidade.png`
- `04_correlacao_spearman.png`
- `06_correlacao_lags.png`
- `07_real_vs_previsto.png`
- `08_importancia_variaveis.png`
- `09_resumo_anual.png`
- `10_comparacao_modelos_r2.png`
- `11_sensibilidade_estacao_fogo.png`

## Interpretação

O Random Forest apresentou apenas pequena melhora sobre um baseline sazonal. A análise de ablação mostrou que retirar as variáveis de focos não piora consistentemente a previsão.

A correlação estadual com defasagem apresenta sinal negativo, mas a análise sazonal mostra que focos e internações possuem picos em períodos diferentes. O sinal muda quando o recorte é restrito aos meses de maior atividade de fogo. Por isso essas correlações não são interpretadas causalmente.

Veja:

- [`docs/resultados.md`](docs/resultados.md)
- [`docs/conclusoes.md`](docs/conclusoes.md)
- [`docs/limitacoes.md`](docs/limitacoes.md)

## Limitação central

Foco de queimadas é uma medida de detecção térmica, não uma medida de concentração de fumaça respirada pela população. Uma etapa epidemiológica mais forte exigiria PM2.5, vento, resolução diária e estratificação por idade e diagnóstico.

## Reprodutibilidade

Os resultados do repositório foram gerados a partir das fontes públicas descritas em `docs/coleta.md`. O código interrompe a execução quando identifica lacunas internas na série de saúde ou divergência material na validação do INPE.

O PDF final também pode ser regenerado pelo workflow do GitHub Actions a partir de `scripts/build_pdf_report.py`.
