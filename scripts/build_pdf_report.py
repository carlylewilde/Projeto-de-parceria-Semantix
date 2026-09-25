from pathlib import Path
import math
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, KeepTogether, ListFlowable, ListItem
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'processed'
VIS = ROOT / 'visualizations'
OUT = ROOT / 'Relatorio_Final_Queimadas_Internacoes_Amazonas.pdf'
TMP = ROOT / '.report_tmp'
TMP.mkdir(exist_ok=True)

GREEN = colors.HexColor('#173F35')
GREEN2 = colors.HexColor('#2B6254')
ORANGE = colors.HexColor('#D97732')
LIGHT_GREEN = colors.HexColor('#EAF2EF')
LIGHT_ORANGE = colors.HexColor('#F9EFE7')
LIGHT_GRAY = colors.HexColor('#F3F5F4')
MID_GRAY = colors.HexColor('#65736F')
DARK = colors.HexColor('#202724')

metrics = pd.read_csv(DATA / 'metricas_modelos.csv')
baseline = pd.read_csv(DATA / 'metricas_baseline.csv').iloc[0]
importance = pd.read_csv(DATA / 'importancia_variaveis_random_forest.csv')
annual = pd.read_csv(DATA / 'resumo_anual.csv')
seasonal = pd.read_csv(DATA / 'resumo_sazonal.csv')
lags = pd.read_csv(DATA / 'correlacao_lags.csv')
sensitivity = pd.read_csv(DATA / 'sensibilidade_estacao_fogo.csv')
meta = pd.read_csv(DATA / 'metadados_cobertura.csv').iloc[0]
corr = pd.read_csv(DATA / 'correlacao_spearman.csv', index_col=0)
ablation = pd.read_csv(DATA / 'ablacao_focos.csv')

principal = metrics[(metrics['analise'] == 'principal') & (metrics['amostra'] == 'teste_2024_2025')]
lr = principal[principal['modelo'] == 'regressao_linear'].iloc[0]
rf = principal[principal['modelo'] == 'random_forest'].iloc[0]
rho = float(corr.loc['focos', 'taxa_internacoes_100k'])
lag2 = lags[lags['lag_meses'] == 2].iloc[0]
sens0 = sensitivity[sensitivity['lag_meses'] == 0].iloc[0]

