import os
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

from .settings import DATA_RAW

load_dotenv()
PROJECT_ID = os.environ["BILLING_PROJECT_ID"]

QUERY = r"""
SELECT
  EXTRACT(YEAR FROM data_internacao) AS ano,
  COUNT(DISTINCT IF(
    REGEXP_CONTAINS(
      UPPER(COALESCE(CAST(cid_principal_categoria AS STRING), '')),
      r'^J[0-9]{2}$'
    ),
    id_aih, NULL
  )) AS so_categoria_3_chars,
  COUNT(DISTINCT IF(
    REGEXP_CONTAINS(
      UPPER(COALESCE(CAST(cid_principal_subcategoria AS STRING), '')),
      r'^J[0-9]{2}[0-9A-Z]$'
    ),
    id_aih, NULL
  )) AS so_subcategoria_4_chars,
  COUNT(DISTINCT IF(
    REGEXP_CONTAINS(
      UPPER(COALESCE(CAST(cid_principal_categoria AS STRING), '')),
      r'^J[0-9]{2}$'
    )
    OR
    REGEXP_CONTAINS(
      UPPER(COALESCE(CAST(cid_principal_subcategoria AS STRING), '')),
      r'^J[0-9]{2}[0-9A-Z]$'
    ),
    id_aih, NULL
  )) AS total_j00_j99
FROM `basedosdados.br_ms_sih.aihs_reduzidas`
WHERE data_internacao BETWEEN DATE('2015-01-01') AND DATE('2025-12-31')
  AND SUBSTR(CAST(id_municipio_paciente AS STRING), 1, 2) = '13'
GROUP BY 1
ORDER BY 1
"""

def main():
    client = bigquery.Client(project=PROJECT_ID)
    df = client.query(QUERY).to_dataframe()
    df.to_csv(DATA_RAW / "diagnostico_sih_cid.csv", index=False)
    print(df.to_string(index=False))
    print("\nTotal J00-J99:", int(df["total_j00_j99"].sum()))

if __name__ == "__main__":
    main()
