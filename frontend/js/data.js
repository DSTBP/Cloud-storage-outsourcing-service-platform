// API基础URL
const API_BASE_URL = 'http://localhost:6666';

// 图表实例
let fileTypeChart = null;
let storageTrendChart = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 获取统计数据
        const statsResponse = await fetch(`${API_BASE_URL}/stats`);
        const stats = await statsResponse.json();

        // 更新概览卡片
        updateOverviewCards(stats);

        // 获取文件类型分布数据
        const fileTypesResponse = await fetch(`${API_BASE_URL}/stats/file-types`);
        const fileTypes = await fileTypesResponse.json();

        // 创建文件类型分布图表
        createFileTypeChart(fileTypes);

        // 获取存储趋势数据
        const storageTrendResponse = await fetch(`${API_BASE_URL}/stats/storage-trend`);
        const storageTrend = await storageTrendResponse.json();

        // 创建存储趋势图表
        createStorageTrendChart(storageTrend);

        // 更新详细数据表格
        updateFileDetailTable(fileTypes);
    } catch (error) {
        console.error('加载数据错误:', error);
        alert('加载数据时发生错误');
    }
});

// 更新概览卡片
function updateOverviewCards(stats) {
    document.getElementById('totalFiles').textContent = stats.totalFiles.toLocaleString();
    document.getElementById('totalStorage').textContent = formatFileSize(stats.totalStorage);
    document.getElementById('activeUsers').textContent = stats.activeUsers.toLocaleString();
    document.getElementById('avgFileSize').textContent = formatFileSize(stats.avgFileSize);

    // 更新增长率
    document.getElementById('filesGrowth').textContent = formatGrowth(stats.filesGrowth);
    document.getElementById('storageGrowth').textContent = formatGrowth(stats.storageGrowth);
    document.getElementById('usersGrowth').textContent = formatGrowth(stats.usersGrowth);
    document.getElementById('sizeGrowth').textContent = formatGrowth(stats.sizeGrowth);
}

// 创建文件类型分布图表
function createFileTypeChart(data) {
    const ctx = document.getElementById('fileTypeChart').getContext('2d');
    
    if (fileTypeChart) {
        fileTypeChart.destroy();
    }

    fileTypeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.type),
            datasets: [{
                data: data.map(item => item.count),
                backgroundColor: [
                    '#4a6cf7',
                    '#6c757d',
                    '#28a745',
                    '#ffc107',
                    '#17a2b8',
                    '#dc3545'
                ],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const value = context.raw;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });
}

// 创建存储趋势图表
function createStorageTrendChart(data) {
    const ctx = document.getElementById('storageTrendChart').getContext('2d');
    
    if (storageTrendChart) {
        storageTrendChart.destroy();
    }

    storageTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => item.date),
            datasets: [{
                label: '存储使用量',
                data: data.map(item => item.storage),
                borderColor: '#4a6cf7',
                backgroundColor: 'rgba(74, 108, 247, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#4a6cf7',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `存储使用量: ${formatFileSize(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatFileSize(value);
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// 更新详细数据表格
function updateFileDetailTable(data) {
    const tbody = document.getElementById('fileDetailTable');
    tbody.innerHTML = '';

    const totalFiles = data.reduce((sum, item) => sum + item.count, 0);
    const totalSize = data.reduce((sum, item) => sum + item.size, 0);

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.type}</td>
            <td>${item.count.toLocaleString()}</td>
            <td>${formatFileSize(item.size)}</td>
            <td>${formatFileSize(item.size / item.count)}</td>
            <td>${((item.count / totalFiles) * 100).toFixed(1)}%</td>
        `;
        tbody.appendChild(tr);
    });
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化增长率
function formatGrowth(growth) {
    const prefix = growth >= 0 ? '+' : '';
    return `${prefix}${growth.toFixed(1)}%`;
} 