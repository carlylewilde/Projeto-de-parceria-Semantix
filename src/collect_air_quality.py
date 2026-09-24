"""
Módulo opcional para PM2.5.

A UEA/SELVA é mantida no projeto como fonte complementar. A consulta histórica
automatizada depende de identificação dos sensores e, no caso do PurpleAir,
de chave de API. O modelo principal não depende deste arquivo.

Não há preenchimento artificial para anos sem monitoramento.
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv

from .settings import DATA_RAW

load_dotenv()

def download_purpleair(sensor_index: int, start_timestamp: int, end_timestamp: int) -> pd.DataFrame:
    key = os.getenv("PURPLEAIR_API_KEY", "").strip()
    if not key:
        raise RuntimeError("PURPLEAIR_API_KEY não configurada.")

    url = f"https://api.purpleair.com/v1/sensors/{sensor_index}/history"
    params = {
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "average": 60,
        "fields": "pm2.5_alt,humidity,temperature",
    }
    response = requests.get(url, headers={"X-API-Key": key}, params=params, timeout=90)
    response.raise_for_status()
    payload = response.json()

    fields = payload.get("fields", [])
    data = payload.get("data", [])
    return pd.DataFrame(data, columns=fields)

def main():
    mapping = DATA_RAW / "selva_purpleair_sensores.csv"
    if not mapping.exists():
        print(
            "PM2.5 não coletado: falta data/raw/selva_purpleair_sensores.csv "
            "com a relação validada sensor_index x município."
        )
        return
    if not os.getenv("PURPLEAIR_API_KEY", "").strip():
        print("PM2.5 não coletado: PURPLEAIR_API_KEY não configurada.")
        return
    print(
        "A rotina de PM2.5 está habilitada, mas a extração só deve ser executada "
        "após validar a lista de sensores UEA/SELVA."
    )

if __name__ == "__main__":
    main()
