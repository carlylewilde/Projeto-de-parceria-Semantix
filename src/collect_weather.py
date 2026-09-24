import time
import requests
import pandas as pd

from .settings import DATA_RAW, START_YEAR, END_YEAR

API = "https://power.larc.nasa.gov/api/temporal/monthly/point"
PARAMS = ["T2M", "RH2M", "PRECTOTCORR"]

def fetch_point(lat: float, lon: float) -> pd.DataFrame:
    params = {
        "parameters": ",".join(PARAMS),
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
        "start": START_YEAR,
        "end": END_YEAR,
    }
    response = requests.get(API, params=params, timeout=90)
    response.raise_for_status()
    payload = response.json()

    series = payload["properties"]["parameter"]
    rows = []
    for key, temp in series["T2M"].items():
        key = str(key)
        if len(key) < 6:
            continue
        ano = int(key[:4])
        mes = int(key[4:6])
        if not 1 <= mes <= 12:
            continue
        rows.append({
            "ano": ano,
            "mes": mes,
            "temperatura_media_c": temp,
            "umidade_relativa_media_pct": series["RH2M"].get(key),
            # No nível mensal, PRECTOTCORR é tratado como média diária do mês.
            "precipitacao_media_diaria_mm_dia": series["PRECTOTCORR"].get(key),
        })
    return pd.DataFrame(rows)

def main():
    seats = pd.read_csv(DATA_RAW / "municipios_am_sedes.csv", dtype={"id_municipio": str})
    parts = []

    for i, row in seats.iterrows():
        print(f"[{i+1:02d}/{len(seats)}] NASA POWER - {row['municipio']}")
        climate = fetch_point(float(row["latitude"]), float(row["longitude"]))
        climate["id_municipio"] = str(row["id_municipio"]).zfill(7)
        climate["municipio"] = row["municipio"]
        parts.append(climate)
        # Requisições sequenciais para não pressionar o serviço.
        time.sleep(0.25)

    out = pd.concat(parts, ignore_index=True)
    expected = 62 * ((END_YEAR - START_YEAR + 1) * 12)
    if len(out) != expected:
        raise RuntimeError(
            f"Esperados {expected} registros clima-município-mês; recebidos {len(out)}."
        )

    out.to_csv(DATA_RAW / "meteorologia_nasa_power_mensal.csv", index=False)
    print("Meteorologia salva.")

if __name__ == "__main__":
    main()
