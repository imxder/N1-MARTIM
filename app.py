from flask import Flask, jsonify, request, render_template
import pandas as pd
import warnings
import os

warnings.simplefilter(action='ignore', category=FutureWarning)

app = Flask(__name__)

def carregar_dados():
    arquivos = {
        2022: 'dataset/VRA2022.csv',
        2023: 'dataset/VRA2023.csv',
        2024: 'dataset/VRA2024.csv',
    }
    lista_de_dfs = []
    
    print(f"Diretório de trabalho atual: {os.getcwd()}")
    
    for ano, caminho in arquivos.items():
        try:
            if os.path.exists(caminho):
                print(f"Lendo o arquivo: {caminho}")
                df_temp = pd.read_csv(caminho, sep=';', encoding='utf-8', dtype={'Código Justificativa': str})
                df_temp['ano'] = ano
                lista_de_dfs.append(df_temp)
            else:
                print(f"Arquivo não encontrado, pulando: {caminho}")
        except FileNotFoundError:
            print(f"Erro: Arquivo não encontrado - {caminho}")
            pass
    
    if not lista_de_dfs:
        print("Nenhum arquivo de dados de voos encontrado. A API não pode continuar.")
        return pd.DataFrame()

    df_completo = pd.concat(lista_de_dfs, ignore_index=True)
    
    try:
        df_aeroportos = pd.read_csv('dataset/codes/airport-codes.csv', sep=';', encoding='latin1')
        df_nomes_aeroportos = df_aeroportos[df_aeroportos['iso_country'] == 'BR'][['ident', 'name']].copy()
    except FileNotFoundError:
        print("Aviso: Arquivo 'dataset/codes/airport-codes.csv' não encontrado.")
        df_nomes_aeroportos = pd.DataFrame(columns=['ident', 'name'])
    
    try:
        df_airlines = pd.read_csv('dataset/codes/airlines-codes.csv', sep=';', encoding='latin1')
        df_airlines.rename(columns={'Nome': 'Nome', 'Sigla': 'Sigla'}, inplace=True)
    except FileNotFoundError:
        print("Aviso: Arquivo 'dataset/codes/airlines-codes.csv' não encontrado.")
        df_airlines = pd.DataFrame(columns=['Sigla', 'Nome'])

    df_realizados = df_completo[df_completo['Situação Voo'] == 'REALIZADO'].copy()
    
    if not df_nomes_aeroportos.empty:
        df_realizados = pd.merge(df_realizados, df_nomes_aeroportos, left_on='ICAO Aeródromo Origem', right_on='ident', how='left')
        df_realizados.rename(columns={'name': 'nome_aeroporto_origem'}, inplace=True)
        df_realizados['nome_aeroporto_origem'].fillna(df_realizados['ICAO Aeródromo Origem'], inplace=True)
    else:
        df_realizados['nome_aeroporto_origem'] = df_realizados['ICAO Aeródromo Origem']

    if not df_airlines.empty:
        df_realizados = pd.merge(df_realizados, df_airlines[['Sigla', 'Nome']], left_on='ICAO Empresa Aérea', right_on='Sigla', how='left')
        df_realizados['Nome'].fillna(df_realizados['ICAO Empresa Aérea'], inplace=True)
    else:
        df_realizados['Nome'] = df_realizados['ICAO Empresa Aérea']

    colunas_de_data = ['Partida Prevista', 'Partida Real', 'Chegada Prevista', 'Chegada Real']
    for coluna in colunas_de_data:
        df_realizados[coluna] = pd.to_datetime(df_realizados[coluna], format='%d/%m/%Y %H:%M', errors='coerce')
    df_realizados.dropna(subset=colunas_de_data, inplace=True)
    
    df_realizados['atraso_partida_min'] = (df_realizados['Partida Real'] - df_realizados['Partida Prevista']).dt.total_seconds() / 60
    df_realizados['voo_atrasado'] = (df_realizados['atraso_partida_min'] > 15).astype(int)
    
    df_realizados['dia_da_semana'] = df_realizados['Partida Prevista'].dt.day_name()
    bins = [-1, 6, 12, 18, 24]
    labels = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
    df_realizados['periodo_dia'] = pd.cut(df_realizados['Partida Prevista'].dt.hour, bins=bins, labels=labels, right=False)
    
    return df_realizados

# Carrega os dados uma vez ao iniciar a aplicação
try:
    df_realizados = carregar_dados()
    if df_realizados.empty:
        raise Exception("Nenhum dado de voo carregado.")
except Exception as e:
    print(f"Erro fatal ao carregar os dados: {e}")
    df_realizados = pd.DataFrame()

# --- ROTA PARA SERVIR O TEMPLATE HTML ---
@app.route('/')
def index():
    return render_template('index.html')

