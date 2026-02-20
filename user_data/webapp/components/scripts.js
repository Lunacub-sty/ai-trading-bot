// 主题切换功能
function initThemeSwitcher() {
    const themeButtons = document.querySelectorAll('.theme-btn');
    const body = document.body;
    
    // 加载保存的主题或默认使用dark主题
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    
    themeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const theme = this.getAttribute('data-theme');
            setTheme(theme);
            localStorage.setItem('theme', theme);
        });
    });
    
    function setTheme(theme) {
        // 移除所有主题类
        body.classList.remove('light', 'dark', 'warm');
        // 添加新主题类
        body.classList.add(theme);
        
        // 更新主题按钮状态
        themeButtons.forEach(button => {
            button.classList.remove('active');
            if (button.getAttribute('data-theme') === theme) {
                button.classList.add('active');
            }
        });
        
        // 更新图表颜色
        updateChartColors(theme);
    }
}

// 更新图表颜色以匹配当前主题
function updateChartColors(theme) {
    if (window.priceChart) {
        if (theme === 'dark') {
            window.priceChart.options.scales.x.ticks.color = '#e1e1e1';
            window.priceChart.options.scales.y.ticks.color = '#e1e1e1';
            window.priceChart.options.plugins.legend.labels.color = '#e1e1e1';
        } else {
            window.priceChart.options.scales.x.ticks.color = '#333';
            window.priceChart.options.scales.y.ticks.color = '#333';
            window.priceChart.options.plugins.legend.labels.color = '#333';
        }
        window.priceChart.update();
    }
    
    if (window.equityChart) {
        if (theme === 'dark') {
            window.equityChart.options.scales.x.ticks.color = '#e1e1e1';
            window.equityChart.options.scales.y.ticks.color = '#e1e1e1';
            window.equityChart.options.plugins.legend.labels.color = '#e1e1e1';
        } else {
            window.equityChart.options.scales.x.ticks.color = '#333';
            window.equityChart.options.scales.y.ticks.color = '#333';
            window.equityChart.options.plugins.legend.labels.color = '#333';
        }
        window.equityChart.update();
    }
}

// 加载组件
function loadComponent(componentName, containerId) {
    fetch(`/components/${componentName}.html`)
        .then(response => response.text())
        .then(html => {
            document.getElementById(containerId).innerHTML = html;
            
            // 如果是主题切换器组件，初始化它
            if (componentName === 'theme-switcher') {
                initThemeSwitcher();
            }
        });
}

// 初始化所有组件
function initComponents() {
    // 加载导航栏
    loadComponent('header', 'header-container');
    
    // 加载页脚
    loadComponent('footer', 'footer-container');
    
    // 加载主题切换器
    loadComponent('theme-switcher', 'theme-switcher-container');
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initComponents);
} else {
    initComponents();
}