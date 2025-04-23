/*
 * @Description: 
 * @Author: DSTBP
 * @Date: 2025-04-16 16:56:03
 * @LastEditTime: 2025-04-20 19:57:53
 * @LastEditors: DSTBP
 */
// 获取系统参数
async function getSystemParameters() {
    const addr = sessionStorage.getItem('systemCenterAddress');
    if (!addr) return null;

    try {
        const res = await fetch(`${addr}/system/parameters`);
        const data = await res.json();
        if (data.status === 'success')
            return data.data;
        throw new Error(data.error_message);
    } catch (err) {
        console.error('获取系统参数失败:', err);
        return null;
    }
}

// 初始化系统参数
async function initSystemParameters() {
    const p1 = sessionStorage.getItem('systemParameters');
    const params = await getSystemParameters();
    if (params) {
        const system_param = JSON.stringify(params, null, 2)
        sessionStorage.setItem('systemParameters', system_param)
    }
}

// 检查登录状态并初始化页面
async function initializePage() {
    try {
        // 显示加载动画
        window.pageLoader.show();
        
        // 检查登录状态
        const userId = sessionStorage.getItem('userId');
        const username = sessionStorage.getItem('username');
        
        if (!userId || !username) {
            throw new Error('未登录');
        }

        // 验证登录状态的有效性（可以添加与服务器的验证）
        const systemCenterAddress = sessionStorage.getItem('systemCenterAddress');
        if (!systemCenterAddress) {
            throw new Error('系统配置缺失');
        }

        // 如果登录验证通过，显示页面内容
        document.getElementById('app').style.visibility = 'visible';
        
        // 初始化页面数据
        await initializeData();
        
        // 隐藏加载动画
        window.pageLoader.hide();
        
    } catch (error) {
        console.error('初始化失败:', error);
        // 如果未登录或验证失败，重定向到登录页面
        window.location.href = 'auth.html';
    }
}

// 初始化页面数据
async function initializeData() {
    try {
        // 设置用户信息
        document.getElementById('username').textContent = sessionStorage.getItem('username') || '用户';
    } catch (error) {
        console.error('数据初始化失败:', error);
        throw error;
    }
}

// 退出登录
function logout() {
    sessionStorage.removeItem('loginResponse');
    window.location.href = 'html/auth.html';
}

// 切换侧边栏显示状态
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

// 存储文件数据
let fileDataCache = [];
let filteredDataCache = [];

// 分页相关变量
let currentPage = 1;
let pageSize = 20;

// 加载统计数据
async function loadStatistics() {
    try {
        const systemCenterAddress = sessionStorage.getItem('systemCenterAddress');
        const username = sessionStorage.getItem('username');
        
        if (!systemCenterAddress || !username) {
            throw new Error('系统配置缺失');
        }

        // 获取文件列表
        const response = await fetch(`${systemCenterAddress}/file/list?username=${username}`);
        if (!response.ok) {
            throw new Error('获取文件列表失败');
        }

        const result = await response.json();
        if (result.status !== 'success') {
            throw new Error(result.error_message || '获取文件列表失败');
        }

        // 更新统计数据
        fileDataCache = result.data.files_info || [];
        filteredDataCache = fileDataCache;
        
        const totalFiles = fileDataCache.length;
        const totalStorage = fileDataCache.reduce((sum, file) => {
            const fileSize = file && file.file_size ? hexBlocksToNumber(file.file_size) : 0;
            return sum + fileSize;
        }, 0);
        const totalDownloads = fileDataCache.reduce((sum, file) => {
            const downloadCount = file && file.download_count ? hexBlocksToNumber(file.download_count) : 0;
            return sum + downloadCount;
        }, 0);
        const avgFileSize = totalFiles > 0 ? totalStorage / totalFiles : 0;

        document.getElementById('totalFiles').textContent = totalFiles;
        document.getElementById('totalStorage').textContent = formatFileSize(totalStorage);
        document.getElementById('totalDownload').textContent = totalDownloads;
        document.getElementById('avgFileSize').textContent = formatFileSize(avgFileSize);

        // 更新总数显示
        document.getElementById('totalItems').textContent = fileDataCache.length;

        // 更新文件类型饼图
        updateFileTypeChart(fileDataCache);
        
        // 更新下载排行图表
        updateDownloadChart(fileDataCache);

        // 渲染第一页
        currentPage = 1;
        renderCurrentPage();

    } catch (error) {
        showToast('加载统计数据失败：' + error.message);
    }
}

