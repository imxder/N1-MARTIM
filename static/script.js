// URLs dos endpoints da API
const API_BASE_URL = window.location.origin + '/api';

// Instâncias dos gráficos para que possam ser atualizadas
let charts = {};

// Paleta de cores limpa e profissional
const chartColors = {
    primary: 'rgba(0, 77, 153, 0.9)', // Azul escuro
    secondary: 'rgba(0, 140, 186, 0.9)', // Azul claro
    highlight: 'rgba(255, 102, 0, 0.9)', // Laranja para destaque
    text: '#333'
};

// --- Funções para buscar dados da API ---
async function fetchOverviewData(anos) {
    const response = await fetch(`${API_BASE_URL}/overview?anos=${anos}`);
    return response.json();
}

async function fetchTopAeroportosData(anos) {
    const response = await fetch(`${API_BASE_URL}/top_aeroportos?anos=${anos}`);
    return response.json();
}

async function fetchAtrasosPorPeriodoData(anos) {
    const response = await fetch(`${API_BASE_URL}/atrasos_por_dia_e_periodo?anos=${anos}`);
    return response.json();
}

async function fetchTendenciasData() {
    const response = await fetch(`${API_BASE_URL}/tendencias`);
    return response.json();
}

// --- Funções para atualizar o DOM e renderizar gráficos ---

function updateMetrics(data) {
    document.getElementById('total-voos').textContent = data.total_voos.toLocaleString('pt-BR');
    document.getElementById('total-atrasos').textContent = data.total_atrasos.toLocaleString('pt-BR');
    document.getElementById('percentual-atrasos').textContent = `${data.percentual_atrasos.toFixed(2)}%`;
}

function renderChart(id, type, labels, data, title, isHorizontal = false) {
    const ctx = document.getElementById(id).getContext('2d');
    
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: false },
            tooltip: {
                backgroundColor: chartColors.primary,
                titleColor: 'white',
                bodyColor: 'white',
                displayColors: false,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        label += context.parsed.x || context.parsed.y;
                        return label.toLocaleString('pt-BR');
                    }
                }
            }
        },
        animation: { duration: 1000, easing: 'easeOutQuart' },
        scales: {
            x: {
                grid: { display: false },
                ticks: { color: chartColors.text }
            },
            y: {
                grid: { color: 'rgba(0, 0, 0, 0.05)' },
                ticks: { color: chartColors.text, precision: 0 }
            }
        }
    };
    
    if (isHorizontal) {
        commonOptions.indexAxis = 'y';
        commonOptions.scales = {
            x: {
                beginAtZero: true,
                grid: { color: 'rgba(0, 0, 0, 0.05)' },
                ticks: { color: chartColors.text, precision: 0 }
            },
            y: {
                grid: { display: false },
                ticks: { color: chartColors.text }
            }
        };
    }

    let colors = Array(data.length).fill(chartColors.secondary);
    if (id === 'topAeroportosChart' && data.length > 0) {
        // Destaca o aeroporto com mais atrasos
        const maxIndex = data.indexOf(Math.max(...data));
        colors[maxIndex] = chartColors.primary;
    } else if (id === 'tendenciaAumentoChart') {
        colors = Array(data.length).fill(chartColors.highlight);
    } else if (id === 'tendenciaReducaoChart') {
        colors = Array(data.length).fill(chartColors.secondary);
    }

    if (charts[id]) {
        charts[id].data.labels = labels;
        charts[id].data.datasets[0].data = data;
        charts[id].data.datasets[0].backgroundColor = colors;
        charts[id].update();
        return;
    }

    charts[id] = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                backgroundColor: colors,
                borderColor: 'transparent',
                borderWidth: 1
            }]
        },
        options: commonOptions
    });
}

function renderTopAeroportos(data) {
    const labels = data.top_aeroportos.map(item => item.aeroporto);
    const valores = data.top_aeroportos.map(item => item.atrasos);
    renderChart('topAeroportosChart', 'bar', labels, valores, 'Top 10 Aeroportos com Mais Atrasos', true);
}

function renderAtrasosPorPeriodo(data) {
    const diaLabels = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'];
    const diaValores = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(dia => data.por_dia_da_semana[dia] || 0);
    renderChart('atrasosDiaSemanaChart', 'bar', diaLabels, diaValores, 'Total de Atrasos por Dia da Semana');

    const periodoLabels = ['Madrugada', 'Manhã', 'Tarde', 'Noite'];
    const periodoValores = periodoLabels.map(periodo => data.por_periodo_do_dia[periodo] || 0);
    renderChart('atrasosPeriodoDiaChart', 'bar', periodoLabels, periodoValores, 'Total de Atrasos por Período do Dia');
}

function renderTendencias(data) {
    const aumentoLabels = Object.keys(data.tendencia_aumento);
    const aumentoValores = aumentoLabels.map(aeroporto => {
        const valores = data.tendencia_aumento[aeroporto];
        return valores[2024] - valores[2022];
    });
    renderChart('tendenciaAumentoChart', 'bar', aumentoLabels, aumentoValores, 'Piores Tendências', true);

    const reducaoLabels = Object.keys(data.tendencia_reducao);
    const reducaoValores = reducaoLabels.map(aeroporto => {
        const valores = data.tendencia_reducao[aeroporto];
        return Math.abs(valores[2024] - valores[2022]);
    });
    renderChart('tendenciaReducaoChart', 'bar', reducaoLabels, reducaoValores, 'Melhores Tendências', true);
}

// --- Funções de controle ---
async function updateDashboard() {
    const anosSelecionados = getSelectedYears();
    
    const [overviewData, topAeroportosData, atrasosPeriodoData, tendenciasData] = await Promise.all([
        fetchOverviewData(anosSelecionados.join(',')),
        fetchTopAeroportosData(anosSelecionados.join(',')),
        fetchAtrasosPorPeriodoData(anosSelecionados.join(',')),
        fetchTendenciasData()
    ]);

    updateMetrics(overviewData);
    renderTopAeroportos(topAeroportosData);
    renderAtrasosPorPeriodo(atrasosPeriodoData);
    renderTendencias(tendenciasData);
}

function getSelectedYears() {
    const select = document.getElementById('ano-select');
    return Array.from(select.options)
                .filter(option => option.selected)
                .map(option => option.value);
}

async function populateYearSelect() {
    const data = await fetchOverviewData('');
    const select = document.getElementById('ano-select');
    data.anos_disponiveis.forEach(ano => {
        const option = document.createElement('option');
        option.value = ano;
        option.textContent = ano;
        option.selected = true;
        select.appendChild(option);
    });
    
    select.addEventListener('change', updateDashboard);
}

document.addEventListener('DOMContentLoaded', () => {
    populateYearSelect().then(() => {
        updateDashboard();
    });
});