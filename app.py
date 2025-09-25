import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
sns.set_style("darkgrid")

# ----------- CONFIGURAÇÃO DA PÁGINA -----------
st.set_page_config(
    page_title="Painel Dark de Voos no Brasil",
    page_icon="🌌",
    layout="wide"
)

# ----------- CSS DARK + CARDS (INCLUI HOVER) -----------
st.markdown("""
<style>
/* Fundo escuro geral */
body, .stApp {
    background-color: #0E1117;
    color: #FAFAFA;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #121418;
}

/* Títulos */
h1, h2, h3, h4 {
    color: #00C9A7 !important;
}

/* Cards de métricas */
.metric-container {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 18px;
}
.metric-card {
    flex: 1;
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    font-weight: 700;
    font-size: 16px;
    color: white;
    transition: transform 0.14s ease-in-out, box-shadow 0.14s ease-in-out;
    min-height: 72px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.metric-card:hover {
    transform: translateY(-6px);
    box-shadow: 0px 10px 30px rgba(0,0,0,0.5);
}
.blue-card { background: linear-gradient(90deg, #1f77b4 0%, #2a9df4 100%); }
.green-card { background: linear-gradient(90deg, #2ca02c 0%, #66d07a 100%); }
.red-card { background: linear-gradient(90deg, #d62728 0%, #ff6b6b 100%); }

/* Forçando textos de inputs a branco */
.stTextInput input, .stSelectbox, .stMultiSelect, .stNumberInput input {
    color: #ffffff;
}

/* Pequeno ajuste nos títulos de seções */
h1 { font-size: 28px; }
h2 { font-size: 20px; }
</style>
""", unsafe_allow_html=True)

