-- Cobertura mensal do SIH/SUS para residentes do Amazonas.
-- Esta consulta NÃO filtra CID. Ela serve apenas para confirmar que o mês
-- está efetivamente presente na fonte antes de interpretar ausência de
-- internações respiratórias como zero.

SELECT
  EXTRACT(YEAR FROM data_internacao) AS ano,
  EXTRACT(MONTH FROM data_internacao) AS mes,
  COUNT(DISTINCT id_aih) AS aihs
FROM `basedosdados.br_ms_sih.aihs_reduzidas`
WHERE data_internacao BETWEEN DATE('2015-01-01') AND DATE('2025-12-31')
  AND SUBSTR(CAST(id_municipio_paciente AS STRING), 1, 2) = '13'
GROUP BY 1, 2
ORDER BY 1, 2;
