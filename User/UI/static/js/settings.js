/*
 * @Description: 
 * @Author: DSTBP
 * @Date: 2025-04-17 08:39:10
 * @LastEditTime: 2025-04-18 21:35:09
 * @LastEditors: DSTBP
 */
// 初始化页面
function initPage() {
    checkLoginStatus();
    loadConfigSettings();
    loadKeySettings();
    loadAvatar();
    initSystemParameters();
    bindAllEvents();
    AOS.init(); // 初始化AOS动画
}

// 检查登录状态
function checkLoginStatus() {
    const userId = sessionStorage.getItem('userId');
    if (!userId) {
        sessionStorage.clear();
        location.href = 'auth.html';
        return;
    }
    const usernameEl = document.getElementById('username');
    if (usernameEl) {
        usernameEl.textContent = sessionStorage.getItem('username') || '用户';
    }
}

// 加载配置设置
function loadConfigSettings() {
    const addr = sessionStorage.getItem('systemCenterAddress') || '';
    const path = sessionStorage.getItem('filePath') || '';
    const params = sessionStorage.getItem('systemParameters') || '{}';

    document.getElementById('systemCenterAddress').value = addr;
    document.getElementById('filePath').value = path;

    try {
        document.getElementById('systemParameters').value = JSON.stringify(JSON.parse(params), null, 2);
    } catch {
        document.getElementById('systemParameters').value = '{}';
    }
}

// 加载密钥设置
function loadKeySettings() {
    const rawPublicKey = sessionStorage.getItem('publicKey');
    const rawPrivateKey = sessionStorage.getItem('privateKey');
    document.getElementById('publicKey').value = (!rawPublicKey || rawPublicKey === 'null') ? '' : rawPublicKey;
    document.getElementById('privateKey').value = (!rawPrivateKey || rawPrivateKey === 'null') ? '' : rawPrivateKey;
}

// 显示头像
function loadAvatar() {
    const avatar = sessionStorage.getItem('avatar');
    document.getElementById('avatarPreview').src = (avatar && avatar !== 'null') ? avatar : './static/images/default-avatar.png';
}

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
    if (p1) {
        document.getElementById('systemParameters').value = p1;
    }
    else {
        const params = await getSystemParameters();
        if (params) {
            const system_param = JSON.stringify(params, null, 2)
            sessionStorage.setItem('systemParameters', system_param)
            document.getElementById('systemParameters').value = system_param;
        }
    }
}