# ----------- FUNÇÃO DE CARREGAMENTO (COM CACHE) -----------
@st.cache_data
def carregar_dados():
    arquivos = {
        2022: 'dataset/VRA2022.csv',
        2023: 'dataset/VRA2023.csv',
        2024: 'dataset/VRA2024.csv',
    }
    lista_de_dfs = []
    for ano, caminho in arquivos.items():
        try:
            df_temp = pd.read_csv(caminho, sep=';', encoding='utf-8', dtype={'Código Justificativa': str})
            df_temp['ano'] = ano
            lista_de_dfs.append(df_temp)
        except FileNotFoundError:
            # ignora arquivo ausente
            pass
        except Exception as e:
            # se der outro erro, tenta continuar e registra
            print(f"Erro lendo {caminho}: {e}")
            pass

    if not lista_de_dfs:
        # não encontro dados, interrompe a execução com mensagem amigável
        st.error("⚠️ Nenhum arquivo de dados (VRA2022/2023/2024) foi encontrado na pasta `dataset/`. Coloque os CSVs e recarregue.")
        st.stop()

    df_completo = pd.concat(lista_de_dfs, ignore_index=True)

    # tenta carregar nomes de aeroportos (opcional)
    try:
        df_aeroportos = pd.read_csv('dataset/codes/airport-codes.csv', sep=';', encoding='latin1')
        df_nomes_aeroportos = df_aeroportos[df_aeroportos['iso_country'] == 'BR'][['ident', 'name']].copy()
    except Exception:
        df_nomes_aeroportos = pd.DataFrame(columns=['ident', 'name'])

    # tenta carregar nomes das companhias (opcional)
    try:
        df_airlines = pd.read_csv('dataset/codes/airlines-codes.csv', sep=';', encoding='latin1')
        # deixa com colunas 'Sigla' e 'Nome' (caso venham diferentes, apenas mantenha o df)
        if 'Sigla' not in df_airlines.columns:
            df_airlines.rename(columns={df_airlines.columns[0]: 'Sigla'}, inplace=True)
        if 'Nome' not in df_airlines.columns and df_airlines.shape[1] > 1:
            df_airlines.rename(columns={df_airlines.columns[1]: 'Nome'}, inplace=True)
    except Exception:
        df_airlines = pd.DataFrame(columns=['Sigla', 'Nome'])

    # filtra voos realizados (mantendo compatibilidade com seu dataset original)
    if 'Situação Voo' in df_completo.columns:
        df_realizados = df_completo[df_completo['Situação Voo'] == 'REALIZADO'].copy()
    else:
        df_realizados = df_completo.copy()  # se não tiver essa coluna, assume tudo

    # merge com nomes de aeroportos
    if not df_nomes_aeroportos.empty and 'ICAO Aeródromo Origem' in df_realizados.columns:
        df_realizados = pd.merge(
            df_realizados,
            df_nomes_aeroportos,
            left_on='ICAO Aeródromo Origem',
            right_on='ident',
            how='left'
        )
        df_realizados.rename(columns={'name': 'nome_aeroporto_origem'}, inplace=True)
        df_realizados['nome_aeroporto_origem'].fillna(df_realizados.get('ICAO Aeródromo Origem', ''), inplace=True)
    else:
        if 'ICAO Aeródromo Origem' in df_realizados.columns:
            df_realizados['nome_aeroporto_origem'] = df_realizados['ICAO Aeródromo Origem']
        else:
            df_realizados['nome_aeroporto_origem'] = 'Desconhecido'

    # merge com nomes de companhias
    if not df_airlines.empty and 'ICAO Empresa Aérea' in df_realizados.columns:
        if 'Sigla' in df_airlines.columns and 'Nome' in df_airlines.columns:
            df_realizados = pd.merge(
                df_realizados,
                df_airlines[['Sigla', 'Nome']],
                left_on='ICAO Empresa Aérea',
                right_on='Sigla',
                how='left'
            )
            df_realizados['Nome'].fillna(df_realizados['ICAO Empresa Aérea'], inplace=True)
        else:
            df_realizados['Nome'] = df_realizados.get('ICAO Empresa Aérea', 'Desconhecido')
    else:
        df_realizados['Nome'] = df_realizados.get('ICAO Empresa Aérea', 'Desconhecido')

    # converte datas
    colunas_de_data = ['Partida Prevista', 'Partida Real', 'Chegada Prevista', 'Chegada Real']
    for coluna in colunas_de_data:
        if coluna in df_realizados.columns:
            df_realizados[coluna] = pd.to_datetime(df_realizados[coluna], format='%d/%m/%Y %H:%M', errors='coerce')

    # remove registros sem datas válidas
    datas_presentes = [c for c in colunas_de_data if c in df_realizados.columns]
    if datas_presentes:
        df_realizados.dropna(subset=datas_presentes, inplace=True)

    # calcula atraso em minutos e flag de atraso (>15 minutos)
    if 'Partida Real' in df_realizados.columns and 'Partida Prevista' in df_realizados.columns:
        df_realizados['atraso_partida_min'] = (df_realizados['Partida Real'] - df_realizados['Partida Prevista']).dt.total_seconds() / 60
        df_realizados['voo_atrasado'] = (df_realizados['atraso_partida_min'] > 15).astype(int)
    else:
        # se não houver colunas, cria colunas vazias para não quebrar o restante do código
        df_realizados['atraso_partida_min'] = 0
        df_realizados['voo_atrasado'] = 0

    # dia da semana e periodo do dia
    if 'Partida Prevista' in df_realizados.columns:
        df_realizados['dia_da_semana'] = df_realizados['Partida Prevista'].dt.day_name()
        bins = [-1, 6, 12, 18, 24]
        labels = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
        df_realizados['periodo_dia'] = pd.cut(df_realizados['Partida Prevista'].dt.hour, bins=bins, labels=labels, right=False)
    else:
        df_realizados['dia_da_semana'] = 'Desconhecido'
        df_realizados['periodo_dia'] = 'Desconhecido'

    return df_realizados

# carrega dados
df_realizados = carregar_dados()

# ----------- HEADER -----------
st.markdown("<h1 style='text-align: center; margin-bottom: 8px;'>🌌 Painel Dark de Voos no Brasil</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#cfece3; margin-top: -8px;'>Análises de atrasos e tendências (2022-2024)</p>", unsafe_allow_html=True)

# ----------- SIDEBAR: FILTROS -----------
st.sidebar.title("🎛️ Filtros")
anos_disponiveis = sorted(df_realizados['ano'].unique())
anos_selecionados = st.sidebar.multiselect(
    "📅 Selecione o(s) Ano(s)", options=anos_disponiveis, default=anos_disponiveis
)
if not anos_selecionados:
    st.sidebar.warning("Por favor, selecione pelo menos um ano.")
    st.stop()

# filtro principal
df_filtrado = df_realizados[df_realizados['ano'].isin(anos_selecionados)].copy()

# ----------- KPIs CUSTOMIZADOS -----------
st.subheader("📊 Indicadores Gerais")
total_voos = int(df_filtrado.shape[0])
total_atrasos = int(df_filtrado['voo_atrasado'].sum())
percentual_atrasos = (total_atrasos / total_voos) * 100 if total_voos > 0 else 0.0

