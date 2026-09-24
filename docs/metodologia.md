# Metodologia

O projeto usa um painel mensal por município para integrar saúde, queimadas, população e meteorologia.

## Etapas

1. validar cobertura mensal do SIH/SUS;
2. extrair internações J00–J99 por município de residência;
3. coletar os focos anuais do satélite de referência do INPE e agregá-los por município e mês;
4. obter população anual;
5. consultar meteorologia mensal para as sedes municipais;
6. construir um painel balanceado;
7. calcular taxas por 100 mil habitantes;
8. criar defasagens de focos de 1, 2 e 3 meses;
9. executar EDA e correlações;
10. treinar Regressão Linear e Random Forest com separação temporal;
11. executar análises de sensibilidade, baseline e ablação;
12. gerar gráficos e dashboard HTML.

Detalhes de coleta estão em `coleta.md`, resultados em `resultados.md` e limitações em `limitacoes.md`.
