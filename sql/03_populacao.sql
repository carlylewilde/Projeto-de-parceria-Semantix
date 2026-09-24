-- População residente por município.
-- Fonte primária: IBGE. Camada de acesso: Base dos Dados.

SELECT
  ano,
  CAST(id_municipio AS STRING) AS id_municipio,
  populacao
FROM `basedosdados.br_ibge_populacao.municipio`
WHERE sigla_uf = 'AM'
  AND ano BETWEEN 2015 AND 2025
ORDER BY ano, id_municipio;