// 渲染文件列表
function renderFileList(files) {
    const fileListBody = document.getElementById('fileListBody');
    fileListBody.innerHTML = '';

    if (!files || files.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `
            <td colspan="9" class="text-center py-4">
                <i class="bi bi-inbox fs-1 text-muted"></i>
                <p class="mt-2 mb-0">暂无文件</p>
            </td>
        `;
        fileListBody.appendChild(emptyRow);
        return;
    }

    files.forEach(file => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <i class="bi ${getFileIcon(file.file_name)} me-2"></i>
                    <span class="text-truncate" title="${file.file_name}">${file.file_name}</span>
                </div>
            </td>
            <td>${getFileTypeName(file.file_name)}</td>
            <td>${formatFileSize(hexBlocksToNumber(file.file_size))}</td>
            <td>${file.upload_user}</td>
            <td>${formatDate(file.upload_time)}</td>
            <td>
                <div class="hash-container">
                    <div class="hash-text" title="点击复制">${file.file_hash || '无'}</div>
                </div>
            </td>
            <td>${hexBlocksToNumber(file.download_count)}</td>
            <td>
                <span class="status-badge ${file.status === 'active' ? 'bg-success' : 'bg-secondary'}">
                    ${getStatusText(file.status)}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-danger delete-btn" data-id="${file._id}">
                    <i class="bi bi-trash"></i> 删除
                </button>
            </td>
        `;
        fileListBody.appendChild(row);
    });

    // 添加删除按钮事件监听
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const fileId = this.getAttribute('data-id');
            await deleteFile(fileId);
        });
    });

    // 添加文件哈希点击复制功能
    document.querySelectorAll('.hash-text').forEach(hashText => {
        hashText.addEventListener('click', function() {
            const hash = this.textContent;
            if (hash && hash !== '无') {
                navigator.clipboard.writeText(hash).then(() => {
                    showToast('哈希值已复制到剪贴板', 'success');
                }).catch(() => {
                    showToast('复制失败');
                });
            }
        });
    });
}

// 渲染当前页的数据
function renderCurrentPage() {
    const totalItems = filteredDataCache.length;
    const totalPages = Math.ceil(totalItems / pageSize);
    const start = (currentPage - 1) * pageSize;
    const end = Math.min(start + pageSize, totalItems);
    const pageData = filteredDataCache.slice(start, end);
    
    // 更新分页信息
    document.getElementById('totalItems').textContent = totalItems;
    document.getElementById('currentPage').textContent = totalPages > 0 ? `${currentPage}/${totalPages}` : '0/0';
    
    // 更新按钮状态
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;

    // 渲染文件列表
    renderFileList(pageData);
}

// 综合筛选和排序
function filterFiles() {
    const searchText = document.getElementById('searchInput').value.toLowerCase();
    const selectedType = document.getElementById('fileTypeFilter').value;
    const sortBy = document.getElementById('sortFilter').value;
    const selectedDate = document.getElementById('dateFilter').value;
    
    // 从缓存的数据中筛选
    filteredDataCache = fileDataCache.filter(file => {
        const fileName = file.file_name.toLowerCase();
        const fileType = getFileTypeName(file.file_name);
        const uploadDate = new Date(Number(file.upload_time));
        const uploadDateStr = uploadDate.toISOString().split('T')[0]; // 获取YYYY-MM-DD格式
        
        // 文件名搜索
        const matchesSearch = fileName.includes(searchText);
        
        // 类型筛选
        const matchesType = selectedType === '' || fileType === selectedType;
        
        // 日期筛选
        const matchesDate = !selectedDate || uploadDateStr === selectedDate;
        
        return matchesSearch && matchesType && matchesDate;
    });
    
    // 排序
    filteredDataCache.sort((a, b) => {
        switch (sortBy) {
            case 'size':
                return hexBlocksToNumber(b.file_size) - hexBlocksToNumber(a.file_size);
            case 'downloads':
                return hexBlocksToNumber(b.download_count) - hexBlocksToNumber(a.download_count);
            case 'date':
                return Number(b.upload_time) - Number(a.upload_time);
            case 'name':
                return a.file_name.localeCompare(b.file_name);
            default:
                return 0;
        }
    });

    // 计算最大页数
    const maxPage = Math.ceil(filteredDataCache.length / pageSize);
    
    // 如果当前页超出新的最大页数，则调整到最后一页
    if (currentPage > maxPage) {
        currentPage = Math.max(1, maxPage);
    }
    
    // 渲染当前页
    renderCurrentPage();
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'active': '正常',
        'inactive': '已禁用',
        'deleted': '已删除'
    };
    return statusMap[status] || '未知';
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查登录状态
    initializePage();
    initSystemParameters();

    // 绑定退出按钮事件
    document.getElementById('logout').addEventListener('click', function(e) {
        e.preventDefault();
        logout();
    });

    // 绑定侧边栏切换按钮
    document.getElementById('sidebarToggle').addEventListener('click', toggleSidebar);

    // 初始化AOS动画
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true
    });

    // 加载统计数据
    loadStatistics();

    // 设置日期选择器的最大值为今天
    const dateFilter = document.getElementById('dateFilter');
    dateFilter.max = getTodayString();
    
    // 添加分页事件监听
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderCurrentPage();
        }
    });

    document.getElementById('nextPage').addEventListener('click', () => {
        const maxPage = Math.ceil(filteredDataCache.length / pageSize);
        if (currentPage < maxPage) {
            currentPage++;
            renderCurrentPage();
        }
    });

    document.getElementById('pageSizeSelect').addEventListener('change', (e) => {
        pageSize = parseInt(e.target.value);
        const maxPage = Math.ceil(filteredDataCache.length / pageSize);
        currentPage = Math.min(currentPage, maxPage);
        renderCurrentPage();
    });

    // 使用防抖处理搜索输入
    const debouncedFilter = debounce(() => filterFiles(), 300);
    document.getElementById('searchInput').addEventListener('input', debouncedFilter);
    document.getElementById('fileTypeFilter').addEventListener('change', filterFiles);
    document.getElementById('sortFilter').addEventListener('change', filterFiles);
    
    // 日期选择器处理
    const dateDisplay = document.getElementById('dateDisplay');
    dateFilter.addEventListener('change', (e) => {
        const selectedDate = e.target.value;
        if (selectedDate) {
            const date = new Date(selectedDate);
            dateDisplay.textContent = `${date.getFullYear()}年${String(date.getMonth() + 1).padStart(2, '0')}月${String(date.getDate()).padStart(2, '0')}日`;
        } else {
            dateDisplay.textContent = '所有日期';
        }
        filterFiles();
    });
});

// 获取今天的日期字符串
function getTodayString() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 添加防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 删除文件
async function deleteFile(fileId) {
    try {
        const systemCenterAddress = sessionStorage.getItem('systemCenterAddress');
        const username = sessionStorage.getItem('username');
        
        if (!systemCenterAddress || !username) {
            throw new Error('系统配置缺失');
        }

        const response = await fetch(`${systemCenterAddress}/file/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                file_uuid: fileId
            })
        });

        if (!response.ok) {
            throw new Error('删除文件失败');
        }

        const result = await response.json();
        if (result.status !== 'success') {
            throw new Error(result.error_message || '删除文件失败');
        }

        showToast('文件删除成功', 'success');
        // 重新加载统计数据和文件列表
        loadStatistics();

    } catch (error) {
        showToast('删除文件失败：' + error.message, 'error');
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化日期
function formatDate(timestamp) {
    const date = new Date(Number(timestamp));
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 获取文件图标
function getFileIcon(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(extension)) return 'bi-file-image';
    if (['mp4', 'avi', 'mov', 'wmv', 'flv'].includes(extension)) return 'bi-file-play';
    if (['mp3', 'wav', 'ogg', 'flac'].includes(extension)) return 'bi-file-music';
    if (extension === 'pdf') return 'bi-file-pdf';
    if (['doc', 'docx'].includes(extension)) return 'bi-file-word';
    if (['xls', 'xlsx'].includes(extension)) return 'bi-file-excel';
    if (['ppt', 'pptx'].includes(extension)) return 'bi-file-ppt';
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(extension)) return 'bi-file-zip';
    if (['txt', 'log', 'md'].includes(extension)) return 'bi-file-text';
    if (['js', 'py', 'java', 'cpp', 'cs', 'php', 'html', 'css'].includes(extension)) return 'bi-file-code';
    return 'bi-file-earmark';
}

