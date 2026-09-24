import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .settings import DATA_PROCESSED, VIS

TARGET = "taxa_internacoes_100k"
NUMERIC = [
    "focos", "focos_lag1", "focos_lag2", "focos_lag3",
    "temperatura_media_c", "umidade_relativa_media_pct",
    "precipitacao_media_diaria_mm_dia",
    "mes_sin", "mes_cos", "populacao", "periodo_pandemia"
]
CATEGORICAL = ["id_municipio"]

def metrics(y_true, y_pred):
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": mean_squared_error(y_true, y_pred) ** 0.5,
        "R2": r2_score(y_true, y_pred),
    }

def preprocessor():
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, NUMERIC),
        ("cat", categorical_pipe, CATEGORICAL),
    ])

def models():
    return {
        "regressao_linear": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=500,
            min_samples_leaf=5,
            max_features="sqrt",
            random_state=42,
            n_jobs=-1,
        ),
    }

def fit_eval(df, sensitivity=False):
    data = df.copy()
    if sensitivity:
        data = data.loc[data["periodo_pandemia"] == 0].copy()

    data = data.dropna(subset=["focos_lag1", "focos_lag2", "focos_lag3"])

    train = data.loc[data["data"] < "2023-01-01"]
    valid = data.loc[(data["data"] >= "2023-01-01") & (data["data"] < "2024-01-01")]
    test = data.loc[data["data"] >= "2024-01-01"]

    rows = []
    fitted = {}

    for name, estimator in models().items():
        pipe = Pipeline([("prep", preprocessor()), ("model", estimator)])
        pipe.fit(train[NUMERIC + CATEGORICAL], train[TARGET])

        pred_valid = pipe.predict(valid[NUMERIC + CATEGORICAL])
        rows.append({"modelo": name, "amostra": "validacao_2023", **metrics(valid[TARGET], pred_valid)})

        train_valid = pd.concat([train, valid], ignore_index=True)
        pipe.fit(train_valid[NUMERIC + CATEGORICAL], train_valid[TARGET])
        pred_test = pipe.predict(test[NUMERIC + CATEGORICAL])
        rows.append({"modelo": name, "amostra": "teste_2024_2025", **metrics(test[TARGET], pred_test)})

        fitted[name] = (pipe, test.copy(), pred_test)

    result = pd.DataFrame(rows)
    result["analise"] = "sensibilidade_sem_pandemia" if sensitivity else "principal"
    return result, fitted

def feature_importance_rf(pipe):
    prep = pipe.named_steps["prep"]
    model = pipe.named_steps["model"]
    names = prep.get_feature_names_out()
    imp = pd.DataFrame({"feature": names, "importancia": model.feature_importances_})
    imp["grupo"] = np.where(
        imp["feature"].str.startswith("cat__id_municipio_"),
        "efeito_municipio",
        imp["feature"].str.replace("num__", "", regex=False)
    )
    return (
        imp.groupby("grupo", as_index=False)["importancia"].sum()
        .sort_values("importancia", ascending=False)
    )

def main():
    df = pd.read_csv(DATA_PROCESSED / "painel_municipal_mensal.csv", parse_dates=["data"])

    main_metrics, fitted = fit_eval(df, sensitivity=False)
    sens_metrics, _ = fit_eval(df, sensitivity=True)
    all_metrics = pd.concat([main_metrics, sens_metrics], ignore_index=True)
    all_metrics.to_csv(DATA_PROCESSED / "metricas_modelos.csv", index=False)

    pipe, test, pred = fitted["random_forest"]
    test = test.assign(previsto=pred)
    state = (
        test.groupby("data", as_index=False)
        .agg(real=(TARGET, "mean"), previsto=("previsto", "mean"))
    )

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(state["data"], state["real"], label="Observado")
    ax.plot(state["data"], state["previsto"], label="Previsto")
    ax.set_title("Random Forest: observado x previsto no período de teste")
    ax.set_xlabel("Data")
    ax.set_ylabel("Taxa média municipal por 100 mil")
    ax.legend()
    ax.grid(True, alpha=.25)
    fig.tight_layout()
    fig.savefig(VIS / "07_real_vs_previsto.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    importance = feature_importance_rf(pipe)
    importance.to_csv(DATA_PROCESSED / "importancia_variaveis_random_forest.csv", index=False)

    top = importance.head(12).sort_values("importancia")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["grupo"], top["importancia"])
    ax.set_title("Importância das variáveis — Random Forest")
    ax.set_xlabel("Importância relativa")
    fig.tight_layout()
    fig.savefig(VIS / "08_importancia_variaveis.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(all_metrics.to_string(index=False))

if __name__ == "__main__":
    main()
