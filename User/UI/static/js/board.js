/*
 * @Description: 
 * @Author: DSTBP
 * @Date: 2025-04-16 16:56:03
 * @LastEditTime: 2025-04-16 20:18:32
 * @LastEditors: DSTBP
 */
// 获取系统参数
async function getSystemParameters() {
    const addr = localStorage.getItem('systemCenterAddress');
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
    const p1 = localStorage.getItem('systemParameters');
    if (p1) {
        document.getElementById('systemParameters').value = p1;
    }
    else {
        const params = await getSystemParameters();
        if (params) {
            const system_param = JSON.stringify(params, null, 2)
            localStorage.setItem('systemParameters', system_param)
            document.getElementById('systemParameters').value = system_param;
        }
    }
}



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

// 退出登录
function logout() {
    localStorage.removeItem('loginResponse');
    window.location.href = 'html/auth.html';
}

// 切换侧边栏显示状态
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查登录状态
    checkLoginStatus();
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
});

// 加载统计数据
function loadStatistics() {
    // 这里可以添加从服务器获取统计数据的逻辑
    // 目前使用模拟数据
    document.getElementById('totalFiles').textContent = '0';
    document.getElementById('totalStorage').textContent = '0 GB';
    document.getElementById('activeUsers').textContent = '0';
    document.getElementById('avgFileSize').textContent = '0 MB';
}
