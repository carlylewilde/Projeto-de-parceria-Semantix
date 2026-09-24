# Coleta de dados

## SIH/SUS

A variável de saúde é o número de internações com diagnóstico principal do capítulo J00–J99 da CID-10. O município usado é o **município de residência do paciente**, e não o município do estabelecimento.

A consulta é executada na tabela pública `br_ms_sih.aihs_reduzidas`, disponibilizada pela Base dos Dados a partir do SIH/SUS.

Na transformação dessa tabela, diagnósticos com três caracteres podem aparecer em `cid_principal_categoria`, enquanto diagnósticos com quatro caracteres aparecem em `cid_principal_subcategoria`. Por isso a consulta final verifica os dois campos.

Campos principais:

- `data_internacao`;
- `id_municipio_paciente`;
- `id_aih`;
- `cid_principal_categoria`;
- `cid_principal_subcategoria`.

Arquivo: `sql/01_internacoes_respiratorias.sql`.

Antes da integração, uma consulta independente verifica a cobertura mensal do SIH. A análise termina no último mês contínuo disponível. Na execução final, esse limite foi **novembro de 2025**.

## Queimadas

Fonte primária: **Programa Queimadas do INPE**.

Para manter comparabilidade temporal, são utilizados os arquivos anuais do **satélite de referência**. O INPE utiliza o AQUA_M-T como referência desde 2002.

A coleta final é feita diretamente nos arquivos anuais oficiais do INPE, e não pela consulta SQL intermediária usada nas primeiras versões do projeto.

O coletor suporta tanto o esquema histórico (`data_pas`, `foco_id`, `municipio`) quanto o esquema mais recente. Os totais anuais são comparados com uma série estadual de validação antes da modelagem.

Arquivo: `src/collect_inpe_official.py`.

## População

Fonte primária: **IBGE**.

A população anual é usada como denominador da taxa:

\[
Taxa = \frac{Internações}{População} \times 100000
\]

Não é feita interpolação silenciosa de população ausente.

## Meteorologia

Fonte: **NASA POWER**.

Parâmetros:

- `T2M`: temperatura do ar a 2 m;
- `RH2M`: umidade relativa a 2 m;
- `PRECTOTCORR`: precipitação corrigida.

A consulta usa a API mensal para o ponto correspondente à sede municipal. O valor mensal de `PRECTOTCORR` é mantido como média diária do mês no arquivo processado.

## Qualidade do ar

PM2.5 não foi incluído no modelo principal porque não foi identificada uma série pública e homogênea cobrindo os 62 municípios durante todo o período.

O projeto não preenche artificialmente períodos sem monitoramento.

## Data de extração

Execução final realizada em **setembro de 2026**.
