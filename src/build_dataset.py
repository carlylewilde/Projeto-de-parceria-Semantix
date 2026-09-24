import numpy as np
import pandas as pd

from .settings import (
    DATA_RAW, DATA_PROCESSED, START_YEAR, END_YEAR,
    PANDEMIC_START, PANDEMIC_END
)

def _analysis_end_from_sih():
    coverage = pd.read_csv(DATA_RAW / "sih_cobertura_mensal.csv")

    expected = pd.DataFrame({
        "data": pd.date_range(
            f"{START_YEAR}-01-01",
            f"{END_YEAR}-12-01",
            freq="MS"
        )
    })
    expected["ano"] = expected["data"].dt.year
    expected["mes"] = expected["data"].dt.month

    check = expected.merge(
        coverage[["ano", "mes", "aihs"]],
        on=["ano", "mes"],
        how="left"
    )
    check["disponivel"] = check["aihs"].notna()

    if check["disponivel"].all():
        return pd.Timestamp(f"{END_YEAR}-12-01"), coverage

    first_missing_idx = check.index[~check["disponivel"]][0]

    # Missing months are acceptable only if every month after the first missing
    # one is also absent. A gap in the middle is a data-quality failure.
    if check.loc[first_missing_idx:, "disponivel"].any():
        gaps = check.loc[~check["disponivel"], ["ano", "mes"]]
        raise RuntimeError(
            "O SIH/SUS possui lacuna interna na série mensal. "
            "O pipeline foi interrompido porque não é seguro truncar a série.\n"
            + gaps.to_string(index=False)
        )

    if first_missing_idx == 0:
        raise RuntimeError("Nenhum mês do período solicitado está disponível no SIH/SUS.")

    analysis_end = check.loc[first_missing_idx - 1, "data"]
    missing_tail = check.loc[first_missing_idx:, ["ano", "mes"]]

    print(
        "Aviso de cobertura SIH/SUS: o período solicitado vai até "
        f"{END_YEAR}-12, mas a série contínua disponível termina em "
        f"{analysis_end:%Y-%m}."
    )
    print("Meses finais ainda não usados na análise:")
    print(missing_tail.to_string(index=False))

    return analysis_end, coverage

def _read_inputs():
    seats = pd.read_csv(
        DATA_RAW / "municipios_am_sedes.csv",
        dtype={"id_municipio": str, "id_municipio_6": str}
    )
    sih = pd.read_csv(
        DATA_RAW / "sih_respiratorias_mensal.csv",
        dtype={"id_municipio_6": str}
    )
    fires = pd.read_csv(
        DATA_RAW / "focos_queimadas_mensal.csv",
        dtype={"id_municipio": str}
    )
    pop = pd.read_csv(
        DATA_RAW / "populacao_municipal.csv",
        dtype={"id_municipio": str}
    )
    weather = pd.read_csv(
        DATA_RAW / "meteorologia_nasa_power_mensal.csv",
        dtype={"id_municipio": str}
    )
    return seats, sih, fires, pop, weather

def main():
    analysis_end, _ = _analysis_end_from_sih()
    seats, sih, fires, pop, weather = _read_inputs()

    seats["id_municipio"] = seats["id_municipio"].str.zfill(7)
    seats["id_municipio_6"] = seats["id_municipio_6"].str.zfill(6)
    sih["id_municipio_6"] = sih["id_municipio_6"].str.zfill(6)
    fires["id_municipio"] = fires["id_municipio"].str.zfill(7)
    pop["id_municipio"] = pop["id_municipio"].str.zfill(7)
    weather["id_municipio"] = weather["id_municipio"].str.zfill(7)

    months = pd.DataFrame({
        "data": pd.date_range(
            f"{START_YEAR}-01-01",
            analysis_end,
            freq="MS"
        )
    })
    months["ano"] = months["data"].dt.year
    months["mes"] = months["data"].dt.month

    panel = (
        seats[["id_municipio", "id_municipio_6", "municipio"]]
        .assign(_key=1)
        .merge(months.assign(_key=1), on="_key")
        .drop(columns="_key")
    )

    panel = panel.merge(
        sih[["ano", "mes", "id_municipio_6", "internacoes"]],
        on=["ano", "mes", "id_municipio_6"], how="left"
    )
    panel = panel.merge(
        fires[["ano", "mes", "id_municipio", "focos", "frp_soma", "frp_media"]],
        on=["ano", "mes", "id_municipio"], how="left"
    )
    panel = panel.merge(
        pop[["ano", "id_municipio", "populacao"]],
        on=["ano", "id_municipio"], how="left"
    )
    panel = panel.merge(
        weather.drop(columns=["municipio"], errors="ignore"),
        on=["ano", "mes", "id_municipio"], how="left"
    )

    panel["internacoes"] = panel["internacoes"].fillna(0).astype(int)
    panel["focos"] = panel["focos"].fillna(0).astype(int)
    panel["frp_soma"] = panel["frp_soma"].fillna(0)
    panel["frp_media"] = panel["frp_media"].fillna(0)

    if panel["populacao"].isna().any():
        missing = (
            panel.loc[panel["populacao"].isna(), ["ano", "id_municipio", "municipio"]]
            .drop_duplicates()
        )
        raise RuntimeError(
            "Há população ausente. O pipeline não fará imputação silenciosa.\n"
            + missing.head(30).to_string(index=False)
        )

    weather_cols = [
        "temperatura_media_c",
        "umidade_relativa_media_pct",
        "precipitacao_media_diaria_mm_dia",
    ]
    if panel[weather_cols].isna().any().any():
        n = int(panel[weather_cols].isna().any(axis=1).sum())
        raise RuntimeError(
            f"Há {n} linhas com meteorologia ausente. "
            "Revise a coleta antes de modelar."
        )

    panel["taxa_internacoes_100k"] = (
        panel["internacoes"] / panel["populacao"] * 100_000
    )

    panel["periodo_pandemia"] = (
        panel["data"].between(PANDEMIC_START, PANDEMIC_END)
    ).astype(int)

    angle = 2 * np.pi * panel["mes"] / 12
    panel["mes_sin"] = np.sin(angle)
    panel["mes_cos"] = np.cos(angle)

    panel = panel.sort_values(["id_municipio", "data"])
    for lag in (1, 2, 3):
        panel[f"focos_lag{lag}"] = (
            panel.groupby("id_municipio")["focos"].shift(lag)
        )

    expected_rows = 62 * len(months)
    if len(panel) != expected_rows:
        raise RuntimeError(
            f"Painel deveria ter {expected_rows} linhas; recebeu {len(panel)}."
        )

    panel.to_csv(DATA_PROCESSED / "painel_municipal_mensal.csv", index=False)

    metadata = pd.DataFrame([{
        "inicio_analise": months["data"].min().strftime("%Y-%m"),
        "fim_analise": months["data"].max().strftime("%Y-%m"),
        "meses": len(months),
        "municipios": 62,
        "linhas_painel": len(panel),
    }])
    metadata.to_csv(DATA_PROCESSED / "metadados_cobertura.csv", index=False)

    print(
        f"Painel final salvo com {len(panel):,} linhas "
        f"({months['data'].min():%Y-%m} a {months['data'].max():%Y-%m})."
    )

if __name__ == "__main__":
    main()