# Valores consolidados documentados pelo projeto.
TOTAL_HOSP = 186529
TOTAL_FIRES = 162838
FIRE_SHARE = 85.7
PEAK_FIRES = 25499
PEAK_FIRE_YEAR = 2024
PEAK_HOSP = 24207
PEAK_HOSP_YEAR = 2023

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleGreen', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=27, leading=31, textColor=GREEN, alignment=TA_CENTER, spaceAfter=8))
styles.add(ParagraphStyle(name='Overline', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=ORANGE, alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name='SubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name='H1x', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=21, textColor=GREEN, spaceBefore=8, spaceAfter=9))
styles.add(ParagraphStyle(name='H2x', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=GREEN2, spaceBefore=8, spaceAfter=6))
styles.add(ParagraphStyle(name='Bodyx', parent=styles['BodyText'], fontName='Helvetica', fontSize=9.2, leading=13, textColor=DARK, spaceAfter=6))
styles.add(ParagraphStyle(name='Smallx', parent=styles['BodyText'], fontName='Helvetica', fontSize=7.8, leading=10, textColor=MID_GRAY, spaceAfter=4))
styles.add(ParagraphStyle(name='CallTitle', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=10, textColor=GREEN, spaceAfter=3))
styles.add(ParagraphStyle(name='CallBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=9, leading=12, textColor=DARK))
styles.add(ParagraphStyle(name='Captionx', parent=styles['BodyText'], fontName='Helvetica-Oblique', fontSize=7.7, leading=9.5, textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=7))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D6DEDA'))
    canvas.setLineWidth(0.4)
    canvas.line(1.8*cm, 1.15*cm, 19.2*cm, 1.15*cm)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(1.8*cm, 0.72*cm, 'Projeto EBAC / Semantix - Relatorio final - setembro de 2026')
    canvas.drawRightString(19.2*cm, 0.72*cm, f'{doc.page}')
    canvas.restoreState()


def p(text, style='Bodyx'):
    return Paragraph(text, styles[style])


def bullets(items):
    return ListFlowable([ListItem(p(x), leftIndent=12) for x in items], bulletType='bullet', leftIndent=18, bulletFontSize=6, spaceAfter=7)


def callout(title, body, fill=LIGHT_GREEN, border=GREEN):
    t = Table([[Paragraph(title, styles['CallTitle']), Paragraph(body, styles['CallBody'])]], colWidths=[4.0*cm, 12.4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), fill),
        ('BOX', (0,0), (-1,-1), 0.7, border),
        ('LINEBEFORE', (0,0), (0,-1), 4, border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


def kpis(items):
    cells = []
    for i, (value, label) in enumerate(items):
        cells.append(Paragraph(f'<font size="16" color="#173F35"><b>{value}</b></font><br/><font size="7.5" color="#65736F">{label}</font>', styles['Bodyx']))
    t = Table([cells], colWidths=[4.08*cm]*len(items))
    st = [('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('ALIGN',(0,0),(-1,-1),'CENTER'), ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#D7DEDB')), ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#D7DEDB')), ('TOPPADDING',(0,0),(-1,-1),9), ('BOTTOMPADDING',(0,0),(-1,-1),9)]
    for i in range(len(items)):
        st.append(('BACKGROUND',(i,0),(i,0), LIGHT_GREEN if i%2==0 else LIGHT_ORANGE))
    t.setStyle(TableStyle(st))
    return t


def savefig(fig, name):
    path = TMP / name
    fig.savefig(path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return path


def chart_annual():
    fig, ax1 = plt.subplots(figsize=(8.4,4.2))
    ax1.plot(annual['ano'], annual['focos_no_periodo_analisado'], marker='o', color='#D97732', label='Focos')
    ax1.set_ylabel('Focos de queimadas', color='#D97732')
    ax1.tick_params(axis='y', labelcolor='#D97732')
    ax1.grid(alpha=.2)
    ax2 = ax1.twinx()
    ax2.plot(annual['ano'], annual['internacoes'], marker='s', color='#173F35', label='Internacoes')
    ax2.set_ylabel('Internacoes respiratorias', color='#173F35')
    ax2.tick_params(axis='y', labelcolor='#173F35')
    ax1.set_title('Resumo anual no periodo comum de analise')
    return savefig(fig, 'annual.png')


def chart_seasonal():
    fig, ax1 = plt.subplots(figsize=(8.1,4.0))
    ax1.plot(seasonal['mes'], seasonal['focos_medios'], marker='o', color='#D97732')
    ax1.set_xlabel('Mes')
    ax1.set_ylabel('Focos medios', color='#D97732')
    ax1.tick_params(axis='y', labelcolor='#D97732')
    ax1.set_xticks(range(1,13))
    ax1.grid(alpha=.2)
    ax2 = ax1.twinx()
    ax2.plot(seasonal['mes'], seasonal['taxa_media_100k'], marker='s', color='#173F35')
    ax2.set_ylabel('Taxa media por 100 mil', color='#173F35')
    ax2.tick_params(axis='y', labelcolor='#173F35')
    ax1.set_title('Sazonalidade media')
    return savefig(fig, 'seasonal.png')


def chart_models():
    values = [baseline['R2'], lr['R2'], rf['R2']]
    labels = ['Baseline', 'Regressao\nLinear', 'Random\nForest']
    fig, ax = plt.subplots(figsize=(6.6,3.8))
    bars = ax.bar(labels, values, color=['#A9B8B3','#2B6254','#D97732'])
    ax.axhline(0, color='#555', lw=.8)
    ax.set_ylabel('R2 no teste 2024-2025')
    ax.set_title('Desempenho preditivo fora da amostra')
    for bar, val in zip(bars, values):
        ax.text(bar.get_x()+bar.get_width()/2, val+0.003, f'{val:.3f}', ha='center', va='bottom', fontsize=9)
    ax.set_ylim(min(-0.02, min(values)-.02), max(values)+.035)
    return savefig(fig, 'models.png')


def chart_lags():
    fig, ax = plt.subplots(figsize=(7.4,3.8))
    ax.bar(lags['lag_meses'].astype(str), lags['rho_spearman'], color='#2B6254')
    ax.axhline(0, color='#555', lw=.8)
    ax.set_xlabel('Defasagem dos focos (meses)')
    ax.set_ylabel('rho de Spearman')
    ax.set_title('Correlacao estadual com defasagens')
    return savefig(fig, 'lags.png')


def chart_sensitivity():
    fig, ax = plt.subplots(figsize=(7.4,3.8))
    ax.bar(sensitivity['lag_meses'].astype(str), sensitivity['rho_spearman'], color='#D97732')
    ax.axhline(0, color='#555', lw=.8)
    ax.set_xlabel('Defasagem dos focos (meses)')
    ax.set_ylabel('rho de Spearman')
    ax.set_title('Sensibilidade: agosto a novembro')
    return savefig(fig, 'sensitivity.png')


def chart_importance():
    top = importance.head(9).sort_values('importancia')
    fig, ax = plt.subplots(figsize=(7.6,4.2))
    ax.barh(top['grupo'], top['importancia'], color='#2B6254')
    ax.set_xlabel('Importancia relativa')
    ax.set_title('Random Forest - importancia das variaveis')
    return savefig(fig, 'importance.png')


def img(path, width=15.7*cm):
    return Image(str(path), width=width, height=width*0.51)


def metric_table():
    data = [
        ['Modelo','MAE','RMSE','R2'],
        ['Regressao Linear', f"{lr['MAE']:.2f}", f"{lr['RMSE']:.2f}", f"{lr['R2']:.3f}"],
        ['Random Forest', f"{rf['MAE']:.2f}", f"{rf['RMSE']:.2f}", f"{rf['R2']:.3f}"],
        ['Baseline municipio x mes', f"{baseline['MAE']:.2f}", f"{baseline['RMSE']:.2f}", f"{baseline['R2']:.3f}"],
    ]
    t=Table(data, colWidths=[7.0*cm,3.0*cm,3.0*cm,3.0*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),GREEN),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('ALIGN',(1,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),.45,colors.HexColor('#D0D8D5')),('BACKGROUND',(0,2),(-1,2),LIGHT_GREEN),('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),8.5),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)
    ]))
    return t

annual_png = chart_annual()
seasonal_png = chart_seasonal()
models_png = chart_models()
lags_png = chart_lags()
sens_png = chart_sensitivity()
importance_png = chart_importance()

story=[]
# Cover
story += [Spacer(1,1.7*cm), p('RELATORIO FINAL DO PROJETO','Overline'), p('Queimadas, clima e internacoes<br/>respiratorias no Amazonas','TitleGreen'), p('Analise de dados e modelagem preditiva - 2015 a 2025','SubTitle'), Spacer(1,.3*cm), kpis([('62','municipios'),('8.122','observacoes'),('186.529','internacoes'),('162.838','focos')]), Spacer(1,1.2*cm), p('Projeto de parceria / portfolio - EBAC + Semantix','SubTitle'), Spacer(1,.6*cm), p('<b>Repositorio publico</b>','Bodyx'), p('<link href="https://github.com/carlylewilde/Projeto-de-parceria-Semantix" color="#2B6254">github.com/carlylewilde/Projeto-de-parceria-Semantix</link>','Smallx'), Spacer(1,1.4*cm), p('Manaus - AM | Setembro de 2026','SubTitle'), PageBreak()]

story += [p('Resumo executivo','H1x'), callout('Pergunta do projeto','Existe associacao entre focos de queimadas, condicoes meteorologicas e internacoes por doencas do aparelho respiratorio entre residentes dos municipios do Amazonas?'), Spacer(1,.25*cm), p('A analise integrou internacoes do SIH/SUS, focos do satelite de referencia do INPE, populacao do IBGE e meteorologia da NASA POWER. A unidade de analise foi municipio x mes, cobrindo os 62 municipios entre janeiro de 2015 e novembro de 2025.'), kpis([('0,012','Spearman municipio-mes'),('0,084','melhor R2 no teste'),('85,7%','focos entre ago-nov'),('25.499','focos em 2024')]), Spacer(1,.25*cm), callout('Resultado principal','A contagem mensal municipal de focos nao apresentou relacao simples nem ganho preditivo robusto para explicar as internacoes respiratorias. Isso nao implica ausencia de efeito da fumaca; a contagem de focos e uma proxy limitada de exposicao humana.', LIGHT_ORANGE, ORANGE), Spacer(1,.35*cm), p('Como a entrega atende ao enunciado','H2x'), bullets(['Visualizacao de dados: dashboard HTML e graficos do projeto.','Entrega via GitHub: repositorio publico com codigo e resultados.','Documentacao: Markdown e este PDF consolidado.','Topicos obrigatorios: coleta de dados, modelagem e conclusoes.']), PageBreak()]

story += [p('1. Problema, objetivo e escopo','H1x'), p('Queimadas sao recorrentes no Amazonas e geram episodios de fumaca com potencial impacto sobre a saude respiratoria. O objetivo foi avaliar se a variacao temporal e espacial dos focos, combinada a fatores meteorologicos, ajuda a explicar ou prever internacoes por doencas do aparelho respiratorio.'), p('Escopo analitico','H2x'), bullets(['62 municipios do Amazonas.','Janeiro de 2015 a novembro de 2025.','Internacoes com diagnostico principal CID-10 J00-J99.','Unidade de analise: municipio x mes.','Exposicao principal: focos do satelite de referencia do INPE.','Covariaveis: temperatura, umidade, precipitacao, populacao, sazonalidade e indicador 2020-2022.']), callout('Associacao nao e causalidade','O projeto avalia associacao estatistica e capacidade preditiva. Ele nao estima quantas internacoes foram causadas pelas queimadas.', colors.HexColor('#F7ECEA'), colors.HexColor('#A6423A')), Spacer(1,.35*cm), img(annual_png), p('Figura 1. Resumo anual de focos e internacoes no periodo comum de analise.','Captionx'), PageBreak()]

story += [p('2. Coleta de dados','H1x'), p('O projeto combinou quatro fontes publicas principais, priorizando comparabilidade temporal, cobertura estadual e reprodutibilidade.'), Table([['Fonte','Variavel','Uso'],['SIH/SUS / DATASUS','Internacoes J00-J99','Desfecho de saude'],['INPE Queimadas','Focos de calor','Exposicao principal'],['IBGE','Populacao municipal','Taxa por 100 mil'],['NASA POWER','T2M, RH2M, PRECTOTCORR','Meteorologia']], colWidths=[5.0*cm,5.5*cm,5.5*cm], style=[('BACKGROUND',(0,0),(-1,0),GREEN),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D0D8D5')),('FONTSIZE',(0,0),(-1,-1),8.5),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]), p('SIH/SUS','H2x'), p('A variavel de saude e o numero de internacoes com diagnostico principal J00-J99. O municipio e o de residencia do paciente. A consulta final verifica campos de categoria e subcategoria do CID, reduzindo risco de subestimacao dos diagnosticos de quatro caracteres. A cobertura mensal foi validada e o ultimo mes continuo disponivel foi novembro de 2025.'), p('INPE','H2x'), p('Os focos foram coletados dos arquivos anuais oficiais do Programa Queimadas, usando o satelite de referencia para manter comparabilidade temporal. Os totais anuais foram comparados com uma serie estadual de validacao antes da modelagem.'), p('IBGE e NASA POWER','H2x'), p('A populacao anual foi usada como denominador da taxa. A NASA POWER forneceu temperatura, umidade relativa e precipitacao mensal para a sede de cada municipio.'), callout('Taxa utilizada','Taxa de internacoes = (internacoes respiratorias / populacao) x 100.000'), PageBreak()]

story += [p('3. Tratamento e integracao','H1x'), p('As fontes foram padronizadas por municipio e mes e integradas em um painel balanceado.'), bullets(['Padronizacao dos codigos municipais.','Grade completa municipio x mes.','Zero apenas em meses cuja cobertura da fonte foi confirmada.','Interrupcao do pipeline diante de lacunas internas ou dados essenciais ausentes.','Defasagens dos focos em 1, 2 e 3 meses.','Variaveis sazonais seno/cosseno e indicador para 2020-2022.']), kpis([('131','meses continuos'),('62','municipios'),('8.122','municipio-mes'),('2025-11','ultimo mes SIH')]), Spacer(1,.4*cm), p('Controle de qualidade','H2x'), p('A validacao foi parte do pipeline. A serie de queimadas foi conferida contra totais anuais estaduais; a serie de saude foi checada para cobertura mensal continua. O projeto nao cria zeros artificiais para meses finais ainda nao publicados.'), PageBreak()]

story += [p('4. Analise exploratoria','H1x'), p('A analise exploratoria avaliou tendencia, sazonalidade, valores extremos e relacoes entre queimadas, meteorologia e internacoes.'), img(seasonal_png), p('Figura 2. Sazonalidade media de focos e taxa de internacoes.','Captionx'), p(f'Os focos se concentram no periodo seco: {FIRE_SHARE:.1f}% ocorreram entre agosto e novembro. A taxa media de internacoes atinge seu pico em outro periodo do ano, criando um desalinhamento sazonal importante.'), p('Correlacao contemporanea','H2x'), callout('Spearman municipio-mes',f'A correlacao entre focos e taxa de internacoes foi rho = {rho:.3f}, praticamente nula.'), p('Uma correlacao simples pode esconder padroes sazonais e espaciais distintos. Por isso foram avaliadas defasagens e um recorte especifico da estacao de fogo.'), PageBreak()]

story += [p('4.1 Defasagens e sensibilidade sazonal','H1x'), img(lags_png), p('Figura 3. Correlacao estadual entre focos e taxa de internacoes com defasagens.','Captionx'), p(f'A maior magnitude ocorreu com dois meses de defasagem, rho = {lag2["rho_spearman"]:.3f}. O sinal negativo nao deve ser interpretado como efeito protetor: ele e compativel com o desalinhamento sazonal entre fogo e internacoes.'), Spacer(1,.2*cm), img(sens_png), p('Figura 4. Sensibilidade restrita a agosto-novembro.','Captionx'), callout('Leitura da sensibilidade',f'No recorte agosto-novembro, a associacao contemporanea muda para rho = {sens0["rho_spearman"]:.3f}. O sinal depende do recorte sazonal e nao sustenta inferencia causal.', LIGHT_ORANGE, ORANGE), PageBreak()]

story += [p('5. Modelagem','H1x'), p('Foram usados Regressao Linear e Random Forest Regressor. A variavel alvo foi a taxa mensal de internacoes respiratorias por 100 mil habitantes.'), p('Variaveis explicativas','H2x'), bullets(['focos no mes e defasagens de 1, 2 e 3 meses;','temperatura, umidade e precipitacao;','seno e cosseno do mes;','populacao;','indicador 2020-2022;','municipio como variavel categorica.']), p('Divisao temporal','H2x'), bullets(['Treinamento: 2015-2022.','Validacao: 2023.','Teste: janeiro/2024 a novembro/2025.','Apos validacao, reajuste com 2015-2023 e avaliacao no teste.']), metric_table(), Spacer(1,.35*cm), img(models_png, 13.5*cm), p('Figura 5. R2 dos modelos no periodo de teste.','Captionx'), PageBreak()]

story += [p('6. Resultados dos modelos','H1x'), callout('Melhor modelo',f'O Random Forest obteve R2 = {rf["R2"]:.3f}, MAE = {rf["MAE"]:.2f} e RMSE = {rf["RMSE"]:.2f}. A melhora sobre a Regressao Linear e o baseline foi pequena.', LIGHT_ORANGE, ORANGE), p('O baixo R2 fora da amostra indica que a maior parte da variacao mensal das taxas municipais permanece sem explicacao pelo conjunto de variaveis usado. Isso e um resultado substantivo e deve ser reportado sem inflar a capacidade do modelo.'), img(importance_png, 14.5*cm), p('Figura 6. Importancia relativa das variaveis no Random Forest.','Captionx'), p('As variaveis ligadas a municipio e populacao concentraram a maior parcela da importancia. Meteorologia teve peso relevante, enquanto focos e suas defasagens tiveram participacao menor. Importancia de variavel nao representa efeito causal.'), PageBreak()]

abla_rows=[['Modelo','Variante','MAE','RMSE','R2']]
for _,r in ablation.iterrows():
    abla_rows.append([r['modelo'].replace('_',' ').title(), r['variante'].replace('_',' '), f"{r['MAE']:.2f}", f"{r['RMSE']:.2f}", f"{r['R2']:.3f}"])
abla_table=Table(abla_rows, colWidths=[4.7*cm,3.2*cm,2.8*cm,2.8*cm,2.8*cm])
abla_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),GREEN),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D0D8D5')),('FONTSIZE',(0,0),(-1,-1),8.2),('ALIGN',(2,0),(-1,-1),'CENTER'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story += [p('6.1 Analise de ablacao','H1x'), p('Os modelos foram treinados novamente sem focos e suas tres defasagens para testar se essas variaveis acrescentavam sinal preditivo.'), abla_table, Spacer(1,.35*cm), callout('Resultado da ablacao','Retirar as variaveis de focos nao piorou de forma consistente o desempenho. No Random Forest, a versao sem focos teve R2 ligeiramente maior, embora com MAE discretamente pior. Os focos nao adicionaram ganho preditivo robusto neste desenho.'), p('Comportamento anual','H2x'), bullets([f'Maior numero anual de focos: {PEAK_FIRES:,} em {PEAK_FIRE_YEAR}.'.replace(',','.'), f'Maior numero anual de internacoes no recorte: {PEAK_HOSP:,} em {PEAK_HOSP_YEAR}.'.replace(',','.'), 'Em 2025, a serie anual completa teve 4.545 focos, reducao de aproximadamente 82,2% frente a 2024.']), PageBreak()]

story += [p('7. Conclusoes','H1x'), callout('Conclusao central','Nao foi identificada uma relacao simples e estavel entre a contagem mensal de focos de queimadas e a taxa municipal de internacoes J00-J99. Os modelos tambem apresentaram baixo poder preditivo fora da amostra.'), p('A correlacao municipio-mes foi praticamente nula. As correlacoes estaduais com defasagem tiveram sinal negativo, mas a analise sazonal mostra que queimadas e internacoes atingem picos em momentos diferentes do ano. Quando o recorte e restrito aos meses de maior atividade do fogo, a associacao muda de sinal.'), p('A conclusao adequada nao e que queimadas sejam inofensivas. Os resultados mostram que a contagem mensal de focos por municipio, isoladamente, e uma proxy limitada da exposicao humana a fumaca.'), p('O que o projeto demonstrou','H2x'), bullets(['Forte sazonalidade das queimadas.','Sazonalidade das internacoes com pico em periodo diferente do fogo.','Associacao contemporanea municipio-mes proxima de zero.','Baixo poder preditivo no teste temporal.','Pouco ganho preditivo ao incluir contagem de focos e lags.','Importancia de separar associacao, previsao e causalidade.']), callout('Resposta a pergunta do projeto','Ha padroes temporais e sazonais relacionados, mas os dados e a granularidade usados nao sustentam uma relacao simples nem uma previsao robusta das internacoes a partir da contagem mensal de focos.', LIGHT_ORANGE, ORANGE), PageBreak()]

story += [p('8. Limitacoes e proximos passos','H1x'), p('Limitacoes','H2x'), bullets(['O SIH/SUS nao cobre integralmente a assistencia exclusivamente privada.','AIH nao equivale necessariamente a pessoa unica.','Foco de satelite e deteccao termica, nao concentracao de fumaca respirada.','A fumaca pode atravessar limites municipais.','Nao ha serie homogenea de PM2.5 para os 62 municipios durante todo o periodo.','A resolucao mensal pode diluir efeitos de poucos dias.','J00-J99 reune doencas com sazonalidades distintas.','A meteorologia representa a sede municipal, nao toda a area territorial.','Fatores de confusao como idade, renda, tabagismo, acesso a saude e circulacao viral nao sao totalmente controlados.']), p('Proximos passos','H2x'), bullets(['Usar resolucao diaria ou semanal.','Incluir PM2.5 e direcao/velocidade do vento.','Estratificar por faixa etaria e grupos de CID.','Avaliar modelos Poisson e Binomial Negativa.','Incorporar defasagens distribuidas e metodos epidemiologicos para autocorrelacao temporal.']), PageBreak()]

story += [p('9. Referencias e reprodutibilidade','H1x'), p('Fontes de dados','H2x'), bullets(['INPE - Programa Queimadas / Dados Abertos.','DATASUS - Informacoes de Saude / TABNET.','Base dos Dados - SIH/SUS.','IBGE - Estimativas da populacao.','NASA POWER - Monthly and Annual API.','geobr - dados espaciais oficiais do Brasil.']), p('Literatura cientifica','H2x'), bullets(['Sacramento, D. S. et al. (2020). Atmospheric Pollution and Hospitalization for Cardiovascular and Respiratory Diseases in the City of Manaus from 2008 to 2012. DOI 10.1155/2020/8458359.','Requia, W. J. et al. (2021). Health impacts of wildfire-related air pollution in Brazil. Nature Communications, 12, 6555.','Campanharo, W. A. et al. (2022). Hospitalization Due to Fire-Induced Pollution in the Brazilian Legal Amazon from 2005 to 2018. Remote Sensing, 14(1), 69.','Amazon Wildfires and Respiratory Health: Impacts during the Forest Fire Season from 2009 to 2019 (2024).','Tadano, Y. S. et al. (2024). Predicting health impacts of wildfire smoke in Amazonas basin, Brazil. Chemosphere, 367, 143688.']), p('Repositorio','H2x'), p('<link href="https://github.com/carlylewilde/Projeto-de-parceria-Semantix" color="#2B6254">https://github.com/carlylewilde/Projeto-de-parceria-Semantix</link>'), callout('Entrega final','Este PDF consolida a documentacao solicitada - coleta de dados, modelagem e conclusoes - e complementa a visualizacao entregue via GitHub.', LIGHT_ORANGE, ORANGE)]

doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=1.8*cm, leftMargin=1.8*cm, topMargin=1.55*cm, bottomMargin=1.45*cm, title='Queimadas, clima e internacoes respiratorias no Amazonas', author='Projeto EBAC / Semantix')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f'PDF criado: {OUT}')
