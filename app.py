import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Dashboard de Aviação")


# --- Carregamento e Processamento de Dados ---
@st.cache_data # Otimizador do Streamlit: executa esta função apenas uma vez se os ficheiros não mudarem
def carregar_e_combinar_dados():
    """
    Carrega todos os dados (voos, aeroportos, companhias) e os combina
    em um único DataFrame limpo e enriquecido.
    """
    print("Iniciando o carregamento e combinação dos dados...")
    
    # 1. Carregar Dados de Voos
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

    # 2. Carregar Códigos de Aeroportos (o ficheiro que enviou)
    caminho_aeroportos = 'dataset/codes/airport-codes.csv'
    if os.path.exists(caminho_aeroportos):
        df_aeroportos = pd.read_csv(caminho_aeroportos, sep=';')
        df_aeroportos = df_aeroportos.rename(columns={'ident': 'icao_code', 'name': 'aeroporto_nome', 'municipality': 'aeroporto_cidade'})
        # Combina (merge) os dados de voos com os nomes dos aeroportos
        df_voos = pd.merge(
            df_voos, 
            df_aeroportos[['icao_code', 'aeroporto_nome', 'aeroporto_cidade']], 
            left_on='aerodromo_origem', 
            right_on='icao_code', 
            how='left'
        )
    else:
        print("AVISO: airport-codes.csv não encontrado. Os nomes dos aeroportos não serão exibidos.")
        df_voos['aeroporto_nome'] = df_voos['aerodromo_origem'] 

    # 3. Carregar Códigos de Companhias Aéreas (o outro ficheiro que enviou)
    caminho_cias = 'dataset/codes/airlines-codes.csv'
    if os.path.exists(caminho_cias):
        df_cias = pd.read_csv(caminho_cias, sep=';')
        df_cias = df_cias.rename(columns={'ICAO': 'icao_code', 'Name': 'cia_aerea_nome'})
        # Combina (merge) os dados de voos com os nomes das companhias
        df_voos = pd.merge(
            df_voos,
            df_cias[['icao_code', 'cia_aerea_nome']],
            left_on='icao_empresa_aerea',
            right_on='icao_code',
            how='left'
        )
    else:
        print("AVISO: airlines-codes.csv não encontrado. Os nomes das companhias não serão exibidos.")
        df_voos['cia_aerea_nome'] = df_voos['icao_empresa_aerea']


    # 4. Limpeza e Processamento Final
    df_voos['partida_prevista'] = pd.to_datetime(df_voos['partida_prevista'], format='%d/%m/%Y %H:%M', errors='coerce')
    df_voos['partida_real'] = pd.to_datetime(df_voos['partida_real'], format='%d/%m/%Y %H:%M', errors='coerce')
    df_voos['atraso_minutos'] = (df_voos['partida_real'] - df_voos['partida_prevista']).dt.total_seconds() / 60
    df_voos['atrasado'] = (df_voos['atraso_minutos'] > 15)
    df_voos['ano'] = df_voos['partida_prevista'].dt.year.astype('Int64')
    
    print("Processamento de dados concluído.")
    return df_voos

df_completo = carregar_e_combinar_dados()

# --- Barra Lateral (Filtros) ---
st.sidebar.header("Filtros do Dashboard")

if df_completo.empty:
    st.error("Nenhum dado de voo foi carregado. Verifique a pasta 'dataset' e os ficheiros CSV.")
    st.stop()

# Filtro de Anos
anos_disponiveis = sorted(df_completo['ano'].dropna().unique().tolist())
ano_selecionado = st.sidebar.multiselect("Ano:", options=anos_disponiveis, default=anos_disponiveis)

# Filtro de Companhias Aéreas
cias_disponiveis = sorted(df_completo['cia_aerea_nome'].dropna().unique().tolist())
cia_selecionada = st.sidebar.multiselect("Companhia Aérea:", options=cias_disponiveis, default=[])

# Aplicação dos filtros
df_filtrado = df_completo[df_completo['ano'].isin(ano_selecionado)]
if cia_selecionada: 
    df_filtrado = df_filtrado[df_filtrado['cia_aerea_nome'].isin(cia_selecionada)]


# --- Layout do Dashboard ---
st.title("✈️ Análise de Voos e Atrasos na Aviação Brasileira")
st.markdown("---")

# Métricas Principais
total_voos = df_filtrado.shape[0]
total_atrasos = int(df_filtrado['atrasado'].sum())
percentual_atrasos = (total_atrasos / total_voos * 100) if total_voos > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total de Voos", f"{total_voos:,}".replace(",", "."))
col2.metric("Total de Atrasos (>15 min)", f"{total_atrasos:,}".replace(",", "."))
col3.metric("Percentual de Atrasos", f"{percentual_atrasos:.2f}%")
st.markdown("---")

# Gráficos em Colunas
c1, c2 = st.columns((7, 3))

with c1:
    st.subheader("Top 10 Aeroportos de Origem com Mais Atrasos")
    df_atrasos = df_filtrado[df_filtrado['atrasado']]
    top_10_aeroportos = df_atrasos['aeroporto_nome'].value_counts().nlargest(10).sort_values(ascending=True)
    
    fig_top_10 = px.bar(
        top_10_aeroportos, x=top_10_aeroportos.values, y=top_10_aeroportos.index,
        orientation='h', labels={'x': 'Número de Voos Atrasados', 'y': 'Aeroporto'},
        text=top_10_aeroportos.values
    )
    st.plotly_chart(fig_top_10, use_container_width=True)

with c2:
    st.subheader("Voos por Companhia Aérea")
    voos_por_cia = df_filtrado['cia_aerea_nome'].value_counts().nlargest(10)
    fig_cia = px.pie(
        voos_por_cia, values=voos_por_cia.values, names=voos_por_cia.index,
        hole=.4
    )
    st.plotly_chart(fig_cia, use_container_width=True)

st.subheader("Evolução Mensal de Voos")
voos_por_mes = df_filtrado.set_index('partida_prevista').resample('M').size().reset_index(name='contagem')
fig_evolucao = px.line(
    voos_por_mes, x='partida_prevista', y='contagem',
    labels={'partida_prevista': 'Mês', 'contagem': 'Número de Voos'},
    markers=True
)
st.plotly_chart(fig_evolucao, use_container_width=True)