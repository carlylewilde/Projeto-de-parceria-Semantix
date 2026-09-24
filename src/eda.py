from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .settings import DATA_PROCESSED, VIS

def save(fig, name):
    fig.tight_layout()
    fig.savefig(VIS / name, dpi=180, bbox_inches="tight")
    plt.close(fig)

def state_monthly(df):
    g = (
        df.groupby("data", as_index=False)
        .agg(
            focos=("focos", "sum"),
            internacoes=("internacoes", "sum"),
            populacao=("populacao", "sum"),
            temperatura_media_c=("temperatura_media_c", "mean"),
            umidade_relativa_media_pct=("umidade_relativa_media_pct", "mean"),
            precipitacao_media_diaria_mm_dia=("precipitacao_media_diaria_mm_dia", "mean"),
        )
    )
    g["taxa_internacoes_100k"] = g["internacoes"] / g["populacao"] * 100_000
    return g

def main():
    df = pd.read_csv(DATA_PROCESSED / "painel_municipal_mensal.csv", parse_dates=["data"])
    state = state_monthly(df)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(state["data"], state["focos"])
    ax.set_title("Focos de queimadas por mês — Amazonas")
    ax.set_xlabel("Data")
    ax.set_ylabel("Focos")
    ax.grid(True, alpha=.25)
    save(fig, "01_focos_serie_temporal.png")

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(state["data"], state["taxa_internacoes_100k"])
    ax.set_title("Taxa mensal de internações respiratórias — Amazonas")
    ax.set_xlabel("Data")
    ax.set_ylabel("Internações por 100 mil habitantes")
    ax.grid(True, alpha=.25)
    save(fig, "02_internacoes_serie_temporal.png")

    seasonal = (
        state.assign(mes=state["data"].dt.month)
        .groupby("mes", as_index=False)
        .agg(
            focos=("focos", "mean"),
            taxa_internacoes_100k=("taxa_internacoes_100k", "mean")
        )
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(seasonal["mes"], seasonal["focos"], marker="o", label="Focos (média)")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Focos médios")
    ax2 = ax.twinx()
    ax2.plot(
        seasonal["mes"], seasonal["taxa_internacoes_100k"],
        marker="s", label="Internações/100 mil (média)"
    )
    ax2.set_ylabel("Internações por 100 mil")
    ax.set_title("Sazonalidade média: queimadas e internações")
    ax.grid(True, alpha=.20)
    save(fig, "03_sazonalidade.png")

    corr_cols = [
        "focos", "taxa_internacoes_100k", "temperatura_media_c",
        "umidade_relativa_media_pct", "precipitacao_media_diaria_mm_dia"
    ]
    corr = df[corr_cols].corr(method="spearman")
    corr.to_csv(DATA_PROCESSED / "correlacao_spearman.csv")

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr.values, vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr_cols)), corr_cols, rotation=45, ha="right")
    ax.set_yticks(range(len(corr_cols)), corr_cols)
    for i in range(len(corr_cols)):
        for j in range(len(corr_cols)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center")
    ax.set_title("Correlação de Spearman")
    fig.colorbar(im, ax=ax, fraction=.046)
    save(fig, "04_correlacao_spearman.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df["focos"], df["taxa_internacoes_100k"], alpha=.35, s=12)
    ax.set_xlabel("Focos no município/mês")
    ax.set_ylabel("Internações respiratórias por 100 mil")
    ax.set_title("Queimadas x internações respiratórias")
    ax.grid(True, alpha=.20)
    save(fig, "05_focos_vs_internacoes.png")

    lag_rows = []
    for lag in (0, 1, 2, 3):
        x = state["focos"].shift(lag)
        y = state["taxa_internacoes_100k"]
        mask = x.notna() & y.notna()
        rho, p = spearmanr(x[mask], y[mask])
        lag_rows.append({"lag_meses": lag, "rho_spearman": rho, "p_valor": p})
    lag_df = pd.DataFrame(lag_rows)
    lag_df.to_csv(DATA_PROCESSED / "correlacao_lags.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(lag_df["lag_meses"].astype(str), lag_df["rho_spearman"])
    ax.axhline(0, linewidth=.8)
    ax.set_xlabel("Defasagem dos focos (meses)")
    ax.set_ylabel("Rho de Spearman")
    ax.set_title("Associação temporal entre focos e internações")
    save(fig, "06_correlacao_lags.png")

    print("EDA concluída.")

if __name__ == "__main__":
    main()
