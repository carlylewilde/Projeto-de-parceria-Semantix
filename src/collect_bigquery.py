import os
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

from .settings import DATA_RAW, SQL

load_dotenv()

def project_id():
    value = os.getenv("BILLING_PROJECT_ID", "").strip()
    if not value:
        raise RuntimeError(
            "Defina BILLING_PROJECT_ID no arquivo .env antes de consultar o BigQuery."
        )
    return value

def run_sql(filename: str) -> pd.DataFrame:
    client = bigquery.Client(project=project_id())
    sql = (SQL / filename).read_text(encoding="utf-8")
    return client.query(sql).to_dataframe()

def save(filename: str, output_name: str):
    print(f"Executando {filename}...")
    df = run_sql(filename)
    out = DATA_RAW / output_name
    df.to_csv(out, index=False)
    print(f"{len(df):,} linhas -> {out}")
    return df

def main():
    save("00_sih_coverage.sql", "sih_cobertura_mensal.csv")
    sih = save("01_internacoes_respiratorias.sql", "sih_respiratorias_mensal.csv")
    sih["id_municipio_6"] = sih["id_municipio_6"].astype(str).str.zfill(6)
    sih.to_csv(DATA_RAW / "sih_respiratorias_mensal.csv", index=False)

    pop = save("03_populacao.sql", "populacao_municipal.csv")
    pop["id_municipio"] = pop["id_municipio"].astype(str).str.zfill(7)
    pop.to_csv(DATA_RAW / "populacao_municipal.csv", index=False)

if __name__ == "__main__":
    main()
