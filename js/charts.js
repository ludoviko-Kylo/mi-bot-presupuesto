// Configuración y gestión de gráficos interactivos con Chart.js
class BudgetCharts {
  constructor() {
    this.donutChart = null;
    this.barChart = null;
  }

  // Formateo de moneda para tooltips y leyendas
  formatMoney(amount, currency = '$') {
    return `${currency}${Number(amount).toLocaleString('es-ES', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  }

  // Inicializa o actualiza el gráfico de dona (Gastos por Categoría)
  updateDonutChart(expenseTotals, currency = '$') {
    const canvas = document.getElementById('categoryDonutChart');
    const emptyState = document.getElementById('donutEmptyState');
    if (!canvas) return;

    const entries = Object.entries(expenseTotals).filter(([_, amt]) => amt > 0);

    if (entries.length === 0) {
      if (this.donutChart) {
        this.donutChart.destroy();
        this.donutChart = null;
      }
      canvas.classList.add('hidden');
      if (emptyState) emptyState.classList.remove('hidden');
      return;
    }

    canvas.classList.remove('hidden');
    if (emptyState) emptyState.classList.add('hidden');

    const labels = [];
    const data = [];
    const bgColors = [];

    entries.forEach(([catId, amount]) => {
      const cat = getCategoryById(catId, 'expense');
      labels.push(cat.name);
      data.push(amount);
      bgColors.push(cat.color || '#64748b');
    });

    if (this.donutChart) {
      this.donutChart.data.labels = labels;
      this.donutChart.data.datasets[0].data = data;
      this.donutChart.data.datasets[0].backgroundColor = bgColors;
      this.donutChart.update();
      return;
    }

    const ctx = canvas.getContext('2d');
    this.donutChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 10,
              boxHeight: 10,
              usePointStyle: true,
              pointStyle: 'circle',
              padding: 14,
              font: {
                family: "'Inter', sans-serif",
                size: 12,
                weight: '500'
              },
              color: '#475569'
            }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            titleFont: { family: "'Inter', sans-serif", size: 13, weight: '600' },
            bodyFont: { family: "'Inter', sans-serif", size: 12 },
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                const val = context.raw || 0;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percent = total > 0 ? Math.round((val / total) * 100) : 0;
                return ` ${context.label}: ${this.formatMoney(val, currency)} (${percent}%)`;
              }
            }
          }
        }
      }
    });
  }

  // Inicializa o actualiza el gráfico de barras (Ingresos vs Gastos Mensuales)
  updateBarChart(historyData, currency = '$') {
    const canvas = document.getElementById('monthlyBarChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    if (this.barChart) {
      this.barChart.data.labels = historyData.labels;
      this.barChart.data.datasets[0].data = historyData.incomes;
      this.barChart.data.datasets[1].data = historyData.expenses;
      this.barChart.update();
      return;
    }

    this.barChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: historyData.labels,
        datasets: [
          {
            label: 'Ingresos',
            data: historyData.incomes,
            backgroundColor: '#10b981',
            borderRadius: 6,
            borderSkipped: false,
            barPercentage: 0.6,
            categoryPercentage: 0.7
          },
          {
            label: 'Gastos',
            data: historyData.expenses,
            backgroundColor: '#f43f5e',
            borderRadius: 6,
            borderSkipped: false,
            barPercentage: 0.6,
            categoryPercentage: 0.7
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            align: 'end',
            labels: {
              boxWidth: 10,
              boxHeight: 10,
              usePointStyle: true,
              pointStyle: 'circle',
              padding: 12,
              font: {
                family: "'Inter', sans-serif",
                size: 12,
                weight: '500'
              },
              color: '#475569'
            }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            titleFont: { family: "'Inter', sans-serif", size: 13, weight: '600' },
            bodyFont: { family: "'Inter', sans-serif", size: 12 },
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                return ` ${context.dataset.label}: ${this.formatMoney(context.raw, currency)}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              font: { family: "'Inter', sans-serif", size: 12 },
              color: '#64748b'
            }
          },
          y: {
            border: { dash: [4, 4], color: 'transparent' },
            grid: {
              color: '#f1f5f9'
            },
            ticks: {
              font: { family: "'Inter', sans-serif", size: 11 },
              color: '#94a3b8',
              callback: (val) => `${currency}${val.toLocaleString('es-ES')}`
            }
          }
        }
      }
    });
  }
}

const budgetCharts = new BudgetCharts();
