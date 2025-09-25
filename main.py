import pandas as pd
import plotly.express as px
import os
import panel as pn

# --- Configuração da Página e Tema ---
pn.extension('plotly', template='fast')

# --- Carregamento e Processamento de Dados ---
# A função de carregamento é a mesma, otimizada com cache do Panel
@pn.cache
def carregar_e_combinar_dados():
    """
    Carrega todos os dados (voos, aeroportos, companhias) e os combina
    em um único DataFrame limpo e enriquecido.
    """
    print("Iniciando o carregamento e combinação dos dados...")
    
    arquivos_vra = ['dataset/VRA2022.csv', 'dataset/VRA2023.csv', 'dataset/VRA2024.csv']
    lista_dfs = []
    for f in arquivos_vra:
        if os.path.exists(f):
            try:
                df_temp = pd.read_csv(f, sep=';', encoding='utf-8', na_values=['null', 'NULL'], dtype={'Código Justificativa': str})
                if not df_temp.empty:
                    lista_dfs.append(df_temp)
            except Exception as e:
                print(f"ERRO ao ler o ficheiro {f}: {e}")
        else:
            print(f"AVISO: Ficheiro {f} não encontrado.")

    if not lista_dfs:
        return pd.DataFrame()

    df_voos = pd.concat(lista_dfs, ignore_index=True)
    df_voos = df_voos.rename(columns={
        'ICAO Empresa Aérea': 'icao_empresa_aerea',
        'ICAO Aeródromo Origem': 'aerodromo_origem',
        'Partida Prevista': 'partida_prevista',
        'Partida Real': 'partida_real',
        'Situação Voo': 'situacao_voo'
    })

    caminho_aeroportos = 'dataset/codes/airport-codes.csv'
    if os.path.exists(caminho_aeroportos):
        df_aeroportos = pd.read_csv(caminho_aeroportos, sep=';')
        df_aeroportos = df_aeroportos.rename(columns={'ident': 'icao_code', 'name': 'aeroporto_nome'})
        df_voos = pd.merge(df_voos, df_aeroportos[['icao_code', 'aeroporto_nome']], left_on='aerodromo_origem', right_on='icao_code', how='left')
    else:
        df_voos['aeroporto_nome'] = df_voos['aerodromo_origem']

    caminho_cias = 'dataset/codes/airlines-codes.csv'
    if os.path.exists(caminho_cias):
        df_cias = pd.read_csv(caminho_cias, sep=';')
        df_cias = df_cias.rename(columns={'ICAO': 'icao_code', 'Name': 'cia_aerea_nome'})
        df_voos = pd.merge(df_voos, df_cias[['icao_code', 'cia_aerea_nome']], left_on='icao_empresa_aerea', right_on='icao_code', how='left')
    else:
        df_voos['cia_aerea_nome'] = df_voos['icao_empresa_aerea']

    df_voos['partida_prevista'] = pd.to_datetime(df_voos['partida_prevista'], format='%d/%m/%Y %H:%M', errors='coerce')
    df_voos['partida_real'] = pd.to_datetime(df_voos['partida_real'], format='%d/%m/%Y %H:%M', errors='coerce')
    df_voos['atraso_minutos'] = (df_voos['partida_real'] - df_voos['partida_prevista']).dt.total_seconds() / 60
    df_voos['atrasado'] = (df_voos['atraso_minutos'] > 15)
    df_voos['ano'] = df_voos['partida_prevista'].dt.year.astype('Int64')
    
    print("Processamento de dados concluído.")
    return df_voos

df_completo = carregar_e_combinar_dados()

# --- Widgets da Barra Lateral (Filtros) ---
if not df_completo.empty:
    anos_disponiveis = sorted(df_completo['ano'].dropna().unique().tolist())
    ano_selecionado = pn.widgets.MultiSelect(name="Ano:", options=anos_disponiveis, value=anos_disponiveis)

    cias_disponiveis = sorted(df_completo['cia_aerea_nome'].dropna().unique().tolist())
    cia_selecionada = pn.widgets.MultiSelect(name="Companhia Aérea:", options=cias_disponiveis, value=[])
