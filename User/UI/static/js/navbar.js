// 处理导航栏逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 获取导航栏元素
    const userDropdown = document.getElementById('userDropdown');
    const usernameSpan = document.getElementById('username');
    const logoutLink = document.getElementById('logout');
    const profileLink = document.querySelector('.dropdown-menu li:nth-child(1) .dropdown-item');
    const settingsLink = document.querySelector('.dropdown-menu li:nth-child(2) .dropdown-item');

    // 设置用户名
    const username = localStorage.getItem('username');
    if (username) {
        usernameSpan.textContent = username;
    }

    // 个人资料和设置链接跳转到settings页面
    if (profileLink) {
        profileLink.href = 'settings.html';
    }
    if (settingsLink) {
        settingsLink.href = 'settings.html';
    }

    // 退出登录处理
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 清除用户相关数据
            localStorage.removeItem('username');
            localStorage.removeItem('avatar');
            localStorage.removeItem('userId');
            localStorage.removeItem('publicKey');
            
            // 跳转到登录页面
            window.location.href = 'auth.html';
        });
    }
}); 