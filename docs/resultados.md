# Resultados

## Cobertura e volume de dados

A análise final cobre **62 municípios do Amazonas**, de **janeiro de 2015 a novembro de 2025**. O mês de dezembro de 2025 não foi incluído porque não apareceu como mês contínuo disponível na extração do SIH/SUS utilizada.

O painel contém **8.122 observações município–mês**, com:

- **186,529 internações** por doenças do aparelho respiratório (CID-10 J00–J99);
- **162,838 focos** na série anual completa do satélite de referência do INPE entre 2015 e 2025;
- **162,720 focos** dentro do mesmo recorte mensal usado no painel de saúde, que termina em novembro de 2025.

A diferença entre a série anual completa de focos e o painel ocorre porque dezembro de 2025 não entra na análise conjunta com internações.

## Comportamento anual

O maior número anual de focos do período ocorreu em **2024**, com **25,499 focos**.

O maior número anual de internações no recorte analisado ocorreu em **2023**, com **24,207 internações**.

A série de 2025 apresentou **4.545 focos no ano completo**, contra **25.499 em 2024**, redução de aproximadamente **82,2%**.

## Sazonalidade

A distribuição das queimadas é fortemente sazonal. No painel, **85.7%** dos focos ocorreram entre agosto e novembro.

A média mensal de focos estaduais foi maior em **agosto**, com aproximadamente **5,847 focos** por agosto ao longo do período. A taxa média estadual de internações respiratórias atingiu seu maior valor em **maio**, com cerca de **45.9 internações por 100 mil habitantes**.

Essa defasagem sazonal ajuda a explicar por que uma correlação simples entre focos e internações pode produzir sinais contraintuitivos.

## Correlações

No painel município–mês, a correlação de Spearman entre focos e taxa de internações foi **rho = 0.012**, praticamente nula.

Quando as séries são agregadas para o estado e os focos são defasados, a maior magnitude observada ocorreu com **2 meses de defasagem: rho = -0.439**. O sinal foi negativo.

Esse resultado **não deve ser interpretado como efeito protetor das queimadas**. Ele é compatível com forte estrutura sazonal: as queimadas se concentram principalmente no período seco, enquanto parte importante das internações J00–J99 ocorre em meses mais úmidos.

Como verificação exploratória, restringindo a série estadual a **agosto–novembro**, a associação contemporânea muda para **rho = 0.324**. Essa análise de sensibilidade reforça que o sinal da correlação depende do recorte sazonal e, portanto, não sustenta inferência causal.

## Desempenho dos modelos

### Teste temporal 2024–2025

| Modelo | MAE | RMSE | R² |
|---|---:|---:|---:|
| Regressão Linear | 25.45 | 37.73 | 0.072 |
| Random Forest | 25.43 | 37.48 | 0.084 |
| Baseline média município × mês | 25.65 | 38.15 | 0.051 |

O Random Forest apresentou o melhor resultado entre os dois modelos principais, mas a diferença foi pequena. O **R² de 0.084** mostra que a maior parte da variação mensal das taxas municipais permanece sem explicação pelo conjunto de variáveis usado.

Na validação de 2023, ambos os modelos apresentaram R² negativo, indicando dificuldade de generalização naquele ano.

## Variáveis de queimadas e capacidade preditiva

Na Random Forest, as variáveis ligadas a município e população concentraram aproximadamente **52.4%** da importância total. As variáveis meteorológicas somaram **23.5%**, e os focos do mês corrente mais as três defasagens somaram **12.9%**.

Importância de variável não é medida causal.

Na análise de ablação, retirar as variáveis de focos quase não alterou a Regressão Linear e não piorou de forma consistente o Random Forest. No teste, o Random Forest **sem focos** obteve R² ligeiramente maior do que o modelo completo, embora com MAE discretamente pior.

Portanto, neste desenho mensal e municipal, **os focos de queimadas não acrescentaram ganho preditivo robusto às demais variáveis**.

## Leitura geral

Os dados confirmam uma forte sazonalidade das queimadas e mostram que o comportamento das internações respiratórias é mais complexo do que uma relação linear simples com contagem de focos.

O resultado não contradiz estudos epidemiológicos que encontram efeitos adversos da fumaça. Este projeto usa **contagem municipal mensal de focos** como proxy de exposição e agrega todo o capítulo J00–J99. Estudos que estimam exposição a PM2.5, transporte de fumaça, faixas etárias e efeitos em escala diária possuem maior capacidade para identificar impactos agudos.
