document.addEventListener('DOMContentLoaded', function() {
    // 设置默认系统中心地址
    if (!localStorage.getItem('systemCenterAddress')) {
        localStorage.setItem('systemCenterAddress', 'http://10.24.37.5:8085');
    }

    const loginForm = document.getElementById('login');
    const username = document.getElementById('username');
    const password = document.getElementById('password');
    const togglePassword = document.getElementById('togglePassword');

    // 用户名验证规则
    const usernamePattern = /^[\u4e00-\u9fa5a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};:'",.<>/?]{3,12}$/;
    
    // 密码验证规则
    const passwordRules = {
        length: password => password.length >= 8 && password.length <= 20,
        uppercase: password => /[A-Z]/.test(password),
        lowercase: password => /[a-z]/.test(password),
        number: password => /[0-9]/.test(password),
        special: password => /[!@#$%^&*()_+\-=\[\]{};:'",.<>/?]/.test(password)
    };

    // 切换密码显示/隐藏
    function setupPasswordToggle() {
        togglePassword.addEventListener('click', function() {
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            
            // 获取按钮内的图标元素
            const icon = this.querySelector('i');
            if (type === 'password') {
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            } else {
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            }
        });
    }

    setupPasswordToggle();

    // 验证用户名
    function validateUsername(username) {
        if (!usernamePattern.test(username)) {
            return '用户名长度必须在3-12字符之间，且只能包含中文、英文、数字和特殊符号';
        }
        return '';
    }

    // 验证密码
    // 验证密码强度
    function validatePassword(password, username) {
        if (password === username) {
            return '密码不能与用户名相同';
        }

        const validations = [
            passwordRules.length(password),
            passwordRules.uppercase(password),
            passwordRules.lowercase(password),
            passwordRules.number(password),
            passwordRules.special(password)
        ];

        const validCount = validations.filter(Boolean).length;
        
        if (!passwordRules.length(password)) {
            return '密码长度必须在8-20位之间';
        }

        if (validCount < 4) { // 至少需要三类字符组合（不包括长度要求）
            return '密码必须包含大写字母、小写字母、数字、特殊字符中的至少三类';
        }

        return '';
    }

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

    // 高亮显示错误输入框
    function highlightInputError(input) {
        input.classList.add('is-invalid');
        // 移除错误高亮
        setTimeout(() => {
            input.classList.remove('is-invalid');
        }, 3000);
    }

    // 表单提交处理
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const usernameValue = username.value;
        const passwordValue = password.value;
        
        // 验证用户名
        const usernameError = validateUsername(usernameValue);
        if (usernameError) {
            highlightInputError(username);
            showToast(usernameError);
            return;
        }
        
        // 验证密码
        const passwordError = validatePassword(passwordValue, usernameValue);
        if (passwordError) {
            highlightInputError(password);
            showToast(passwordError);
            return;
        }

        // 使用 SHA256 加密密码
        const passwordHash = CryptoJS.SHA256(passwordValue).toString();

        // 准备发送到后端的数据
        const loginData = {
            username: usernameValue,
            password: passwordHash
        };

        // 从localStorage获取系统中心地址
        const systemCenterAddress = localStorage.getItem('systemCenterAddress');

        // 发送登录请求到后端
        fetch(`${systemCenterAddress}/user/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(loginData),
            mode: 'cors'  // 启用CORS
        })
        .then(response => {
            if (response.status === 429) {
                throw new Error('请求过于频繁，请稍后再试');
            }
            return response.json();
        })
        .then(async data => {
            if (data.status === 'success') {
                // 存储信息到 localStorage
                const userId = data.data.user_id;
                const public_key = data.data.public_key;
                const avatar = data.data.avatar;

                if (public_key !== null) {
                    const pem_key = await window.pywebview.api.keypair_format_conversion(public_key, "PEM");
                    localStorage.setItem('publicKey', pem_key.replace(/\n/g,'<br>'));
                } else {
                    localStorage.setItem('publicKey', null);
                }
                localStorage.setItem('userId', userId);
                localStorage.setItem('username', usernameValue);
                localStorage.setItem('avatar', avatar);

                showToast('登录成功！', 'success');
                // 登录成功后跳转到board页面
                setTimeout(() => {
                    window.location.href = 'board.html';
                }, 1500);
            } else {
                showToast(data.error_message || '登录失败，请重试');
            }
        })
        .catch(error => {
            console.error('登录错误:', error);
            showToast(error.message || '登录失败，请稍后重试');
        });
    });
});