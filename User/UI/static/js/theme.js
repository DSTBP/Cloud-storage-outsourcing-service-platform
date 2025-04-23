// 主题切换功能
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('themeToggle');
    const icon = themeToggle.querySelector('i');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // 检查本地存储中的主题设置
    let currentTheme = sessionStorage.getItem('theme');
    if (!currentTheme) {
        currentTheme = prefersDarkScheme.matches ? 'dark' : 'light';
    }
    
    // 初始化主题
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);
    applyTheme(currentTheme);

    // 切换主题
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        sessionStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
        applyTheme(newTheme);
    });

    // 更新图标
    function updateThemeIcon(theme) {
        if (theme === 'dark') {
            icon.classList.remove('bi-sun-fill');
            icon.classList.add('bi-moon-fill');
        } else {
            icon.classList.remove('bi-moon-fill');
            icon.classList.add('bi-sun-fill');
        }
    }

    // 应用主题样式
    function applyTheme(theme) {
        const root = document.documentElement;
        
        if (theme === 'dark') {
            // 基础颜色
            root.style.setProperty('--primary-color', '#4a6cf7');
            root.style.setProperty('--secondary-color', '#a0a8b0');
            root.style.setProperty('--accent-color', '#4895ef');
            root.style.setProperty('--background-color', '#1a1f2e');
            root.style.setProperty('--text-primary', '#e4e6eb');
            root.style.setProperty('--text-secondary', '#b0b3b8');
            
            // 背景和文本
            root.style.setProperty('--bg-color', '#242837');
            root.style.setProperty('--bg-color-alt', '#1e2330');
            root.style.setProperty('--text-color', '#e4e6eb');
            root.style.setProperty('--text-color-secondary', '#b0b3b8');
            
            // 容器和卡片
            root.style.setProperty('--container-bg', 'rgba(40, 40, 40, 0.9)');
            root.style.setProperty('--card-bg', 'rgba(36, 40, 55, 0.95)');
            root.style.setProperty('--navbar-bg', 'rgba(0, 0, 0, 0.2)');
            
            // 输入框
            root.style.setProperty('--input-bg', 'rgba(60, 60, 60, 0.8)');
            root.style.setProperty('--input-border', 'rgba(100, 100, 100, 0.5)');
            root.style.setProperty('--input-text', '#ffffff');
            
            // 按钮
            root.style.setProperty('--btn-primary-bg', '#4a6baf');
            root.style.setProperty('--btn-primary-hover', '#3a5a9f');

            // 导航栏
            root.style.setProperty('--navbar-text', '#e4e6eb');
            root.style.setProperty('--navbar-brand-color', '#e4e6eb');
            root.style.setProperty('--navbar-link-color', '#e4e6eb');
            
        } else {
            // 基础颜色
            root.style.setProperty('--primary-color', '#4361ee');
            root.style.setProperty('--secondary-color', '#3f37c9');
            root.style.setProperty('--accent-color', '#4895ef');
            root.style.setProperty('--background-color', '#4361ee');
            root.style.setProperty('--text-primary', '#ffffff');
            root.style.setProperty('--text-secondary', 'rgba(255, 255, 255, 0.8)');
            
            // 背景和文本
            root.style.setProperty('--bg-color', '#f5f5f5');
            root.style.setProperty('--bg-color-alt', '#ffffff');
            root.style.setProperty('--text-color', '#333333');
            root.style.setProperty('--text-color-secondary', '#666666');
            
            // 容器和卡片
            root.style.setProperty('--container-bg', 'rgba(255, 255, 255, 0.9)');
            root.style.setProperty('--card-bg', 'rgba(255, 255, 255, 0.95)');
            root.style.setProperty('--navbar-bg', 'rgba(255, 255, 255, 0.1)');
            
            // 输入框
            root.style.setProperty('--input-bg', 'rgba(255, 255, 255, 0.8)');
            root.style.setProperty('--input-border', 'rgba(200, 200, 200, 0.5)');
            root.style.setProperty('--input-text', '#333333');
            
            // 按钮
            root.style.setProperty('--btn-primary-bg', '#0d6efd');
            root.style.setProperty('--btn-primary-hover', '#0b5ed7');

            // 导航栏
            root.style.setProperty('--navbar-text', '#1A237E');
            root.style.setProperty('--navbar-brand-color', '#1A237E');
            root.style.setProperty('--navbar-link-color', '#4EA9FF');
        }

        // 更新主页特定元素（如果存在）
        const heroWrapper = document.querySelector('.hero-wrapper');
        const statsSection = document.querySelector('.stats-section');
        const footer = document.querySelector('.footer');
        const navbar = document.querySelector('.navbar');

        if (heroWrapper) {
            heroWrapper.style.background = theme === 'dark'
                ? 'linear-gradient(135deg, var(--background-color) 0%, #2a3042 100%)'
                : 'linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%)';
        }

        if (statsSection) {
            statsSection.style.background = theme === 'dark'
                ? 'linear-gradient(135deg, var(--background-color) 0%, #2a3042 100%)'
                : 'linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%)';
        }

        if (footer) {
            footer.style.background = theme === 'dark' ? '#1a1f2e' : '#1a202c';
        }

        // 更新导航栏文本和图标颜色
        if (navbar) {
            // 更新品牌名称颜色
            const navBrand = navbar.querySelector('.navbar-brand');
            if (navBrand) {
                navBrand.style.color = theme === 'dark' ? '#e4e6eb' : '#1A237E';
            }

            // 更新导航链接颜色
            const navLinks = navbar.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.style.color = theme === 'dark' ? '#e4e6eb' : '#1A237E';
            });

            // 更新图标颜色
            const icons = navbar.querySelectorAll('.bi');
            icons.forEach(icon => {
                icon.style.color = theme === 'dark' ? '#e4e6eb' : '#4EA9FF';
            });
        }

        // 更新粒子颜色
        const particleColor = theme === 'dark' ? '#FFFFF0' : '#5463E3';
        if (window.pJSDom && window.pJSDom[0]) {
            const particlesJS = window.pJSDom[0].pJS;
            particlesJS.particles.color.value = particleColor;
            particlesJS.particles.line_linked.color = particleColor;
            particlesJS.particles.line_linked.color_rgb_line = hexToRgb(particleColor);
            
            // 重新初始化粒子
            particlesJS.fn.particlesEmpty();
            particlesJS.fn.particlesCreate();
            particlesJS.fn.particlesDraw();
        }
    }

    // 辅助函数：将十六进制颜色转换为RGB
    function hexToRgb(hex) {
        const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
        hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
});