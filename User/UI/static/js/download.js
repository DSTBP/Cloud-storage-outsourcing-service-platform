// 检查登录状态
function checkLoginStatus() {
    const userId = sessionStorage.getItem('userId');
    if (!userId) {
        sessionStorage.clear();
        window.location.href = 'auth.html';
        return;
    }

    // 显示用户名
    document.getElementById('username').textContent = sessionStorage.getItem('username') || '用户';
}

// 初始化 AOS 动画
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus()
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true
    });

    // 加载文件列表
    loadFileList();

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
    const dateFilter = document.getElementById('dateFilter');
    const dateDisplay = document.getElementById('dateDisplay');
    
    // 设置日期选择器的最大值为今天
    dateFilter.max = getTodayString();
    
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
    
    // 初始化日期显示
    dateDisplay.textContent = '所有日期';
});

// 创建并显示提示框
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

// 存储文件数据
let fileDataCache = [];
let filteredDataCache = [];

// 分页相关变量
let currentPage = 1;
let pageSize = 20;

// 加载文件列表
async function loadFileList() {
    const systemCenterAddress = sessionStorage.getItem('systemCenterAddress');
    if (!systemCenterAddress) {
        showToast('系统中心地址未配置');
        return;
    }

    try {
        const response = await fetch(`${systemCenterAddress}/file/list`);
        if (!response.ok) {
            throw new Error('获取文件列表失败');
        }
        const result = await response.json();

        // 检查返回的数据结构
        if (!result.data) {
            fileDataCache = []
            filteredDataCache = []
        } else {
            // 缓存文件数据
            fileDataCache = result.data.files_info;
            filteredDataCache = result.data.files_info;
        }

        // 更新总数显示
        document.getElementById('totalItems').textContent = fileDataCache.length;

        if (fileDataCache.length === 0) {
            showToast('暂无文件可下载', 'success');
            renderFileList([]);  // 显示空状态
        } else {
            // 渲染第一页
            currentPage = 1;
            renderCurrentPage();
        }
    } catch (error) {
        console.error('加载文件列表失败:', error);
        showToast('加载文件列表失败：' + error.message);
        // 显示空状态
        renderFileList([]);
    }
}

