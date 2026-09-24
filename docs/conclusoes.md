# Conclusões

A análise reuniu internações do SIH/SUS, focos do satélite de referência do INPE, população do IBGE e variáveis meteorológicas da NASA POWER para os 62 municípios do Amazonas.

O principal resultado é que **não foi identificada uma relação simples e estável entre a contagem mensal de focos de queimadas e a taxa municipal de internações por J00–J99**.

A correlação município–mês foi próxima de zero (`rho = 0.012`), enquanto as correlações estaduais com defasagem apresentaram sinal negativo. A própria análise sazonal mostra que esse sinal é fortemente influenciado pelo fato de queimadas e internações atingirem seus picos em momentos diferentes do ano. Quando a análise é restringida aos meses de maior atividade de fogo, o sinal contemporâneo se torna positivo, mas esse resultado é exploratório e não permite atribuição causal.

Os modelos de Regressão Linear e Random Forest apresentaram **baixo poder preditivo fora da amostra**. O melhor R² no teste 2024–2025 foi **0.084**, obtido pelo Random Forest. Além disso, a retirada das variáveis de focos não piorou consistentemente o desempenho.

Assim, a conclusão adequada não é que as queimadas sejam inofensivas. A literatura epidemiológica encontra efeitos respiratórios associados à fumaça de incêndios, inclusive na Amazônia. O que os resultados deste projeto mostram é que **contagem municipal mensal de focos, isoladamente, é uma proxy limitada para exposição humana à fumaça**.

Entre os fatores que podem explicar essa limitação estão:

- transporte de fumaça entre municípios;
- ausência de uma série homogênea de PM2.5 para todo o estado;
- uso de dados mensais, que pode diluir efeitos de poucos dias;
- agregação de todo o capítulo J00–J99, que reúne doenças com sazonalidades diferentes;
- diferenças etárias e socioeconômicas;
- mudanças de acesso e comportamento hospitalar, especialmente entre 2020 e 2022.

Como continuidade, o projeto pode ser refinado com dados diários, PM2.5, direção e velocidade do vento e estratificação por faixa etária e grupos de CID. Uma modelagem de contagens por Poisson ou Binomial Negativa também seria mais adequada para uma etapa epidemiológica de inferência.

**Conclusão final:** o projeto encontrou forte estrutura espacial e sazonal, mas evidência insuficiente para afirmar, com este desenho, que a variação mensal da contagem de focos explique de forma importante as internações respiratórias no Amazonas.
