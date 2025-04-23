document.addEventListener('DOMContentLoaded', function() {
    // 设置默认系统中心地址
    if (!sessionStorage.getItem('systemCenterAddress')) {
        sessionStorage.setItem('systemCenterAddress', 'http://10.24.37.3:8085');
    }

    const registerForm = document.getElementById('register');
    const regUsername = document.getElementById('regUsername');
    const regPassword = document.getElementById('regPassword');
    const regConfirmPassword = document.getElementById('regConfirmPassword');
    const toggleRegPassword = document.getElementById('toggleRegPassword');
    const toggleRegConfirmPassword = document.getElementById('toggleRegConfirmPassword');

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
    function setupPasswordToggle(toggleBtn, passwordInput) {
        toggleBtn.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
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

    // 设置密码和确认密码的切换功能
    setupPasswordToggle(toggleRegPassword, regPassword);
    setupPasswordToggle(toggleRegConfirmPassword, regConfirmPassword);

    // 验证用户名
    function validateUsername(username) {
        if (!usernamePattern.test(username)) {
            return '用户名长度必须在3-12字符之间，且只能包含中文、英文、数字和特殊符号';
        }
        return '';
    }

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

    // 验证确认密码
    function validateConfirmPassword(password, confirmPassword) {
        if (password !== confirmPassword) {
            return '两次输入的密码不一致';
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
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = regUsername.value;
        const password = regPassword.value;
        const confirmPassword = regConfirmPassword.value;
        
        // 验证用户名
        const usernameError = validateUsername(username);
        if (usernameError) {
            highlightInputError(regUsername);
            showToast(usernameError);
            return;
        }
        
        // 验证密码
        const passwordError = validatePassword(password, username);
        if (passwordError) {
            highlightInputError(regPassword);
            showToast(passwordError);
            return;
        }
        
        // 验证确认密码
        const confirmPasswordError = validateConfirmPassword(password, confirmPassword);
        if (confirmPasswordError) {
            highlightInputError(regConfirmPassword);
            showToast(confirmPasswordError);
            return;
        }

        // 使用 SHA256 加密密码
        const passwordHash = CryptoJS.SHA256(password).toString();

        // 准备发送到后端的数据
        const registerData = {
            username: username,
            password: passwordHash
        };

        // 从sessionStorage获取系统中心地址
        const systemCenterAddress = sessionStorage.getItem('systemCenterAddress');

        // 发送注册请求到后端
        fetch(`${systemCenterAddress}/user/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(registerData),
            mode: 'cors'  // 启用CORS
        })
        .then(response => {
            if (response.status === 429) {
                throw new Error('请求过于频繁，请稍后再试');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                showToast('注册成功！', 'success');
                // 注册成功后跳转到登录页面
                setTimeout(() => {
                    window.location.href = 'auth.html';
                }, 1500);
            } else {
                showToast(data.error_message || '注册失败，请重试');
            }
        })
        .catch(error => {
            console.error('注册错误:', error);
            showToast(error.message || '注册失败，请稍后重试');
        });
    });
}); 