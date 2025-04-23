// 验证IP地址和端口号的格式
function validateSystemAddress(address) {
    const regex = /^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$/;
    if (!regex.test(address)) {
        return false;
    }
    
    // 验证IP地址各部分是否在有效范围内
    const [ip, port] = address.split(':');
    const ipParts = ip.split('.');
    for (const part of ipParts) {
        const num = parseInt(part);
        if (num < 0 || num > 255) {
            return false;
        }
    }
    
    // 验证端口号是否在有效范围内
    const portNum = parseInt(port);
    return portNum >= 1 && portNum <= 65535;
}

// 显示错误提示
function showError(message) {
    const input = document.getElementById('systemAddress');
    input.classList.add('is-invalid');
    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    feedback.textContent = message;
    input.parentNode.appendChild(feedback);
}

// 清除错误提示
function clearError() {
    const input = document.getElementById('systemAddress');
    input.classList.remove('is-invalid');
    const feedback = input.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否已经设置过系统中心地址
    const savedAddress = sessionStorage.getItem('systemCenterAddress');
    if (!savedAddress) {
        // 显示弹窗
        const modal = new bootstrap.Modal(document.getElementById('systemAddressModal'));
        modal.show();
    }

    // 保存按钮点击事件
    document.getElementById('saveSystemAddress').addEventListener('click', function() {
        const address = document.getElementById('systemAddress').value.trim();
        clearError();

        if (!address) {
            showError('请输入系统中心地址');
            return;
        }

        if (!validateSystemAddress(address)) {
            showError('请输入有效的IP地址和端口号，格式如：192.168.12.3:2411');
            return;
        }

        // 保存到sessionStorage
        sessionStorage.setItem('systemCenterAddress', 'http://' + address);
        
        // 关闭弹窗
        const modal = bootstrap.Modal.getInstance(document.getElementById('systemAddressModal'));
        modal.hide();
    });

    // 显示页面内容
    document.getElementById('app').style.display = 'block';
}); 