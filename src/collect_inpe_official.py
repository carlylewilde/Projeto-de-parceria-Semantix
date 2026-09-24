from __future__ import annotations

import io
import re
import time
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd
import requests

from .settings import DATA_RAW, START_YEAR, END_YEAR

STATE_BASE = (
    "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/"
    "EstadosBr_sat_ref/AM/focos_br_am_ref_{year}.zip"
)
BRAZIL_BASE = (
    "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/"
    "Brasil_sat_ref/focos_br_ref_{year}.zip"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; academic-data-project/1.0)"
}


def _norm(value: str) -> str:
    value = "" if pd.isna(value) else str(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.upper().strip()
    value = re.sub(r"[^A-Z0-9 ]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _request(url: str) -> requests.Response:
    last_error = None
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=180)
            r.raise_for_status()
            if not r.content.startswith(b"PK"):
                raise RuntimeError(
                    f"Resposta de {url} não parece um arquivo ZIP "
                    f"(content-type={r.headers.get('content-type')})."
                )
            return r
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Falha ao baixar {url}: {last_error}")


def _read_csv_from_zip(content: bytes, year: int) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(content), "r") as z:
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not csvs:
            raise RuntimeError(f"ZIP do INPE {year} não contém CSV.")
        raw = z.read(csvs[0])

    errors = []
    for encoding in ("utf-8", "utf-8-sig", "latin1"):
        for sep in (",", ";"):
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=encoding, sep=sep)
                if df.shape[1] > 3:
                    return df
            except Exception as exc:
                errors.append(f"{encoding}/{sep}: {exc}")

    for encoding in ("utf-8", "utf-8-sig", "latin1"):
        try:
            return pd.read_csv(
                io.BytesIO(raw),
                encoding=encoding,
                sep=None,
                engine="python"
            )
        except Exception as exc:
            errors.append(f"{encoding}/auto: {exc}")

    raise RuntimeError(
        f"Não foi possível ler o CSV do INPE {year}. "
        + " | ".join(errors[-4:])
    )


def _find_col(columns: list[str], aliases: set[str]) -> str | None:
    mapping = {_norm(c).replace(" ", ""): c for c in columns}
    for alias in aliases:
        key = _norm(alias).replace(" ", "")
        if key in mapping:
            return mapping[key]
    return None


def _download_year(year: int) -> pd.DataFrame:
    if year <= 2024:
        url = STATE_BASE.format(year=year)
        filter_state = False
    else:
        url = BRAZIL_BASE.format(year=year)
        filter_state = True

    print(f"\nINPE {year}: {url}", flush=True)
    response = _request(url)
    print(
        f"  download OK: {len(response.content)/1024:.1f} KiB, "
        f"{response.headers.get('content-type')}",
        flush=True
    )

    df = _read_csv_from_zip(response.content, year)

    data_col = _find_col(
        list(df.columns),
        {
            "DataHora",
            "data_hora_gmt",
            "data_hora",
            "datahora",
            "data_pas",
            "dt_hr_gmt",
        }
    )
    municipio_col = _find_col(
        list(df.columns),
        {"Municipio", "Município", "municipio"}
    )
    estado_col = _find_col(
        list(df.columns),
        {"Estado", "UF", "estado"}
    )
    frp_col = _find_col(
        list(df.columns),
        {"FRP", "potencia_radiativa_fogo", "frp"}
    )
    foco_id_col = _find_col(
        list(df.columns),
        {"foco_id", "id_foco", "focus_id"}
    )

    if data_col is None or municipio_col is None:
        raise RuntimeError(
            f"INPE {year}: colunas essenciais não identificadas. "
            f"Recebidas: {list(df.columns)}"
        )

    if filter_state:
        if estado_col is None:
            raise RuntimeError(
                f"INPE {year}: arquivo Brasil não possui coluna de estado. "
                f"Recebidas: {list(df.columns)}"
            )
        state_norm = df[estado_col].map(_norm)
        df = df[state_norm.isin({"AMAZONAS", "AM"})].copy()
        print(f"  registros do Amazonas após filtro: {len(df):,}", flush=True)

    out = pd.DataFrame()
    out["data_hora"] = pd.to_datetime(
        df[data_col],
        errors="coerce",
        dayfirst=False
    )
    out["municipio_inpe"] = df[municipio_col].astype(str)

    if foco_id_col is not None:
        out["foco_id"] = df[foco_id_col].astype(str)
    else:
        out["foco_id"] = pd.NA

    if frp_col is not None:
        out["frp"] = pd.to_numeric(df[frp_col], errors="coerce")
    else:
        out["frp"] = pd.NA

    if foco_id_col is not None:
        before_dedup = len(out)
        out = out.drop_duplicates(subset=["foco_id"]).copy()
        removed = before_dedup - len(out)
        if removed:
            print(f"  duplicatas por foco_id removidas: {removed:,}", flush=True)

    before = len(out)
    invalid_dates = int(out["data_hora"].isna().sum())
    if invalid_dates:
        sample_raw_dates = (
            df.loc[out["data_hora"].isna(), data_col]
            .astype(str)
            .head(5)
            .tolist()
        )
        print(
            f"  datas não reconhecidas: {invalid_dates:,}; exemplos={sample_raw_dates}",
            flush=True,
        )

    out = out.dropna(subset=["data_hora", "municipio_inpe"]).copy()
    if len(out) < before:
        print(f"  descartados por data/município inválido: {before-len(out):,}", flush=True)

    out["ano"] = out["data_hora"].dt.year
    out["mes"] = out["data_hora"].dt.month

    wrong_year = int((out["ano"] != year).sum())
    if wrong_year:
        print(f"  aviso: {wrong_year:,} linhas com ano diferente foram excluídas.", flush=True)
        out = out[out["ano"].eq(year)].copy()

    print(f"  focos válidos no ano: {len(out):,}", flush=True)
    return out


