// API基础URL
const API_BASE_URL = 'http://localhost:6666';

// 全局状态
let currentUser = null;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 登录表单提交
    document.getElementById('login').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                const data = await response.json();
                currentUser = data.user;
                showFileManager();
            } else {
                alert('登录失败，请检查用户名和密码');
            }
        } catch (error) {
            console.error('登录错误:', error);
            alert('登录过程中发生错误');
        }
    });

    // 注册表单提交
    document.getElementById('register').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const password = document.getElementById('regPassword').value;
        
        try {
            const response = await fetch(`${API_BASE_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                alert('注册成功，请登录');
                showLogin();
            } else {
                alert('注册失败，用户名可能已存在');
            }
        } catch (error) {
            console.error('注册错误:', error);
            alert('注册过程中发生错误');
        }
    });

    // 文件上传处理
    document.getElementById('fileInput').addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${currentUser.token}`
                },
                body: formData
            });

            if (response.ok) {
                alert('文件上传成功');
                loadFiles();
            } else {
                alert('文件上传失败');
            }
        } catch (error) {
            console.error('上传错误:', error);
            alert('上传过程中发生错误');
        }
    });
});

// 显示登录表单
function showLogin() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('fileManager').style.display = 'none';
}

// 显示注册表单
function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('fileManager').style.display = 'none';
}

// 显示文件管理器
function showFileManager() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('fileManager').style.display = 'block';
    document.getElementById('welcomeUser').textContent = `欢迎, ${currentUser.username}`;
    loadFiles();
}

// 加载文件列表
async function loadFiles() {
    try {
        const response = await fetch(`${API_BASE_URL}/files`, {
            headers: {
                'Authorization': `Bearer ${currentUser.token}`
            }
        });

        if (response.ok) {
            const files = await response.json();
            renderFiles(files);
        } else {
            alert('获取文件列表失败');
        }
    } catch (error) {
        console.error('加载文件错误:', error);
        alert('加载文件列表时发生错误');
    }
}

// 渲染文件列表
function renderFiles(files) {
    const tbody = document.getElementById('fileTableBody');
    tbody.innerHTML = '';

    files.forEach(file => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${file.filename}</td>
            <td>${formatFileSize(file.size)}</td>
            <td>${new Date(file.uploadTime).toLocaleString()}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="downloadFile('${file._id}')">
                    <i class="bi bi-download"></i> 下载
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// 下载文件
async function downloadFile(fileId) {
    try {
        const response = await fetch(`${API_BASE_URL}/download/${fileId}`, {
            headers: {
                'Authorization': `Bearer ${currentUser.token}`
            }
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('Content-Disposition').split('filename=')[1];
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('文件下载失败');
        }
    } catch (error) {
        console.error('下载错误:', error);
        alert('下载过程中发生错误');
    }
}

// 退出登录
function logout() {
    currentUser = null;
    showLogin();
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
} 