// 渲染文件列表
function renderFileList(files) {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';

    if (!files || files.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `
            <td colspan="9" class="empty-state">
                <i class="bi bi-inbox"></i>
                <p class="mb-0">暂无文件</p>
                <p class="small text-muted">当前列表为空</p>
            </td>
        `;
        fileList.appendChild(emptyRow);
        
        // 更新分页信息
        document.getElementById('totalItems').textContent = '0';
        document.getElementById('currentPage').textContent = '0/0';
        
        // 禁用分页按钮
        document.getElementById('prevPage').disabled = true;
        document.getElementById('nextPage').disabled = true;
        return;
    }

    files.forEach(file => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <i class="bi ${getFileIcon(file.file_name)} me-2"></i>
                    <span class="text-truncate" style="max-width: 200px;" title="${file.file_name}">
                        ${file.file_name}
                    </span>
                </div>
            </td>
            <td>${unifiedFileType(file.file_name)}</td>
            <td>${formatFileSize(file.file_size)}</td>
            <td>${file.upload_user}</td>
            <td>${formatDate(file.upload_time)}</td>
            <td>
                <div class="hash-container" data-hash="${file.file_hash}">
                    <div class="hash-text">${file.file_hash}</div>
                    <div class="copy-tooltip">点击复制哈希值</div>
                </div>
            </td>
            <td>${hexBlocksToNumber(file.download_count)}</td>
            <td>
                <span class="status-badge ${file.status === 'active' ? 'bg-success' : 'bg-secondary'}">
                    ${getStatusText(file.status)}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-primary download-btn" data-id="${file._id}" 
                    ${file.status !== 'active' ? 'disabled' : ''}>
                    <i class="bi bi-download"></i> 下载
                </button>
            </td>
        `;
        fileList.appendChild(row);
    });

    // 添加下载按钮事件监听
    document.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (!this.disabled) {
                const fileId = this.getAttribute('data-id');
                downloadFile(fileId);
            }
        });
    });

    // 添加哈希值复制功能
    document.querySelectorAll('.hash-container').forEach(container => {
        container.addEventListener('click', async function() {
            const hash = this.getAttribute('data-hash');
            try {
                await navigator.clipboard.writeText(hash);
                this.classList.add('copied');
                const tooltip = this.querySelector('.copy-tooltip');
                tooltip.textContent = '已复制！';
                setTimeout(() => {
                    this.classList.remove('copied');
                    tooltip.textContent = '点击复制哈希值';
                }, 2000);
            } catch (err) {
                showToast('复制失败：' + err.message);
            }
        });
    });
}

// 类型转换
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

// 格式化文件大小
function formatFileSize(hexStr) {
    const bytes = hexBlocksToNumber(hexStr)
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化日期
function formatDate(timestamp) {
    const date = new Date(Number(timestamp));
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}年${month}月${day}日 ${hour}:${minute}`;
}

// 格式化日期（仅年月日）
function formatDateYMD(timestamp) {
    const date = new Date(Number(timestamp));
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}年${month}月${day}日`;
}

// 获取今天的日期字符串（用于日期选择器）
function getTodayString() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
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
        'jpg': '图片',
        'jpeg': '图片',
        'png': '图片',
        'gif': '图片',
        'bmp': '图片',
        'webp': '图片',
        'mp4': '视频',
        'avi': '视频',
        'mov': '视频',
        'wmv': '视频',
        'flv': '视频',
        'mp3': '音频',
        'wav': '音频',
        'ogg': '音频',
        'flac': '音频',
        'pdf': 'PDF文档',
        'doc': 'Word文档',
        'docx': 'Word文档',
        'xls': 'Excel文档',
        'xlsx': 'Excel文档',
        'ppt': 'PPT文档',
        'pptx': 'PPT文档',
        'zip': '压缩文件',
        'rar': '压缩文件',
        '7z': '压缩文件',
        'tar': '压缩文件',
        'gz': '压缩文件',
        'txt': '文本文件',
        'log': '日志文件',
        'md': 'Markdown文件',
        'js': 'JavaScript文件',
        'py': 'Python文件',
        'java': 'Java文件',
        'cpp': 'C++文件',
        'cs': 'C#文件',
        'php': 'PHP文件',
        'html': 'HTML文件',
        'css': 'CSS文件'
    };
    return typeMap[extension] || '其他文件';
}

// 创建下载进度弹窗
function createDownloadModal() {
    // 检查是否已存在模态框
    let modal = document.getElementById('downloadModal');
    if (modal) {
        return new bootstrap.Modal(modal);
    }

    // 创建模态框
    modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'downloadModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', 'downloadModalLabel');
    modal.setAttribute('aria-hidden', 'true');

    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="downloadModalLabel">文件下载</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="progress">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" 
                             id="downloadProgress"
                             style="width: 0%" 
                             aria-valuenow="0" 
                             aria-valuemin="0" 
                             aria-valuemax="100">0%</div>
                    </div>
                    <div class="mt-2 text-center" id="downloadStatus">准备下载...</div>
                </div>
                <div class="modal-footer" style="display: none" id="downloadModalFooter">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    return new bootstrap.Modal(modal);
}

// 设置下载进度回调函数
window.download_progress_callback = function(progress, message) {
    updateDownloadProgress(progress, message);
};

function updateDownloadProgress(progress, status) {
    const progressBar = document.getElementById('downloadProgress');
    const statusText = document.getElementById('downloadStatus');
    
    if (progressBar && statusText) {
        // 平滑更新进度
        const currentProgress = parseInt(progressBar.getAttribute('aria-valuenow'));
        const step = (progress - currentProgress) / 10;
        
        for (let i = 0; i <= 10; i++) {
            setTimeout(() => {
                const currentValue = currentProgress + step * i;
                progressBar.style.width = `${currentValue}%`;
                progressBar.setAttribute('aria-valuenow', currentValue);
                progressBar.textContent = `${Math.round(currentValue)}%`;  // 添加百分比文本
                statusText.textContent = status;
            }, i * 30);
        }
    }
}

// 下载文件
async function downloadFile(fileId) {
    const systemCenterAddress = sessionStorage.getItem('systemCenterAddress');
    const systemParams = sessionStorage.getItem('systemParameters');
    const username = sessionStorage.getItem('username');
    const rawPrivateKey = sessionStorage.getItem('privateKey')
    const filePath = sessionStorage.getItem('filePath');

    const missingParams = [];
    if (!systemCenterAddress) missingParams.push('systemCenterAddress');
    if (!systemParams) missingParams.push('systemParameters');
    if (!username) missingParams.push('username');
    if (!rawPrivateKey) missingParams.push('privateKey');
    if (!filePath) missingParams.push('filePath');

    if (missingParams.length > 0) {
        showToast(`缺少必要的配置信息：${missingParams.join(', ')}`, 'error');
        return;
    }

    const privateKey = rawPrivateKey.replace(/<br\s*\/?>/gi, '\n')

    // 创建并显示进度弹窗
    const downloadModal = createDownloadModal();    
    try {
        downloadModal.show();
        
        await window.pywebview.api.download_file(
            systemCenterAddress,
            JSON.parse(systemParams),
            username,
            fileId,
            privateKey,
            filePath
        );
        
        showToast('文件下载成功', 'success');
        downloadModal.hide();
    } catch (error) {
        showToast('下载失败：' + error.message, 'error');
        downloadModal.hide();
    }
}

function unifiedFileType(fileName) {
    const res = getFileTypeName(fileName);
    const codeFiles = ['Markdown文件', 'JavaScript文件', 'Python文件', 'Java文件', 'C++文件', 'C#文件', 'PHP文件', 'HTML文件', 'CSS文件'];
    if (codeFiles.includes(res)) {
        return '代码文件';
    }
    const textFiles = ['文本文件', '日志文件'];
    if (textFiles.includes(res)) {
        return '文本文件';
    }
    return res;
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
        const fileType = unifiedFileType(file.file_name);
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
    
    // 显示筛选结果数量
    const totalItems = document.getElementById('totalItems');
    if (filteredDataCache.length === 0) {
        totalItems.textContent = '0';
        showToast('没有找到匹配的文件');
    } else {
        totalItems.textContent = filteredDataCache.length;
    }
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