def main():
    seats = pd.read_csv(
        DATA_RAW / "municipios_am_sedes.csv",
        dtype={"id_municipio": str}
    )
    seats["id_municipio"] = seats["id_municipio"].astype(str).str.zfill(7)
    seats["municipio_norm"] = seats["municipio"].map(_norm)

    municipality_map = dict(
        zip(seats["municipio_norm"], seats["id_municipio"])
    )

    aliases = {
        "SANTO ANTONIO DO ICA": "SANTO ANTONIO DO ICA",
        "SAO SEBASTIAO DO UATUMA": "SAO SEBASTIAO DO UATUMA",
        "SAO PAULO DE OLIVENCA": "SAO PAULO DE OLIVENCA",
        "SAO GABRIEL DA CACHOEIRA": "SAO GABRIEL DA CACHOEIRA",
    }

    for raw_name, seat_name in aliases.items():
        if seat_name in municipality_map:
            municipality_map[raw_name] = municipality_map[seat_name]

    parts = []
    annual = []

    for year in range(START_YEAR, END_YEAR + 1):
        raw = _download_year(year)
        raw["municipio_norm"] = raw["municipio_inpe"].map(_norm)
        raw["id_municipio"] = raw["municipio_norm"].map(municipality_map)

        unmatched = (
            raw.loc[raw["id_municipio"].isna(), ["municipio_inpe", "municipio_norm"]]
            .drop_duplicates()
        )
        if not unmatched.empty:
            print("\nMunicípios sem correspondência:", flush=True)
            print(unmatched.head(30).to_string(index=False), flush=True)
            raise RuntimeError(
                f"INPE {year}: {len(unmatched)} nomes de município sem "
                "correspondência no cadastro de sedes IBGE/geobr."
            )

        annual.append({"ano": year, "focos": len(raw)})

        grouped = (
            raw.groupby(["ano", "mes", "id_municipio"], as_index=False)
            .agg(
                focos=("data_hora", "size"),
                frp_soma=("frp", "sum"),
                frp_media=("frp", "mean"),
            )
        )
        parts.append(grouped)

    out = pd.concat(parts, ignore_index=True)
    out["id_municipio"] = out["id_municipio"].astype(str).str.zfill(7)
    out.to_csv(DATA_RAW / "focos_queimadas_mensal.csv", index=False)

    annual_df = pd.DataFrame(annual).sort_values("ano")
    annual_df.to_csv(
        DATA_RAW / "focos_queimadas_anual_validacao.csv",
        index=False
    )

    print("\nTotais anuais coletados do INPE:", flush=True)
    print(annual_df.to_string(index=False), flush=True)

    validation_path = (
        Path(__file__).resolve().parents[1]
        / "data" / "validation" / "focos_amazonas_anual_2015_2025.csv"
    )

    if validation_path.exists():
        official = pd.read_csv(validation_path)[["ano", "focos"]].copy()
        official = official.rename(columns={"focos": "focos_publicados"})

        check = official.merge(
            annual_df.rename(columns={"focos": "focos_coletados"}),
            on="ano",
            how="left",
        )
        check["diferenca"] = (
            check["focos_coletados"] - check["focos_publicados"]
        )
        check["dif_pct"] = (
            check["diferenca"].abs()
            / check["focos_publicados"].replace(0, pd.NA)
            * 100
        )

        print("\nComparação com a série de validação:", flush=True)
        print(check.to_string(index=False), flush=True)

        material = (
            check["focos_coletados"].isna()
            | (
                (check["diferenca"].abs() > 2)
                & (check["dif_pct"].fillna(100) > 0.1)
            )
        )
        if material.any():
            bad = check.loc[material]
            raise RuntimeError(
                "A série coletada do INPE diverge materialmente da série "
                "de validação nos seguintes anos:\n"
                + bad.to_string(index=False)
            )

    print(
        f"\nINPE corrigido salvo com {len(out):,} linhas município-mês.",
        flush=True
    )


if __name__ == "__main__":
    main()