// 获取文件类型名称
function getFileTypeName(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    const typeMap = {
        'jpg': '图片', 'jpeg': '图片', 'png': '图片', 'gif': '图片', 'bmp': '图片', 'webp': '图片',
        'mp4': '视频', 'avi': '视频', 'mov': '视频', 'wmv': '视频', 'flv': '视频',
        'mp3': '音频', 'wav': '音频', 'ogg': '音频', 'flac': '音频',
        'pdf': 'PDF文档',
        'doc': 'Word文档', 'docx': 'Word文档',
        'xls': 'Excel文档', 'xlsx': 'Excel文档',
        'ppt': 'PPT文档', 'pptx': 'PPT文档',
        'zip': '压缩文件', 'rar': '压缩文件', '7z': '压缩文件', 'tar': '压缩文件', 'gz': '压缩文件',
        'txt': '文本文件', 'log': '日志文件', 'md': 'Markdown文件',
        'js': '代码文件', 'py': '代码文件', 'java': '代码文件', 'cpp': '代码文件',
        'cs': '代码文件', 'php': '代码文件', 'html': '代码文件', 'css': '代码文件'
    };
    return typeMap[extension] || '其他文件';
}

// 显示提示消息
function showToast(message, type = 'error') {
    // 移除旧的提示框
    const oldToast = document.querySelector('.toast-container');
    if (oldToast) {
        oldToast.remove();
    }

    // 创建新的提示框
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
    toastContainer.style.zIndex = 9999;
    
    const toastEl = document.createElement('div');
    toastEl.className = 'toast show';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    const toastHeader = document.createElement('div');
    toastHeader.className = `toast-header ${type === 'error' ? 'bg-danger' : 'bg-success'} text-white`;
    
    const title = document.createElement('strong');
    title.className = 'me-auto';
    title.textContent = type === 'error' ? '错误' : '成功';
    
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close btn-close-white';
    closeButton.setAttribute('data-bs-dismiss', 'toast');
    closeButton.setAttribute('aria-label', '关闭');
    closeButton.onclick = () => toastContainer.remove();
    
    const toastBody = document.createElement('div');
    toastBody.className = 'toast-body';
    toastBody.textContent = message;
    
    toastHeader.appendChild(title);
    toastHeader.appendChild(closeButton);
    toastEl.appendChild(toastHeader);
    toastEl.appendChild(toastBody);
    toastContainer.appendChild(toastEl);
    document.body.appendChild(toastContainer);
    
    // 3秒后自动关闭
    setTimeout(() => {
        toastContainer.remove();
    }, 3000);
}

