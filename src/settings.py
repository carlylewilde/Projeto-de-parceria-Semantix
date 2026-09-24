from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
VIS = ROOT / "visualizations"
SQL = ROOT / "sql"

START_YEAR = 2015
END_YEAR = 2025
UF = "AM"
UF_IBGE = "13"
SATELITE_REFERENCIA = "AQUA_M-T"
PANDEMIC_START = "2020-01-01"
PANDEMIC_END = "2022-12-31"

for path in (DATA_RAW, DATA_INTERIM, DATA_PROCESSED, VIS):
    path.mkdir(parents=True, exist_ok=True)
