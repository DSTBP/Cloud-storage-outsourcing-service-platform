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

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus()
    // 初始化 AOS 动画库
    AOS.init();
    
    const dropZone = document.getElementById('dropZone');
    const selectFileBtn = document.getElementById('selectFileBtn');
    const fileList = document.getElementById('fileList');
    const fileItemTemplate = document.getElementById('fileItemTemplate');
    
    // 存储上传任务
    const uploadTasks = new Map();
    
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
    
    // 格式化文件大小
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 选择文件按钮点击事件
    selectFileBtn.addEventListener('click', async () => {
        try {
            const filePath = await window.pywebview.api.select_file();
            if (filePath) {
                createUploadTask(filePath);
            }
        } catch (error) {
            showToast('选择文件失败: ' + error.message);
        }
    });
    
    // 拖放文件处理
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            const filePath = e.dataTransfer.files[0].path;
            createUploadTask(filePath);
        }
    });
    
    // 创建上传任务
    function createUploadTask(filePath) {
        const fileName = filePath.split('\\').pop();
        const taskId = Date.now().toString();
        
        // 创建文件列表项
        const fileItem = fileItemTemplate.content.cloneNode(true).querySelector('.file-item');
        fileItem.dataset.taskId = taskId;
        fileItem.dataset.filePath = filePath;
        
        // 设置文件图标
        const fileIcon = fileItem.querySelector('.bi');
        fileIcon.className = `bi ${getFileIcon(fileName)} me-3 fs-4`;
        
        // 设置文件名
        fileItem.querySelector('.file-name').textContent = fileName;
        
        // 设置取消按钮事件
        const cancelBtn = fileItem.querySelector('.cancel-btn');
        cancelBtn.addEventListener('click', () => cancelUpload(taskId));
        
        // 设置重试按钮事件
        const retryBtn = fileItem.querySelector('.retry-btn');
        retryBtn.addEventListener('click', () => retryUpload(taskId));
        
        // 添加到文件列表
        fileList.insertBefore(fileItem, fileList.firstChild);
        
        // 开始上传
        startUpload(taskId);
    }
    
    // 开始上传
    async function startUpload(taskId) {
        const fileItem = document.querySelector(`.file-item[data-task-id="${taskId}"]`);
        const filePath = fileItem.dataset.filePath;
        const progressBar = fileItem.querySelector('.progress-bar');
        const statusText = fileItem.querySelector('.file-status');
        const cancelBtn = fileItem.querySelector('.cancel-btn');
        const retryBtn = fileItem.querySelector('.retry-btn');
        
        try {
            // 重置状态
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', 0);
            progressBar.classList.remove('bg-danger');
            progressBar.classList.add('bg-primary', 'progress-bar-animated');
            statusText.textContent = '准备上传...';
            cancelBtn.style.display = 'inline-block';
            retryBtn.style.display = 'none';
            
            // 从sessionStorage获取必要参数
            const systemCenterUrl = sessionStorage.getItem('systemCenterAddress');
            const systemParams = JSON.parse(sessionStorage.getItem('systemParameters'));
            const username = sessionStorage.getItem('username');
            
            if (!systemCenterUrl || !systemParams || !username) {
                throw new Error('缺少必要的系统参数');
            }
            
            // 调用Python API上传文件
            const fileUuid = await window.pywebview.api.upload_file(
                systemCenterUrl,
                systemParams,
                filePath,
                username
            );
            
            // 更新状态为成功
            progressBar.style.width = '100%';
            progressBar.setAttribute('aria-valuenow', 100);
            progressBar.classList.remove('progress-bar-animated');
            statusText.textContent = '上传成功';
            cancelBtn.style.display = 'none';
            
            showToast('文件上传成功', 'success');
            
        } catch (error) {
            // 更新状态为失败
            progressBar.style.width = '100%';
            progressBar.classList.remove('progress-bar-animated', 'bg-primary');
            progressBar.classList.add('bg-danger');
            statusText.textContent = `上传失败: ${error.message}`;
            cancelBtn.style.display = 'none';
            retryBtn.style.display = 'inline-block';
            
            showToast('上传失败: ' + error.message);
        }
    }
    
    // 取消上传
    function cancelUpload(taskId) {
        const fileItem = document.querySelector(`.file-item[data-task-id="${taskId}"]`);
        if (fileItem) {
            fileItem.remove();
        }
    }
    
    // 重试上传
    function retryUpload(taskId) {
        startUpload(taskId);
    }
    
    // 更新上传进度
    window.updateUploadProgress = async function(progress, message) {
        const fileItem = document.querySelector('.file-item');
        if (fileItem) {
            const progressBar = fileItem.querySelector('.progress-bar');
            const statusText = fileItem.querySelector('.file-status');
            
            // 平滑更新进度
            const currentProgress = parseInt(progressBar.getAttribute('aria-valuenow'));
            const step = (progress - currentProgress) / 10;
            
            for (let i = 0; i <= 10; i++) {
                const currentValue = currentProgress + step * i;
                progressBar.style.width = `${currentValue}%`;
                progressBar.setAttribute('aria-valuenow', currentValue);
                await new Promise(resolve => setTimeout(resolve, 50)); // 每一小步延时50ms
            }
            
            statusText.textContent = message;
            await new Promise(resolve => setTimeout(resolve, 500)); // 完成后额外停留0.5s
        }
    };
    
    // 侧边栏切换
    document.getElementById('sidebarToggle').addEventListener('click', function() {
        document.querySelector('.sidebar').classList.toggle('show');
    });

    // 清除已完成按钮点击事件
    document.getElementById('clearCompleted').addEventListener('click', function() {
        const completedItems = document.querySelectorAll('.file-item .file-status');
        completedItems.forEach(item => {
            if (item.textContent === '上传成功') {
                item.closest('.file-item').remove();
            }
        });
    });
});
