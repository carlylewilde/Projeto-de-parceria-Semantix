import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

from .settings import DATA_PROCESSED, VIS

def div(fig):
    return plot(fig, include_plotlyjs=False, output_type="div", config={"responsive": True})

def main():
    df = pd.read_csv(DATA_PROCESSED / "painel_municipal_mensal.csv", parse_dates=["data"])
    metrics = pd.read_csv(DATA_PROCESSED / "metricas_modelos.csv")
    baseline = pd.read_csv(DATA_PROCESSED / "metricas_baseline.csv")
    ablation = pd.read_csv(DATA_PROCESSED / "ablacao_focos.csv")
    importance = pd.read_csv(DATA_PROCESSED / "importancia_variaveis_random_forest.csv")
    meta = pd.read_csv(DATA_PROCESSED / "metadados_cobertura.csv").iloc[0]

    state = (
        df.groupby("data", as_index=False)
        .agg(
            focos=("focos", "sum"),
            internacoes=("internacoes", "sum"),
            populacao=("populacao", "sum"),
        )
    )
    state["taxa_internacoes_100k"] = state["internacoes"] / state["populacao"] * 100_000

    fig1 = px.line(state, x="data", y="focos", title="Focos de queimadas por mês")
    fig2 = px.line(
        state, x="data", y="taxa_internacoes_100k",
        title="Internações respiratórias por 100 mil habitantes"
    )
    fig3 = px.scatter(
        df, x="focos", y="taxa_internacoes_100k",
        hover_name="municipio", hover_data=["ano", "mes"],
        title="Focos x taxa de internações"
    )

    seasonal = (
        df.groupby("mes", as_index=False)
        .agg(focos=("focos", "mean"), taxa=("taxa_internacoes_100k", "mean"))
    )
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=seasonal["mes"], y=seasonal["focos"], name="Focos médios"))
    fig4.add_trace(go.Scatter(
        x=seasonal["mes"], y=seasonal["taxa"], name="Taxa média", yaxis="y2"
    ))
    fig4.update_layout(
        title="Sazonalidade",
        yaxis2={"overlaying": "y", "side": "right"}
    )

    best = metrics.loc[
        (metrics["analise"] == "principal") &
        (metrics["amostra"] == "teste_2024_2025")
    ].copy()

    metric_table = best.to_html(index=False, float_format=lambda x: f"{x:.3f}")
    baseline_table = baseline.to_html(index=False, float_format=lambda x: f"{x:.3f}")
    ablation_table = ablation.to_html(index=False, float_format=lambda x: f"{x:.3f}")
    imp_table = importance.head(8).to_html(index=False, float_format=lambda x: f"{x:.3f}")

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Queimadas e internações respiratórias no Amazonas</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body {{ font-family: Arial, sans-serif; max-width: 1180px; margin: 0 auto; padding: 28px; color: #202124; }}
h1 {{ margin-bottom: 4px; }}
.subtitle {{ color: #5f6368; margin-top: 0; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
.card {{ border: 1px solid #ddd; border-radius: 10px; padding: 12px; }}
.kpis {{ display:grid; grid-template-columns: repeat(4,1fr); gap:12px; margin:18px 0; }}
.kpi {{ border:1px solid #ddd; border-radius:10px; padding:14px; text-align:center; }}
.kpi strong {{ display:block; font-size:1.45rem; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
th, td {{ border-bottom: 1px solid #ddd; padding: 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
.note {{ background: #f6f7f8; padding: 12px 16px; border-radius: 8px; }}
@media (max-width: 800px) {{
  .grid, .kpis {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<h1>Queimadas e internações respiratórias no Amazonas</h1>
<p class="subtitle">Painel município–mês — 62 municípios, {meta['inicio_analise']} a {meta['fim_analise']}</p>

<div class="kpis">
  <div class="kpi"><strong>{int(df['internacoes'].sum()):,}</strong>internações</div>
  <div class="kpi"><strong>{int(df['focos'].sum()):,}</strong>focos no painel</div>
  <div class="kpi"><strong>{int(meta['linhas_painel']):,}</strong>município-mês</div>
  <div class="kpi"><strong>{best['R2'].max():.3f}</strong>melhor R² no teste</div>
</div>

<div class="note">
Os resultados descrevem associação e capacidade preditiva. Não demonstram causalidade.
O desempenho preditivo foi baixo, portanto as relações devem ser interpretadas com cautela.
</div>

<div class="grid">
  <div class="card">{div(fig1)}</div>
  <div class="card">{div(fig2)}</div>
  <div class="card">{div(fig3)}</div>
  <div class="card">{div(fig4)}</div>
</div>

<h2>Modelos principais — teste temporal 2024–2025</h2>
{metric_table}

<h2>Baseline sazonal</h2>
{baseline_table}

<h2>Análise de ablação — retirar variáveis de focos</h2>
{ablation_table}

<h2>Importância das variáveis — Random Forest</h2>
{imp_table}

<p>Detalhes metodológicos e interpretação estão em <code>docs/</code>.</p>
</body>
</html>"""

    out = VIS / "dashboard_resultados.html"
    out.write_text(html, encoding="utf-8")
    print(f"Dashboard salvo em {out}")

if __name__ == "__main__":
    main()
