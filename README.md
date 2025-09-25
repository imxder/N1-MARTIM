# Dashboard de Análise de Voos - Aviação Brasileira

Este projeto consiste num dashboard interativo para a análise de dados de voos da aviação comercial brasileira. A aplicação, desenvolvida com a biblioteca **Streamlit**, permite a visualização de métricas e tendências sobre voos e atrasos, utilizando dados públicos da ANAC para os anos de 2022, 2023 e 2024.

O `Streamlit` foi escolhido pela sua simplicidade e rapidez na criação de aplicações de dados interativas e visualmente atraentes.

## Funcionalidades

- **Visão Geral:** Métricas principais (Total de Voos, Atrasos, Taxa de Atraso) exibidas de forma clara e objetiva.
- **Análise de Aeroportos:** Gráfico de barras com o Top 10 aeroportos de origem com maior volume de voos atrasados.
- **Performance das Companhias:** Gráfico comparativo que mostra a evolução anual do número de atrasos para as 10 principais companhias aéreas.
- **Análise Sazonal:** Gráficos que detalham a distribuição de atrasos por dia da semana e por período do dia.
- **Análise de Tendências:** Identificação de aeroportos com aumento ou redução consistente no número de atrasos, comparando os anos de 2022 e 2024.

## Tecnologias Utilizadas

- **Python:** Linguagem principal do projeto.
- **Streamlit:** Framework utilizado para construir a interface web interativa.
- **Pandas:** Biblioteca para manipulação e análise dos dados.
- **Seaborn & Matplotlib:** Bibliotecas para a criação das visualizações de dados.

## Como Executar o Projeto

Siga os passos abaixo para executar o dashboard no seu ambiente local.

### Pré-requisitos

- Ter o [Python](https://www.python.org/downloads/) instalado (versão 3.8 ou superior).

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <https://github.com/imxder/N1-MARTIM.git>
    cd <N1-MARTIM>
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
    (Certifique-se que o `requirements.txt` contém `streamlit`, `pandas`, `seaborn` e `matplotlib`)
    ```bash
    pip install -r requirements.txt
    ```

### Execução

1.  Com o ambiente virtual ativo, execute o seguinte comando no terminal:
    ```bash
    streamlit run app.py
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
├── app.py              # Código principal da aplicação Streamlit
├── requirements.txt    # Ficheiro com as dependências do projeto
└── README.md             
```

## Fontes de Dados

- **Voos (VRA):** Ficheiros `VRA*.csv` contendo dados detalhados sobre cada voo (origem, destino, horários, situação).
- **Códigos de Aeroportos:** `airport-codes.csv` para mapear os códigos ICAO para nomes de aeroportos e cidades.
- **Códigos de Companhias Aéreas:** `airlines-codes.csv` para mapear os códigos para os nomes das companhias.