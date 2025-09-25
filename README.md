# Dashboard de Análise de Voos - Aviação Brasileira

Este projeto consiste num dashboard interativo para a análise de dados de voos da aviação comercial brasileira. A aplicação, desenvolvida com a biblioteca **Panel**, permite a visualização de métricas e tendências sobre voos e atrasos, utilizando dados públicos da ANAC para os anos de 2022, 2023 e 2024.

O `Panel` foi escolhido pela sua flexibilidade no controle do layout e pela sua poderosa capacidade de criar dashboards reativos.

## Funcionalidades

- **Métricas Chave:** Visualização em tempo real do total de voos, total de atrasos (> 15 minutos) e o percentual de voos atrasados.
- **Filtros Interativos:** Filtre os dados por um ou mais Anos e por uma ou mais Companhias Aéreas através de widgets na barra lateral.
- **Top 10 Aeroportos:** Gráfico de barras horizontais que exibe os 10 aeroportos de origem com maior número de voos atrasados.
- **Voos por Companhia Aérea:** Gráfico de barras horizontais que mostra a participação das 10 principais companhias no total de voos.
- **Evolução Mensal:** Gráfico de linhas que acompanha o volume total de voos ao longo dos meses.
- **Dados Enriquecidos:** Utiliza ficheiros de códigos para exibir os nomes completos dos aeroportos e das companhias aéreas, tornando a análise mais clara e intuitiva.

## Tecnologias Utilizadas

- **Python:** Linguagem principal do projeto.
- **Panel:** Framework utilizado para construir a interface web interativa e reativa.
- **Pandas:** Biblioteca para manipulação e análise dos dados.
- **Plotly:** Biblioteca para a criação dos gráficos interativos.

## Como Executar o Projeto

Siga os passos abaixo para executar o dashboard no seu ambiente local.

### Pré-requisitos

- Ter o [Python](https://www.python.org/downloads/) instalado (versão 3.8 ou superior).

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO_GIT>
    cd <NOME_DA_PASTA_DO_PROJETO>
    ```

2.  **(Recomendado) Crie e ative um ambiente virtual:**
    - No Windows:
      ```bash
      python -m venv venv
      .\venv\Scripts\activate
      ```
    - No macOS/Linux:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```

3.  **Instale as dependências:**
    (Certifique-se que o `requirements.txt` contém `panel`, `pandas` e `plotly`)
    ```bash
    pip install -r requirements.txt
    ```

### Execução

1.  Com o ambiente virtual ativo, execute o seguinte comando no terminal:
    ```bash
    panel serve app.py --show
    ```

2.  A aplicação será aberta automaticamente no seu navegador.

## Estrutura do Projeto

```
.
├── dataset/
│   ├── codes/
│   │   ├── airlines-codes.csv
│   │   └── airport-codes.csv
│   ├── VRA2022.csv
│   ├── VRA2023.csv
│   └── VRA2024.csv
├── app.py              # Código principal da aplicação Panel
├── requirements.txt    # Ficheiro com as dependências do projeto
└── README.md            
```

## Fontes de Dados

- **Voos (VRA):** Ficheiros `VRA*.csv` contendo dados detalhados sobre cada voo (origem, destino, horários, situação).
- **Códigos de Aeroportos:** `airport-codes.csv` para mapear os códigos ICAO para nomes de aeroportos e cidades.
- **Códigos de Companhias Aéreas:** `airlines-codes.csv` para mapear os códigos ICAO para os nomes das companhias.
