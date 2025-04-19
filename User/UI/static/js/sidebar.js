// 侧边栏导航功能
document.addEventListener('DOMContentLoaded', function() {
    // 获取所有侧边栏项目
    const sidebarItems = document.querySelectorAll('.sidebar-item');
    
    // 为每个侧边栏项目添加点击事件
    sidebarItems.forEach(item => {
        item.addEventListener('click', function() {
            const text = this.querySelector('span').textContent.trim();
            
            // 根据文本内容跳转到相应页面
            switch(text) {
                case '控制面板':
                    window.location.href = 'board.html';
                    break;
                case '上传文件':
                    window.location.href = 'upload.html';
                    break;
                case '下载文件':
                    window.location.href = 'download.html';
                    break;
                case '数据分析':
                    window.location.href = 'data.html';
                    break;
                case '系统设置':
                    window.location.href = 'settings.html';
                    break;
            }
        });

        // 添加鼠标悬停效果
        item.style.cursor = 'pointer';
    });

    // 根据当前页面URL设置活动项
    const currentPage = window.location.pathname.split('/').pop();
    sidebarItems.forEach(item => {
        const text = item.querySelector('span').textContent.trim();
        switch(currentPage) {
            case 'board.html':
                if(text === '控制面板') item.classList.add('active');
                break;
            case 'upload.html':
                if(text === '上传文件') item.classList.add('active');
                break;
            case 'download.html':
                if(text === '下载文件') item.classList.add('active');
                break;
            case 'data.html':
                if(text === '数据分析') item.classList.add('active');
                break;
            case 'settings.html':
                if(text === '系统设置') item.classList.add('active');
                break;
        }
    });
}); 