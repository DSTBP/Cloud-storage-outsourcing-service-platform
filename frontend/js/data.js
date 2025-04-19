import { formatFileSize, formatGrowth } from './utils.js';
import { chartManager } from './charts.js';

export class DataManager {
    constructor() {
        this.stats = null;
    }

    updateOverviewCards(stats) {
        this.stats = stats;
        document.getElementById('totalFiles').textContent = stats.totalFiles.toLocaleString();
        document.getElementById('totalStorage').textContent = formatFileSize(stats.totalStorage);
        document.getElementById('activeUsers').textContent = stats.activeUsers.toLocaleString();
        document.getElementById('avgFileSize').textContent = formatFileSize(stats.avgFileSize);

        document.getElementById('filesGrowth').textContent = formatGrowth(stats.filesGrowth);
        document.getElementById('storageGrowth').textContent = formatGrowth(stats.storageGrowth);
        document.getElementById('usersGrowth').textContent = formatGrowth(stats.usersGrowth);
        document.getElementById('sizeGrowth').textContent = formatGrowth(stats.sizeGrowth);
    }

    updateFileDetailTable(data) {
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

    updateCharts(data) {
        chartManager.createFileTypeChart(data.fileTypes);
        chartManager.createStorageTrendChart(data.storageTrend);
    }
}

export const dataManager = new DataManager();