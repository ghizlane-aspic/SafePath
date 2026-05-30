/**
 * Chart.js Configuration for Drowsiness Timeline
 */

let drowsinessChart;
const maxDataPoints = 60; // 60 seconds of data
const chartData = {
    labels: [],
    datasets: [{
        label: 'Drowsiness Score',
        data: [],
        borderColor: '#e8a838',
        backgroundColor: 'rgba(232, 168, 56, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#e8a838',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2
    }]
};

/**
 * Initialize the drowsiness chart
 */
function initializeChart() {
    const ctx = document.getElementById('drowsiness-chart').getContext('2d');
    
    // Initialize with empty data
    for (let i = 0; i < maxDataPoints; i++) {
        chartData.labels.push('');
        chartData.datasets[0].data.push(0);
    }
    
    drowsinessChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 300
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#e8a838',
                    borderColor: '#e8a838',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return 'Score: ' + context.parsed.y + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        display: false
                    }
                },
                y: {
                    display: true,
                    min: 0,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#6b7280',
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        },
        plugins: [{
            // Custom plugin to draw threshold line
            id: 'thresholdLine',
            afterDatasetsDraw: function(chart) {
                const ctx = chart.ctx;
                const yAxis = chart.scales.y;
                const xAxis = chart.scales.x;
                const thresholdValue = 70; // Alert threshold
                const y = yAxis.getPixelForValue(thresholdValue);
                
                ctx.save();
                ctx.strokeStyle = '#dc2626';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(xAxis.left, y);
                ctx.lineTo(xAxis.right, y);
                ctx.stroke();
                
                // Draw label
                ctx.fillStyle = '#dc2626';
                ctx.font = '12px Inter';
                ctx.fillText('Alert Threshold', xAxis.right - 110, y - 5);
                ctx.restore();
            }
        }]
    });
}

/**
 * Update chart with new drowsiness score
 * @param {number} score - Drowsiness score (0-100)
 */
function updateChart(score) {
    if (!drowsinessChart) return;
    
    // Add new data point
    chartData.datasets[0].data.push(score);
    chartData.labels.push('');
    
    // Remove oldest data point if we exceed max
    if (chartData.datasets[0].data.length > maxDataPoints) {
        chartData.datasets[0].data.shift();
        chartData.labels.shift();
    }
    
    // Update line color based on score
    if (score >= 70) {
        chartData.datasets[0].borderColor = '#dc2626';
        chartData.datasets[0].backgroundColor = 'rgba(220, 38, 38, 0.1)';
    } else if (score >= 30) {
        chartData.datasets[0].borderColor = '#f59e0b';
        chartData.datasets[0].backgroundColor = 'rgba(245, 158, 11, 0.1)';
    } else {
        chartData.datasets[0].borderColor = '#34d399';
        chartData.datasets[0].backgroundColor = 'rgba(52, 211, 153, 0.1)';
    }
    
    // Update the chart
    drowsinessChart.update('none'); // 'none' mode for better performance
}

/**
 * Reset chart data
 */
function resetChart() {
    if (!drowsinessChart) return;
    
    chartData.datasets[0].data = new Array(maxDataPoints).fill(0);
    chartData.labels = new Array(maxDataPoints).fill('');
    drowsinessChart.update();
}