// 将十六进制块转换为数字
function hexBlocksToNumber(hexStr) {
    const cleanHex = hexStr.replace(/\s+/g, '');
    const bigIntValue = BigInt('0x' + cleanHex);
    const numberValue = Number(bigIntValue);

    if (!Number.isSafeInteger(numberValue)) {
        console.warn('超出Number安全范围');
        return bigIntValue;  // 返回BigInt以保证精度
    }
    return numberValue;
}

// 初始化文件类型饼图
function initFileTypeChart() {
    const chartDom = document.getElementById('fileTypeChart');
    const myChart = echarts.init(chartDom);
    
    // 监听窗口大小变化，调整图表大小
    window.addEventListener('resize', function() {
        myChart.resize();
    });

    return myChart;
}

// 更新文件类型饼图
function updateFileTypeChart(files) {
    // 统计各类型文件数量
    const typeCount = {};
    files.forEach(file => {
        const type = getFileTypeName(file.file_name);
        typeCount[type] = (typeCount[type] || 0) + 1;
    });

    // 准备图表数据
    const chartData = Object.entries(typeCount).map(([name, value]) => ({
        name,
        value
    }));

    // 配置图表选项
    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            data: chartData.map(item => item.name),
            textStyle: {
                fontSize: 12,
                color: '#4D8BFF',
            }
        },
        series: [
            {
                name: '文件类型',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: true,
                    position: 'outside',
                    formatter: '{b}\n{c} ({d}%)',
                    textStyle: {
                        fontSize: 12,
                        color: '#4D8BFF',
                    }
                },
                labelLine: {
                    show: true,
                    length: 20,
                    length2: 10,
                    smooth: true
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 14,
                        fontWeight: 'bold'
                    }
                },
                data: chartData
            }
        ]
    };

    // 应用配置
    const myChart = initFileTypeChart();
    myChart.setOption(option);
}

