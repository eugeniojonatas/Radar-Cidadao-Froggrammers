document.addEventListener('DOMContentLoaded', () => {
    // Configurações globais do Chart.js para ficarem mais bonitos
    Chart.defaults.color = '#7f8c8d';
    Chart.defaults.font.family = "'Segoe UI', sans-serif";

    // 1. Gráfico de Frequência (perfil.html)
    const ctxFreq = document.getElementById('chartFrequencia');
    if (ctxFreq) {
        new Chart(ctxFreq, {
            type: 'bar',
            data: {
                labels: ['2019', '2020', '2021', '2022', '2023', '2024'],
                datasets: [{
                    label: 'Presença (%)',
                    data: [85, 92, 98, 94, 90, 88],
                    backgroundColor: '#1565c0',
                    borderRadius: 5,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });
    }

    // 2. Gráfico Geral (graficos.html)
    const ctxGeral = document.getElementById('chartGeral');
    if (ctxGeral) {
        new Chart(ctxGeral, {
            type: 'line',
            data: {
                labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                datasets: [{
                    label: 'Projetos de Lei Apresentados',
                    data: [15, 28, 42, 35, 50, 48],
                    borderColor: '#ff9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true } }
            }
        });
    }
});