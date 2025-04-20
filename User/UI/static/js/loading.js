// 创建加载动画元素
function createLoader() {
    const loader = document.createElement('div');
    loader.className = 'page-loader';
    loader.innerHTML = `
        <div class="loader-content">
            <div class="loader-spinner"></div>
            <div class="loader-text">正在加载...</div>
        </div>
    `;
    document.body.appendChild(loader);
    return loader;
}

// 显示加载动画
function showLoader() {
    const loader = document.querySelector('.page-loader') || createLoader();
    loader.classList.remove('fade-out');
}

// 隐藏加载动画
function hideLoader() {
    const loader = document.querySelector('.page-loader');
    if (loader) {
        loader.classList.add('fade-out');
        setTimeout(() => {
            loader.remove();
        }, 500);
    }
}

// 页面加载完成后隐藏加载动画
document.addEventListener('DOMContentLoaded', () => {
    // 等待所有资源加载完成
    window.addEventListener('load', () => {
        // 给一个小延迟，确保页面渲染完成
        setTimeout(hideLoader, 500);
    });
});

// 导出加载器控制函数
window.pageLoader = {
    show: showLoader,
    hide: hideLoader
}; 