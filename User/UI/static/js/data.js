/*
 * @Description: 
 * @Author: DSTBP
 * @Date: 2025-04-17 08:44:22
 * @LastEditTime: 2025-04-17 08:49:31
 * @LastEditors: DSTBP
 */

// 检查登录状态
function checkLoginStatus() {
    const userId = localStorage.getItem('userId');
    if (!userId) {
        localStorage.clear();
        window.location.href = 'auth.html';
        return;
    }

    // 显示用户名
    document.getElementById('username').textContent = localStorage.getItem('username') || '用户';
}

// 初始化 AOS 动画
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true
    });

    // 加载数据分析
    loadDataAnalysis();
});

// 加载数据分析
function loadDataAnalysis() {
    // 这里应该从后端API获取数据
    // 示例数据
    const data = {
        totalFiles: 156,
        storageUsed: 6.5,
        uploadCount: 89,
        downloadCount: 234,
        storageTrend: {
            labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
            data: [2.1, 2.8, 3.5, 4.2, 5.0, 6.5]
        },
        fileTypes: {
            labels: ['文档', '图片', '视频', '音频', '其他'],
            data: [45, 30, 15, 5, 5]
        },
        activities: [
            {
                type: 'upload',
                fileName: '项目报告.pdf',
                time: '2024-03-15 14:30',
                size: '2.5 MB'
            },
            {
                type: 'download',
                fileName: '设计图.jpg',
                time: '2024-03-15 13:45',
                size: '1.8 MB'
            },
            {
                type: 'upload',
                fileName: '会议记录.docx',
                time: '2024-03-15 10:20',
                size: '0.5 MB'
            }
        ]
    };

    // 更新概览数据
    updateOverview(data);
    
    // 创建图表
    createStorageTrendChart(data.storageTrend);
    createFileTypeChart(data.fileTypes);
    
    // 更新活动记录
    updateActivities(data.activities);
}

// 更新概览数据
function updateOverview(data) {
    document.getElementById('totalFiles').textContent = data.totalFiles;
    document.getElementById('storageUsed').textContent = `${data.storageUsed} GB`;
    document.getElementById('uploadCount').textContent = data.uploadCount;
    document.getElementById('downloadCount').textContent = data.downloadCount;
}

// 创建存储使用趋势图表
function createStorageTrendChart(data) {
    const ctx = document.getElementById('storageTrendChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: '存储使用量 (GB)',
                data: data.data,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                fill: true,
                backgroundColor: 'rgba(75, 192, 192, 0.1)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '存储使用趋势'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 创建文件类型分布图表
function createFileTypeChart(data) {
    const ctx = document.getElementById('fileTypeChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)',
                    'rgb(255, 205, 86)',
                    'rgb(75, 192, 192)',
                    'rgb(153, 102, 255)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: '文件类型分布'
                }
            }
        }
    });
}

// 更新活动记录
function updateActivities(activities) {
    const activityList = document.getElementById('activityList');
    activityList.innerHTML = '';

    activities.forEach(activity => {
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        
        const icon = activity.type === 'upload' ? 'bi-upload' : 'bi-download';
        const typeText = activity.type === 'upload' ? '上传' : '下载';
        
        activityItem.innerHTML = `
            <div class="activity-icon">
                <i class="bi ${icon}"></i>
            </div>
            <div class="activity-info">
                <div class="activity-title">
                    <span class="activity-type">${typeText}</span>
                    <span class="activity-file">${activity.fileName}</span>
                </div>
                <div class="activity-details">
                    <span class="activity-time">${activity.time}</span>
                    <span class="activity-size">${activity.size}</span>
                </div>
            </div>
        `;
        
        activityList.appendChild(activityItem);
    });
}

// 添加退出功能
document.getElementById('logout').addEventListener('click', function(e) {
    e.preventDefault();
    localStorage.removeItem('loginResponse');
    window.location.href = 'auth.html';
});
