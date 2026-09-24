-- SIH/SUS - internações de residentes do Amazonas com diagnóstico principal J00-J99.
-- IMPORTANTE:
-- Na transformação da Base dos Dados, diagnósticos com 3 caracteres ficam em
-- cid_principal_categoria; diagnósticos com 4 caracteres ficam em
-- cid_principal_subcategoria. Portanto, é necessário testar os dois campos.

SELECT
  EXTRACT(YEAR FROM data_internacao) AS ano,
  EXTRACT(MONTH FROM data_internacao) AS mes,
  CAST(id_municipio_paciente AS STRING) AS id_municipio_6,
  COUNT(DISTINCT id_aih) AS internacoes
FROM `basedosdados.br_ms_sih.aihs_reduzidas`
WHERE data_internacao BETWEEN DATE('2015-01-01') AND DATE('2025-12-31')
  AND SUBSTR(CAST(id_municipio_paciente AS STRING), 1, 2) = '13'
  AND (
    REGEXP_CONTAINS(
      UPPER(COALESCE(CAST(cid_principal_categoria AS STRING), '')),
      r'^J[0-9]{2}$'
    )
    OR
    REGEXP_CONTAINS(
      UPPER(COALESCE(CAST(cid_principal_subcategoria AS STRING), '')),
      r'^J[0-9]{2}[0-9A-Z]$'
    )
  )
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
