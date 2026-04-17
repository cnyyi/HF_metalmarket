/* ========================================================
   宏发金属交易市场 - 后台管理全局JS
   2026-04-16 全面改版：侧边栏 + 暗色模式 + 微交互
   ======================================================== */

/**
 * 统一 Toast 通知函数
 * @param {string} type - 'success' | 'error' | 'warning' | 'info'
 * @param {string} message - 通知内容
 * @param {number} duration - 自动关闭时间（毫秒），默认 3000
 */
function showToast(type, message, duration) {
    duration = duration || 3000;
    var iconMap = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    var icon = iconMap[type] || iconMap['info'];

    var toastHtml = '<div class="toast-notification toast-' + type + '">' +
        '<i class="fa ' + icon + '"></i> ' +
        '<span>' + message + '</span>' +
        '<button class="toast-close" onclick="this.parentElement.remove()">&times;</button>' +
        '</div>';

    var container = document.getElementById('toastContainer');
    if (!container) return;
    container.insertAdjacentHTML('beforeend', toastHtml);

    var toastEl = container.lastElementChild;
    setTimeout(function() {
        toastEl.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(function() { toastEl.remove(); }, 300);
    }, duration);
}

/**
 * HTML 转义函数
 */
function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

/**
 * 数字格式化函数
 */
function formatNumber(num) {
    return parseFloat(num).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * CSRF Token 获取函数
 */
function getCSRFToken() {
    return $('meta[name="csrf-token"]').attr('content');
}

/**
 * 全局 Loading 控制
 */
var GlobalLoading = {
    show: function(text) {
        text = text || '加载中...';
        var overlay = document.getElementById('globalLoadingOverlay');
        var loadingText = document.getElementById('globalLoadingText');
        if (overlay) {
            if (loadingText) loadingText.textContent = text;
            overlay.classList.add('active');
        }
    },
    hide: function() {
        var overlay = document.getElementById('globalLoadingOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }
};

/**
 * 生成空状态 HTML
 * @param {string} title - 标题
 * @param {string} desc - 描述
 * @param {string} iconClass - 图标类名（如 'fa-inbox'）
 * @returns {string} HTML字符串
 */
function emptyStateHtml(title, desc, iconClass) {
    iconClass = iconClass || 'fa-inbox';
    return '<div class="empty-state">' +
        '<div class="empty-icon"><i class="fa ' + iconClass + '"></i></div>' +
        '<div class="empty-title">' + escapeHtml(title) + '</div>' +
        '<div class="empty-desc">' + escapeHtml(desc || '') + '</div>' +
        '</div>';
}

/**
 * 金额数字跳动动画
 * @param {HTMLElement} el - 目标元素
 * @param {number} target - 目标数值
 * @param {number} duration - 动画时长（毫秒）
 * @param {boolean} isMoney - 是否金额（显示¥符号和2位小数），默认true
 */
function animateValue(el, target, duration, isMoney) {
    duration = duration || 800;
    if (isMoney === undefined) isMoney = true;
    var start = 0;
    var startTime = null;

    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        var progress = Math.min((timestamp - startTime) / duration, 1);
        // ease-out cubic
        var eased = 1 - Math.pow(1 - progress, 3);
        var current = target * eased;
        if (isMoney) {
            el.textContent = '¥' + current.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        } else {
            el.textContent = Math.round(current).toLocaleString('en-US');
        }
        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
}

/**
 * Flash 消息自动转 Toast 通知
 */
(function() {
    var flashEl = document.getElementById('flashMessagesData');
    if (flashEl) {
        try {
            var flashMessages = JSON.parse(flashEl.textContent);
            var categoryMap = {
                'success': 'success',
                'danger': 'error',
                'warning': 'warning',
                'info': 'info',
                'primary': 'info',
                'secondary': 'info',
                'light': 'info',
                'dark': 'info'
            };
            if (flashMessages && flashMessages.length > 0) {
                setTimeout(function() {
                    flashMessages.forEach(function(item) {
                        var category = categoryMap[item[0]] || 'info';
                        showToast(category, item[1]);
                    });
                }, 100);
            }
        } catch (e) {
            // ignore parse errors
        }
    }
})();

/**
 * 主题切换（暗色/亮色）
 */
(function() {
    var toggleBtn = document.getElementById('themeToggle');
    var html = document.documentElement;

    // 初始化主题
    var saved = localStorage.getItem('hf-theme') ||
        (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    html.setAttribute('data-theme', saved);
    updateThemeIcon(saved);

    function updateThemeIcon(theme) {
        if (!toggleBtn) return;
        var icon = toggleBtn.querySelector('i');
        if (icon) {
            icon.className = theme === 'dark' ? 'fa fa-sun' : 'fa fa-moon';
        }
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            var current = html.getAttribute('data-theme');
            var next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('hf-theme', next);
            updateThemeIcon(next);
        });
    }

    // 监听系统主题变化
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (!localStorage.getItem('hf-theme')) {
                var theme = e.matches ? 'dark' : 'light';
                html.setAttribute('data-theme', theme);
                updateThemeIcon(theme);
            }
        });
    }
})();

/**
 * 侧边栏交互（移动端展开/收起）
 */
(function() {
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebarOverlay');
    var toggleBtn = document.getElementById('sidebarToggle');

    function openSidebar() {
        if (sidebar) sidebar.classList.add('show');
        if (overlay) overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('show');
        if (overlay) overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            if (sidebar && sidebar.classList.contains('show')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // 点击侧边栏链接后自动关闭（移动端）
    if (sidebar) {
        sidebar.addEventListener('click', function(e) {
            var link = e.target.closest('.sidebar-item');
            if (link && window.innerWidth < 992) {
                closeSidebar();
            }
        });
    }

    // 窗口大小变化时处理
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            closeSidebar();
        }
    });
})();

/**
 * 金额列自动添加 .col-amount 类
 * 在页面加载后扫描表格中的金额TD
 */
(function() {
    // 金额列特征：包含 ¥ 符号或数字格式
    function enhanceAmountCells() {
        document.querySelectorAll('.table td').forEach(function(td) {
            var text = td.textContent.trim();
            // 检测是否是金额（包含¥ 或 纯数字+逗号+小数）
            if (text.match(/^[\-¥]?[\d,]+\.?\d*$/) && text.length > 3) {
                td.classList.add('col-amount');
            }
        });
    }

    // 页面加载后执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', enhanceAmountCells);
    } else {
        enhanceAmountCells();
    }

    // AJAX 加载后也执行
    var origAjax = $.ajax;
    if (origAjax) {
        $(document).ajaxComplete(function() {
            setTimeout(enhanceAmountCells, 50);
        });
    }
})();


/**
 * 面包屑已迁移为圆角色块格式，直接由子页面 breadcrumb block 渲染
 * 无需 JS 解析旧格式
 */
