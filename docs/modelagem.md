# Modelagem

## Unidade de análise

A unidade básica é `município × mês`.

A execução final cobre janeiro de 2015 a novembro de 2025:

`62 municípios × 131 meses = 8.122 observações`.

## Variável alvo

`taxa_internacoes_100k`

\[
taxa = \frac{internações\ respiratórias}{população} \times 100000
\]

## Variáveis explicativas

- focos no mês;
- focos com defasagem de 1, 2 e 3 meses;
- temperatura média;
- umidade relativa média;
- precipitação média diária do mês;
- seno e cosseno do mês;
- população;
- indicador 2020–2022;
- município como variável categórica.

## Divisão temporal

- treinamento: 2015–2022;
- validação: 2023;
- teste: 2024–novembro/2025.

Depois da validação, o modelo é ajustado novamente com 2015–2023 e avaliado no teste.

## Modelos principais

### Regressão Linear

Baseline paramétrico para comparação.

### Random Forest Regressor

Modelo não linear com 500 árvores, `min_samples_leaf=5` e `max_features="sqrt"`.

## Métricas

São reportados MAE, RMSE e R².

No teste temporal:

| Modelo | MAE | RMSE | R² |
|---|---:|---:|---:|
| Regressão Linear | 25.45 | 37.73 | 0.072 |
| Random Forest | 25.43 | 37.48 | 0.084 |

Como referência adicional, foi calculado um baseline sazonal por município e mês, com R² de **0.051**.

## Análise de sensibilidade

A modelagem também é repetida retirando 2020–2022. O desempenho permanece baixo e as conclusões gerais não mudam de forma substancial.

## Ablação das variáveis de focos

Foi executada uma comparação entre os modelos completos e versões sem `focos`, `focos_lag1`, `focos_lag2` e `focos_lag3`.

A remoção dessas variáveis não produziu piora consistente no teste. Isso indica que, neste desenho, a contagem de focos acrescenta pouco sinal preditivo além de município, população, meteorologia e sazonalidade.

## Interpretação

R² baixo não invalida a análise exploratória. Ele indica que as variáveis disponíveis explicam apenas uma fração pequena da variação mensal das taxas.

A Random Forest é usada para previsão e exploração de importância relativa, não para inferência causal.