// 显示提示
function showToast(message, type = 'success') {
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

// 保存到文件
function saveKeyToFile(key, defaultFilename) {
    const blob = new Blob([key], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = defaultFilename; // 直接使用默认文件名
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
}

// 绑定所有事件
function bindAllEvents() {
    const $ = (id) => document.getElementById(id);

    // 生成密钥对
    $('generateKeys')?.addEventListener('click', async () => {
        try {
            const systemParams = JSON.parse(sessionStorage.getItem('systemParameters'));
            const keypair = await window.pywebview.api.generate_keypair(systemParams);
            
            if (keypair && keypair.private_key && keypair.public_key) {
                // 保存到sessionStorage
                sessionStorage.setItem('privateKey', keypair.private_key.replace(/\n/g,'<br>'));
                sessionStorage.setItem('publicKey', keypair.public_key.replace(/\n/g,'<br>'));
                
                // 更新UI显示
                $('privateKey').value = keypair.private_key.replace(/\n/g,'<br>');
                $('publicKey').value = keypair.public_key.replace(/\n/g,'<br>');
                
                showToast('密钥对生成成功', 'success');
            } else {
                throw new Error('生成密钥对失败');
            }
        } catch (err) {
            console.error('生成密钥对失败:', err);
            showToast('生成密钥对失败: ' + err.message, 'error');
        }
    });

    // 配置保存
    $('saveConfigSettings')?.addEventListener('click', async () => {
        const addr = $('systemCenterAddress').value;
        const path = $('filePath').value;
        if (!addr || !path) return showToast('请填写完整设置', 'error');

        sessionStorage.setItem('systemCenterAddress', addr);
        sessionStorage.setItem('filePath', path);

        const params = await getSystemParameters();
        $('systemParameters').value = JSON.stringify(params || {}, null, 2);
        showToast(params ? '配置设置已保存，系统参数已刷新' : '配置设置已保存，但获取系统参数失败', params ? 'success' : 'warning');
    });

    // 地址变更监听
    $('systemCenterAddress')?.addEventListener('change', async (e) => {
        const addr = e.target.value;
        sessionStorage.setItem('systemCenterAddress', addr);
        const params = await getSystemParameters();
        $('systemParameters').value = JSON.stringify(params || {}, null, 2);
        showToast(params ? '系统参数已刷新' : '获取失败', params ? 'success' : 'warning');
    });

    // 密钥保存
    $('saveKeySettings')?.addEventListener('click', () => {
        const pub = sessionStorage.getItem('publicKey');
        const pri = sessionStorage.getItem('privateKey');
        if (!pub || !pri) return showToast('请填写公私钥', 'error');
        sessionStorage.setItem('publicKey', pub);
        sessionStorage.setItem('privateKey', pri);
        showToast('密钥设置已保存');
    });

    // 文件路径选择
    $('selectFilePath')?.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.addEventListener('change', (e) => {
            $('filePath').value = e.target.files[0]?.path || '';
        });
        input.click();
    });

    // 密钥路径选择
    $('selectKeyPath')?.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.addEventListener('change', (e) => {
            $('keyPath').value = e.target.files[0]?.path || '';
        });
        input.click();
    });

    // 公钥选择文件
    $('selectPublicKey')?.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.pem,.key';
        input.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                $('publicKey').value = text.replace(/\n/g,'<br>');
                sessionStorage.setItem('publicKey', text.replace(/\n/g,'<br>'));
                showToast('公钥已加载', 'success');
            } catch (err) {
                console.error('读取公钥文件失败:', err);
                showToast('读取公钥文件失败', 'error');
            }
        });
        input.click();
    });

    // 私钥选择文件
    $('selectPrivateKey')?.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.pem,.key';
        input.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                $('privateKey').value = text.replace(/\n/g,'<br>');
                sessionStorage.setItem('privateKey', text.replace(/\n/g,'<br>'));
                showToast('私钥已加载', 'success');
            } catch (err) {
                console.error('读取私钥文件失败:', err);
                showToast('读取私钥文件失败', 'error');
            }
        });
        input.click();
    });

    // 公钥复制
    $('copyPublicKey')?.addEventListener('click', () => {
        const publicKey = $('publicKey').value.replace(/<br\s*\/?>/gi, '\n');
        if (!publicKey) {
            showToast('没有可复制的公钥', 'error');
            return;
        }
        navigator.clipboard.writeText(publicKey)
            .then(() => showToast('公钥已复制到剪贴板', 'success'))
            .catch(() => showToast('复制失败', 'error'));
    });

    // 私钥复制
    $('copyPrivateKey')?.addEventListener('click', () => {
        const privateKey = $('privateKey').value.replace(/<br\s*\/?>/gi, '\n');
        if (!privateKey) {
            showToast('没有可复制的私钥', 'error');
            return;
        }
        navigator.clipboard.writeText(privateKey)
            .then(() => showToast('私钥已复制到剪贴板', 'success'))
            .catch(() => showToast('复制失败', 'error'));
    });

    // 公钥保存文件
    $('savePublicKey')?.addEventListener('click', async () => {
        const publicKey = $('publicKey').value.replace(/<br\s*\/?>/gi, '\n');
        if (!publicKey) {
            showToast('没有可保存的公钥', 'error');
            return;
        }
        try {
            const savePath = await window.pywebview.api.save_file('public_key.pem');
            if (savePath) {
                await window.pywebview.api.write_file(savePath, publicKey);
                showToast('公钥已保存', 'success');
            }
        } catch (err) {
            console.error('保存公钥失败:', err);
            showToast('保存公钥失败: ' + err.message, 'error');
        }
    });

    // 私钥保存文件
    $('savePrivateKey')?.addEventListener('click', async () => {
        const privateKey = $('privateKey').value.replace(/<br\s*\/?>/gi, '\n');
        if (!privateKey) {
            showToast('没有可保存的私钥', 'error');
            return;
        }
        try {
            const savePath = await window.pywebview.api.save_file('private_key.pem');
            if (savePath) {
                await window.pywebview.api.write_file(savePath, privateKey);
                showToast('私钥已保存', 'success');
            }
        } catch (err) {
            console.error('保存私钥失败:', err);
            showToast('保存私钥失败: ' + err.message, 'error');
        }
    });

    // 通知设置保存（预留）
    $('saveNotificationSettings')?.addEventListener('click', () => {
        showToast('通知设置已保存');
    });

    // 密码显示切换
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('input');
            const icon = btn.querySelector('i');
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            icon.classList.toggle('bi-eye', !isPassword);
            icon.classList.toggle('bi-eye-slash', isPassword);
        });
    });

    // 头像上传
    $('uploadAvatar')?.addEventListener('click', () => $('avatarInput').click());
    $('avatarInput')?.addEventListener('change', handleAvatarUpload);

    // 上传公钥
    $('uploadPublicKey')?.addEventListener('click', async () => {
        const publicKey = $('publicKey').value.replace(/<br\s*\/?>/gi, '\n');
        const username = sessionStorage.getItem('username');
        const userId = sessionStorage.getItem('userId');
        const systemCenterAddress = sessionStorage.getItem('systemCenterAddress');

        if (!publicKey) {
            showToast('没有可上传的公钥', 'error');
            return;
        }
        if (!username || !userId) {
            showToast('请先登录', 'error');
            return;
        }
        if (!systemCenterAddress) {
            showToast('请先设置系统中心地址', 'error');
            return;
        }

        try {
            const response = await fetch(`${systemCenterAddress}/user/public_key`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    user_id: userId,
                    public_key: publicKey
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                showToast('公钥上传成功', 'success');
            } else {
                throw new Error(data.error_message || '上传失败');
            }
        } catch (err) {
            console.error('上传公钥失败:', err);
            showToast('上传公钥失败: ' + err.message, 'error');
        }
    });

    // 公私钥匹配验证
    $('matchKeyPair')?.addEventListener('click', async () => {
        const privateKey = $('privateKey').value.replace(/<br\s*\/?>/gi, '\n');
        const publicKey = $('publicKey').value.replace(/<br\s*\/?>/gi, '\n');

        if (!privateKey || !publicKey) {
            showToast('请先加载或生成密钥对', 'error');
            return;
        }

        try {
            const result = await window.pywebview.api.match_keypair(privateKey, publicKey);
            if (result === true) {
                showToast('公私钥匹配验证成功', 'success');
            } else {
                throw new Error('验证失败');
            }
        } catch (err) {
            console.error('公私钥匹配验证失败:', err);
            showToast('公私钥匹配验证失败: ' + err.message, 'error');
        }
    });
}

// 处理头像上传
function handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
    if (!allowed.includes(file.type)) return showToast('不支持的图片格式', 'error');
    if (file.size > 2 * 1024 * 1024) return showToast('图片不能超过2MB', 'error');

    const reader = new FileReader();
    reader.onload = async function(ev) {
        const base64 = ev.target.result;
        const userId = sessionStorage.getItem('userId');
        if (!userId) return showToast('请先登录', 'error');

        const addr = sessionStorage.getItem('systemCenterAddress');
        try {
            const res = await fetch(`${addr}/user/avatar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ user_id: userId, avatar: base64 }),
                mode: 'cors'
            });
            const data = await res.json();
            if (data.status === 'success') {
                document.getElementById('avatarPreview').src = base64;
                sessionStorage.setItem('avatar', base64);
                showToast('头像上传成功');
            } else {
                showToast(data.error_message || '上传失败', 'error');
            }
        } catch (err) {
            console.error(err);
            showToast('头像上传失败，请稍后再试', 'error');
        }
    };
    reader.readAsDataURL(file);
}

// 启动
document.addEventListener('DOMContentLoaded', initPage);
