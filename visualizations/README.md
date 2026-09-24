# Visualizações

O repositório publica um resumo estático em `dashboard_resultados.html`.

Os gráficos completos em PNG são gerados automaticamente ao executar:

```bash
python run_pipeline.py
```

Saídas esperadas:

- `01_focos_serie_temporal.png`
- `02_internacoes_serie_temporal.png`
- `03_sazonalidade.png`
- `04_correlacao_spearman.png`
- `05_focos_vs_internacoes.png`
- `06_correlacao_lags.png`
- `07_real_vs_previsto.png`
- `08_importancia_variaveis.png`
- `09_resumo_anual.png`
- `10_comparacao_modelos_r2.png`
- `11_sensibilidade_estacao_fogo.png`

Os números utilizados no dashboard estão versionados em `data/processed/`.