# --- DEFINIÇÃO DAS ROTAS (ENDPOINTS) DA API ---
@app.route('/api/overview', methods=['GET'])
def get_overview():
    """Endpoint para a visão geral, aceitando filtros de ano."""
    if df_realizados.empty:
        return jsonify({"error": "Dados não carregados."}), 500

    anos_str = request.args.get('anos', '')
    if anos_str:
        try:
            anos_selecionados = [int(ano) for ano in anos_str.split(',')]
            df_filtrado = df_realizados[df_realizados['ano'].isin(anos_selecionados)]
        except (ValueError, TypeError):
            return jsonify({"error": "Parâmetro 'anos' inválido. Use uma lista de números separados por vírgula."}), 400
    else:
        df_filtrado = df_realizados

    total_voos = int(df_filtrado.shape[0])
    total_atrasos = int(df_filtrado['voo_atrasado'].sum())
    percentual_atrasos = (total_atrasos / total_voos) * 100 if total_voos > 0 else 0
    
    return jsonify({
        "total_voos": total_voos,
        "total_atrasos": total_atrasos,
        "percentual_atrasos": round(percentual_atrasos, 2),
        "anos_disponiveis": sorted(df_realizados['ano'].unique().tolist())
    })

@app.route('/api/top_aeroportos', methods=['GET'])
def get_top_aeroportos():
    """Endpoint para o top 10 de aeroportos com mais atrasos."""
    if df_realizados.empty:
        return jsonify({"error": "Dados não carregados."}), 500
    
    anos_str = request.args.get('anos', '')
    if anos_str:
        anos_selecionados = [int(ano) for ano in anos_str.split(',')]
        df_filtrado = df_realizados[df_realizados['ano'].isin(anos_selecionados)]
    else:
        df_filtrado = df_realizados
    
    atrasos_por_aeroporto = df_filtrado.groupby('nome_aeroporto_origem')['voo_atrasado'].sum().sort_values(ascending=False).head(10)
    
    if atrasos_por_aeroporto.empty:
        return jsonify({"data": []})

    data = atrasos_por_aeroporto.to_dict()
    
    return jsonify({
        "top_aeroportos": [{"aeroporto": k, "atrasos": int(v)} for k, v in data.items()]
    })

@app.route('/api/atrasos_por_dia_e_periodo', methods=['GET'])
def get_atrasos_por_dia_e_periodo():
    """Endpoint para atrasos por dia da semana e período do dia."""
    if df_realizados.empty:
        return jsonify({"error": "Dados não carregados."}), 500
    
    anos_str = request.args.get('anos', '')
    if anos_str:
        anos_selecionados = [int(ano) for ano in anos_str.split(',')]
        df_filtrado = df_realizados[df_realizados['ano'].isin(anos_selecionados)]
    else:
        df_filtrado = df_realizados

    atrasos_por_dia = df_filtrado.groupby('dia_da_semana')['voo_atrasado'].sum()
    dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    atrasos_por_dia = atrasos_por_dia.reindex(dias_ordem).fillna(0).astype(int)
    
    atrasos_por_periodo = df_filtrado.groupby('periodo_dia')['voo_atrasado'].sum()
    periodos_ordem = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
    atrasos_por_periodo = atrasos_por_periodo.reindex(periodos_ordem).fillna(0).astype(int)
    
    return jsonify({
        "por_dia_da_semana": atrasos_por_dia.to_dict(),
        "por_periodo_do_dia": atrasos_por_periodo.to_dict()
    })

@app.route('/api/tendencias', methods=['GET'])
def get_tendencias():
    """Endpoint para a análise de tendências de 2022-2024."""
    if df_realizados.empty:
        return jsonify({"error": "Dados não carregados."}), 500

    anos_necessarios_tendencia = [2022, 2023, 2024]
    df_tendencia = df_realizados[df_realizados['ano'].isin(anos_necessarios_tendencia)].copy()
    
    if df_tendencia.empty:
        return jsonify({"warning": "Dados de 2022, 2023 e 2024 não encontrados para a análise de tendência."})

    df_pivot = df_tendencia.pivot_table(
        index='nome_aeroporto_origem', columns='ano', values='voo_atrasado', aggfunc='sum'
    ).fillna(0)
    
    condicao_aumento = (df_pivot[2023] >= df_pivot[2022]) & (df_pivot[2024] > df_pivot[2023])
    condicao_reducao = (df_pivot[2023] <= df_pivot[2022]) & (df_pivot[2024] < df_pivot[2023])
    
    df_aumento = df_pivot[condicao_aumento].copy()
    df_reducao = df_pivot[condicao_reducao].copy()
    
    df_aumento['Variacao_Total'] = df_aumento[2024] - df_aumento[2022]
    df_reducao['Variacao_Total'] = df_reducao[2024] - df_reducao[2022]
    
    df_aumento.sort_values('Variacao_Total', ascending=False, inplace=True)
    df_reducao.sort_values('Variacao_Total', ascending=True, inplace=True)
    
    top_10_aumento = df_aumento.head(10).to_dict('index')
    top_10_reducao = df_reducao.head(10).to_dict('index')
    
    def convert_to_int(d):
        return {k: {int(y): int(v) for y, v in x.items() if y != 'Variacao_Total'} for k, x in d.items()}

    return jsonify({
        "tendencia_aumento": convert_to_int(top_10_aumento),
        "tendencia_reducao": convert_to_int(top_10_reducao)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)