// 初始化下载排行图表
function initDownloadChart() {
    const chartDom = document.getElementById('downloadChart');
    const myChart = echarts.init(chartDom);
    
    // 监听窗口大小变化，调整图表大小
    window.addEventListener('resize', function() {
        myChart.resize();
    });

    return myChart;
}

// 更新下载排行图表
function updateDownloadChart(files) {
    // 按下载次数排序并取前10个文件
    const sortedFiles = [...files].sort((a, b) => {
        const aDownloads = hexBlocksToNumber(a.download_count);
        const bDownloads = hexBlocksToNumber(b.download_count);
        return bDownloads - aDownloads;
    }).slice(0, 10);

    // 准备图表数据
    const xAxisData = sortedFiles.map(file => file.file_name);
    const seriesData = sortedFiles.map(file => hexBlocksToNumber(file.download_count));

    // 配置图表选项
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                const file = sortedFiles[params[0].dataIndex];
                return `文件名: ${file.file_name}<br/>下载次数: ${params[0].value}<br/>上传时间: ${formatDate(file.upload_time)}`;
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            axisLabel: {
                formatter: '{value} 次'
            }
        },
        yAxis: {
            type: 'category',
            data: xAxisData,
            axisLabel: {
                interval: 0,
                formatter: function(value) {
                    // 文件名过长时截断显示
                    if (value.length > 15) {
                        return value.substring(0, 15) + '...';
                    }
                    return value;
                }
            }
        },
        series: [
            {
                name: '下载次数',
                type: 'bar',
                data: seriesData,
                itemStyle: {
                    color: function(params) {
                        // 使用渐变色
                        return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                            { offset: 0, color: '#83bff6' },
                            { offset: 0.5, color: '#188df0' },
                            { offset: 1, color: '#188df0' }
                        ]);
                    },
                    borderRadius: [0, 0, 0, 0]
                },
                emphasis: {
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                            { offset: 0, color: '#2378f7' },
                            { offset: 0.7, color: '#2378f7' },
                            { offset: 1, color: '#83bff6' }
                        ])
                    }
                }
            }
        ]
    };

    // 应用配置
    const myChart = initDownloadChart();
    myChart.setOption(option);
}