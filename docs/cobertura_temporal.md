# Cobertura temporal

O período planejado foi 2015–2025.

Na extração do SIH/SUS usada neste projeto, a série contínua por `data_internacao`
para residentes do Amazonas contém 131 meses, de 2015-01 a 2025-11.
O mês 2025-12 não apareceu nessa consulta.

Decisão metodológica: encerrar a análise em 2025-11, sem imputar dezembro como zero.

O pipeline aceita ausência apenas no final da série. Se surgir qualquer lacuna entre
dois meses disponíveis, a construção do painel é interrompida.
