import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .settings import DATA_PROCESSED, VIS

TARGET = "taxa_internacoes_100k"
NUM_FULL = [
    "focos", "focos_lag1", "focos_lag2", "focos_lag3",
    "temperatura_media_c", "umidade_relativa_media_pct",
    "precipitacao_media_diaria_mm_dia",
    "mes_sin", "mes_cos", "populacao", "periodo_pandemia"
]
NUM_NO_FIRE = [c for c in NUM_FULL if not c.startswith("focos")]
CAT = ["id_municipio"]

def metricas(y, pred):
    return {
        "MAE": mean_absolute_error(y, pred),
        "RMSE": mean_squared_error(y, pred) ** 0.5,
        "R2": r2_score(y, pred),
    }

def prep(cols):
    return ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), cols),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), CAT),
    ])

def avaliar(train_valid, test, cols, estimator):
    pipe = Pipeline([("prep", prep(cols)), ("model", estimator)])
    pipe.fit(train_valid[cols + CAT], train_valid[TARGET])
    pred = pipe.predict(test[cols + CAT])
    return metricas(test[TARGET], pred)

def main():
    df = pd.read_csv(DATA_PROCESSED / "painel_municipal_mensal.csv", parse_dates=["data"])
    data = df.dropna(subset=["focos_lag1", "focos_lag2", "focos_lag3"]).copy()

    train_valid = data.loc[data["data"] < "2024-01-01"].copy()
    test = data.loc[data["data"] >= "2024-01-01"].copy()

    # Baseline: média histórica de município × mês.
    seasonal = train_valid.groupby(["id_municipio", "mes"])[TARGET].mean()
    municipal = train_valid.groupby("id_municipio")[TARGET].mean()
    global_mean = train_valid[TARGET].mean()
    pred_base = np.array([
        seasonal.get((m, mes), municipal.get(m, global_mean))
        for m, mes in zip(test["id_municipio"], test["mes"])
    ])
    pd.DataFrame([{
        "modelo": "baseline_media_municipio_mes",
        "amostra": "teste_2024_2025",
        **metricas(test[TARGET], pred_base),
    }]).to_csv(DATA_PROCESSED / "metricas_baseline.csv", index=False)

    rows = []
    for nome, factory in [
        ("regressao_linear", lambda: LinearRegression()),
        ("random_forest", lambda: RandomForestRegressor(
            n_estimators=500, min_samples_leaf=5,
            max_features="sqrt", random_state=42, n_jobs=-1
        )),
    ]:
        for variante, cols in [("com_focos", NUM_FULL), ("sem_focos", NUM_NO_FIRE)]:
            rows.append({
                "modelo": nome,
                "variante": variante,
                **avaliar(train_valid, test, cols, factory())
            })
    pd.DataFrame(rows).to_csv(DATA_PROCESSED / "ablacao_focos.csv", index=False)

    state = (
        df.groupby("data", as_index=False)
        .agg(
            focos=("focos", "sum"),
            internacoes=("internacoes", "sum"),
            populacao=("populacao", "sum"),
        )
    )
    state["taxa"] = state["internacoes"] / state["populacao"] * 100_000
    state["mes"] = state["data"].dt.month

    rows = []
    for lag in (0, 1, 2, 3):
        x = state["focos"].shift(lag)
        mask = state["mes"].isin([8, 9, 10, 11]) & x.notna()
        rho, p = spearmanr(x[mask], state.loc[mask, "taxa"])
        rows.append({
            "periodo": "agosto_novembro",
            "lag_meses": lag,
            "rho_spearman": rho,
            "p_valor_nao_ajustado": p,
            "n_meses": int(mask.sum()),
        })
    sensitivity = pd.DataFrame(rows)
    sensitivity.to_csv(DATA_PROCESSED / "sensibilidade_estacao_fogo.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(sensitivity["lag_meses"].astype(str), sensitivity["rho_spearman"])
    ax.axhline(0, linewidth=.8)
    ax.set_xlabel("Defasagem dos focos (meses)")
    ax.set_ylabel("Rho de Spearman")
    ax.set_title("Sensibilidade: agosto–novembro")
    fig.tight_layout()
    fig.savefig(VIS / "11_sensibilidade_estacao_fogo.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("Análises adicionais concluídas.")

if __name__ == "__main__":
    main()