st.markdown(f"""
<div class="metric-container">
    <div class="metric-card blue-card">
        🛫<br>Voos Realizados<br><b style="font-size:20px;">{total_voos:,}</b>
    </div>
    <div class="metric-card green-card">
        ⏰<br>Atrasos (>15 min)<br><b style="font-size:20px;">{total_atrasos:,}</b>
    </div>
    <div class="metric-card red-card">
        ⚠️<br>Taxa de Atrasos<br><b style="font-size:20px;">{percentual_atrasos:.2f}%</b>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ----------- AEROPORTOS COM MAIS ATRASOS -----------
st.header("🛑 Top 10 Aeroportos com Mais Atrasos na Partida")
atrasos_por_aeroporto = df_filtrado.groupby('nome_aeroporto_origem')['voo_atrasado'].sum().sort_values(ascending=False).head(10)

if not atrasos_por_aeroporto.empty:
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    palette = sns.color_palette("rocket", n_colors=len(atrasos_por_aeroporto))
    sns.barplot(x=atrasos_por_aeroporto.values, y=atrasos_por_aeroporto.index, ax=ax, palette=palette, orient='h')

    # Anotações nas barras
    for p in ax.patches:
        width = p.get_width()
        y = p.get_y() + p.get_height() / 2
        ax.text(width + max(atrasos_por_aeroporto.values) * 0.01, y, f'{int(width):,}'.replace(',', '.'), va='center', color='white', fontsize=10)

    ax.set_title('Top 10 Aeroportos por Volume Total de Atrasos', color='#00C9A7', fontsize=14)
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.tick_params(colors='white', labelsize=10)
    sns.despine(left=True, bottom=True)
    st.pyplot(fig)
else:
    st.warning("Não há dados de atraso de aeroportos para os filtros selecionados.")

# ----------- COMPARATIVO ANUAL POR COMPANHIA -----------
st.header("✈️ Comparativo Anual de Atrasos (Top 10 Companhias)")
if len(anos_selecionados) > 1:
    top_10_nomes = df_filtrado.groupby('Nome')['voo_atrasado'].sum().nlargest(10).index
    df_para_plot = df_filtrado[df_filtrado['Nome'].isin(top_10_nomes)]
    atrasos_companhia_ano = df_para_plot.groupby(['ano', 'Nome'])['voo_atrasado'].sum().reset_index()

    if not atrasos_companhia_ano.empty:
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        fig2.patch.set_facecolor('#0E1117')
        ax2.set_facecolor('#0E1117')

        sns.barplot(data=atrasos_companhia_ano, x='Nome', y='voo_atrasado', hue='ano', ax=ax2, palette="mako")
        ax2.set_title('Comparativo de Atrasos na Partida por Ano (Top 10 Companhias)', color='#00C9A7', fontsize=14)
        ax2.set_xlabel('')
        ax2.set_ylabel('Número Total de Voos Atrasados', color='white')
        ax2.tick_params(colors='white', labelrotation=45)
        plt.xticks(rotation=45, ha='right')

        # ajustar legenda para dark
        legend = ax2.legend()
        if legend:
            legend.get_frame().set_facecolor('#121418')
            for text in legend.get_texts():
                text.set_color('white')

        st.pyplot(fig2)
    else:
        st.info("Não há dados de atrasos de companhias para os anos selecionados.")
else:
    st.info("Selecione mais de um ano no filtro para visualizar a comparação entre companhias aéreas.")

# ----------- ATRASOS POR DIA DA SEMANA E PERÍODO -----------
st.header("📆 Atrasos por Dia da Semana e Por Período do Dia")
col_dia, col_periodo = st.columns(2)

with col_dia:
    st.subheader("Dias da Semana")
    atrasos_por_dia = df_filtrado.groupby('dia_da_semana')['voo_atrasado'].sum()
    dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    atrasos_por_dia = atrasos_por_dia.reindex(dias_ordem).fillna(0)

    if not atrasos_por_dia.empty:
        fig3, ax3 = plt.subplots(figsize=(7, 4))
        fig3.patch.set_facecolor('#0E1117')
        ax3.set_facecolor('#0E1117')

        sns.barplot(x=atrasos_por_dia.index, y=atrasos_por_dia.values, ax=ax3, palette='crest')
        ax3.set_title('Total de Atrasos por Dia da Semana', color='#00C9A7')
        ax3.set_xlabel('')
        ax3.set_ylabel('Número de Voos Atrasados', color='white')
        ax3.set_xticklabels(['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'])
        ax3.tick_params(colors='white')
        st.pyplot(fig3)
    else:
        st.info("Sem dados por dia da semana para os filtros selecionados.")

with col_periodo:
    st.subheader("Períodos do Dia")
    atrasos_por_periodo = df_filtrado.groupby('periodo_dia')['voo_atrasado'].sum()
    periodos_ordem = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
    atrasos_por_periodo = atrasos_por_periodo.reindex(periodos_ordem).fillna(0)

    if not atrasos_por_periodo.empty:
        fig4, ax4 = plt.subplots(figsize=(7, 4))
        fig4.patch.set_facecolor('#0E1117')
        ax4.set_facecolor('#0E1117')

        sns.barplot(x=atrasos_por_periodo.index, y=atrasos_por_periodo.values, ax=ax4, palette='mako')
        ax4.set_title('Total de Atrasos por Período do Dia', color='#00C9A7')
        ax4.set_xlabel('')
        ax4.set_ylabel('Número de Voos Atrasados', color='white')
        ax4.tick_params(colors='white')
        st.pyplot(fig4)
    else:
        st.info("Sem dados por período do dia para os filtros selecionados.")

st.divider()

# ----------- TENDÊNCIAS 2022-2024 -----------
st.header("📈📉 Tendências de Atrasos (2022 → 2024)")

anos_necessarios_tendencia = [2022, 2023, 2024]
anos_presentes_no_filtro = list(df_filtrado['ano'].unique())
if all(ano in anos_presentes_no_filtro for ano in anos_necessarios_tendencia):
    df_pivot = df_filtrado.pivot_table(
        index='nome_aeroporto_origem', columns='ano', values='voo_atrasado', aggfunc='sum'
    ).fillna(0)

    # garante colunas dos anos
    for ano in anos_necessarios_tendencia:
        if ano not in df_pivot.columns:
            df_pivot[ano] = 0

    condicao_aumento = (df_pivot[2023] >= df_pivot[2022]) & (df_pivot[2024] > df_pivot[2023])
    condicao_reducao = (df_pivot[2023] <= df_pivot[2022]) & (df_pivot[2024] < df_pivot[2023])

    df_aumento = df_pivot[condicao_aumento].copy()
    df_reducao = df_pivot[condicao_reducao].copy()

    df_aumento['Variacao_Total'] = df_aumento[2024] - df_aumento[2022]
    df_reducao['Variacao_Total'] = df_reducao[2024] - df_reducao[2022]

    df_aumento.sort_values('Variacao_Total', ascending=False, inplace=True)
    df_reducao.sort_values('Variacao_Total', ascending=True, inplace=True)

    col_tend_aumento, col_tend_reducao = st.columns(2)

    with col_tend_aumento:
        st.subheader("Tendência de Aumento 📈")
        st.markdown("Aeroportos com aumento consistente de atrasos entre 2022 e 2024.")
        if not df_aumento.empty:
            top_10_aumento = df_aumento.head(10)
            fig_aum, ax_aum = plt.subplots(figsize=(8, 5))
            fig_aum.patch.set_facecolor('#0E1117')
            ax_aum.set_facecolor('#0E1117')

            sns.barplot(x=top_10_aumento['Variacao_Total'], y=top_10_aumento.index, ax=ax_aum, palette='Reds_r')
            ax_aum.set_title('Top 10 Piores Tendências (Aumento)', color='#00C9A7')
            ax_aum.set_xlabel('Nº de Atrasos a Mais em 2024 vs 2022')
            ax_aum.tick_params(colors='white')
            st.pyplot(fig_aum)

            with st.expander("Ver dados detalhados da tendência de aumento"):
                st.dataframe(df_aumento)
        else:
            st.info("Nenhum aeroporto apresentou tendência consistente de aumento.")

    with col_tend_reducao:
        st.subheader("Tendência de Redução 📉")
        st.markdown("Aeroportos com redução consistente de atrasos entre 2022 e 2024.")
        if not df_reducao.empty:
            top_10_reducao = df_reducao.head(10).copy()
            top_10_reducao['Variacao_Absoluta'] = (top_10_reducao['Variacao_Total'] * -1)

            fig_red, ax_red = plt.subplots(figsize=(8, 5))
            fig_red.patch.set_facecolor('#0E1117')
            ax_red.set_facecolor('#0E1117')

            sns.barplot(x=top_10_reducao['Variacao_Absoluta'], y=top_10_reducao.index, ax=ax_red, palette='Greens_r')
            ax_red.set_title('Top 10 Melhores Tendências (Redução)', color='#00C9A7')
            ax_red.set_xlabel('Nº de Atrasos a Menos em 2024 vs 2022')
            ax_red.tick_params(colors='white')
            st.pyplot(fig_red)

            with st.expander("Ver dados detalhados da tendência de redução"):
                st.dataframe(df_reducao)
        else:
            st.info("Nenhum aeroporto apresentou tendência consistente de redução.")
else:
    st.info("Para visualizar a análise de tendência 3 anos, selecione dados de 2022, 2023 e 2024 nos filtros (se disponíveis).")