else:
    # Se não houver dados, exibe uma mensagem de erro
    pn.pane.Alert("Nenhum dado foi carregado. Verifique a pasta 'dataset' e os ficheiros CSV.", alert_type='danger').servable()


# --- Funções Reativas para Gerar Gráficos e Métricas ---
# O decorator @pn.depends liga os widgets às funções.
# Sempre que o valor de um widget mudar, a função é executada novamente.
@pn.depends(ano_selecionado.param.value, cia_selecionada.param.value)
def get_df_filtrado(anos, cias):
    df_filtrado = df_completo[df_completo['ano'].isin(anos)]
    if cias:
        df_filtrado = df_filtrado[df_filtrado['cia_aerea_nome'].isin(cias)]
    return df_filtrado

def get_metricas(df):
    total_voos = df.shape[0]
    total_atrasos = int(df['atrasado'].sum())
    percentual_atrasos = (total_atrasos / total_voos * 100) if total_voos > 0 else 0
    return {
        'total_voos': f"{total_voos:,}".replace(",", "."),
        'total_atrasos': f"{total_atrasos:,}".replace(",", "."),
        'percentual_atrasos': f"{percentual_atrasos:.2f}%"
    }

def plot_top_aeroportos(df):
    df_atrasos = df[df['atrasado']]
    top_10 = df_atrasos['aeroporto_nome'].value_counts().nlargest(10).sort_values(ascending=True)
    fig = px.bar(top_10, x=top_10.values, y=top_10.index, orientation='h', labels={'x': '', 'y': ''}, text=top_10.values)
    return fig

def plot_voos_por_cia(df):
    voos_por_cia = df['cia_aerea_nome'].value_counts().nlargest(10).sort_values(ascending=True)
    fig = px.bar(voos_por_cia, x=voos_por_cia.values, y=voos_por_cia.index, orientation='h', labels={'x': '', 'y': ''}, text=voos_por_cia.values)
    fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
    return fig

def plot_evolucao_mensal(df):
    voos_por_mes = df.set_index('partida_prevista').resample('M').size().reset_index(name='contagem')
    fig = px.line(voos_por_mes, x='partida_prevista', y='contagem', labels={'partida_prevista': 'Mês', 'contagem': 'Número de Voos'}, markers=True)
    return fig

# --- Layout do Dashboard ---
metricas_reativas = pn.bind(get_metricas, df=get_df_filtrado)

# Cria os indicadores numéricos (métricas)
total_voos_indicator = pn.indicators.Number(name='Total de Voos', value=metricas_reativas.get('total_voos'), format='{value}')
total_atrasos_indicator = pn.indicators.Number(name='Total de Atrasos (>15 min)', value=metricas_reativas.get('total_atrasos'), format='{value}')
percentual_atrasos_indicator = pn.indicators.Number(name='Percentual de Atrasos', value=metricas_reativas.get('percentual_atrasos'), format='{value}')

# Define o layout da aplicação
dashboard = pn.template.FastListTemplate(
    site="✈️ Análise de Voos e Atrasos",
    title="Dashboard da Aviação Brasileira",
    sidebar=[
        pn.pane.Markdown("### Filtros do Dashboard"),
        ano_selecionado,
        cia_selecionada
    ],
    main=[
        pn.Row(total_voos_indicator, total_atrasos_indicator, percentual_atrasos_indicator),
        pn.Row(
            pn.Column(
                pn.pane.Markdown("### Top 10 Aeroportos com Mais Atrasos"),
                pn.pane.Plotly(pn.bind(plot_top_aeroportos, df=get_df_filtrado))
            ),
            pn.Column(
                pn.pane.Markdown("### Top 10 Voos por Companhia Aérea"),
                pn.pane.Plotly(pn.bind(plot_voos_por_cia, df=get_df_filtrado))
            )
        ),
        pn.Column(
            pn.pane.Markdown("### Evolução Mensal de Voos"),
            pn.pane.Plotly(pn.bind(plot_evolucao_mensal, df=get_df_filtrado))
        )
    ]
)

# Torna o dashboard "servível" para que possa ser executado
dashboard.servable()