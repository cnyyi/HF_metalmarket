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
 * 侧边栏分组折叠
 */
(function() {
    var STORAGE_KEY = 'sidebar_collapsed_sections';

    function getCollapsed() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        } catch(e) {
            return [];
        }
    }

    function saveCollapsed(arr) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
        } catch(e) {}
    }

    function initSections() {
        var sections = document.querySelectorAll('.sidebar-section[data-section]');
        var collapsed = getCollapsed();

        sections.forEach(function(section) {
            var key = section.getAttribute('data-section');
            var title = section.querySelector('.sidebar-section-title');
            var hasActive = section.querySelector('.sidebar-item.active');

            if (hasActive) {
                section.classList.remove('collapsed');
                var idx = collapsed.indexOf(key);
                if (idx > -1) {
                    collapsed.splice(idx, 1);
                    saveCollapsed(collapsed);
                }
            } else if (collapsed.indexOf(key) > -1) {
                section.classList.add('collapsed');
            }

            if (title) {
                title.addEventListener('click', function(e) {
                    e.preventDefault();
                    section.classList.toggle('collapsed');
                    var isCollapsed = section.classList.contains('collapsed');
                    var current = getCollapsed();
                    if (isCollapsed) {
                        if (current.indexOf(key) === -1) {
                            current.push(key);
                        }
                    } else {
                        var idx = current.indexOf(key);
                        if (idx > -1) {
                            current.splice(idx, 1);
                        }
                    }
                    saveCollapsed(current);
                });
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSections);
    } else {
        initSections();
    }
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

/**
 * 统一分页 HTML 生成器
 * @param {string} container - 分页容器选择器（如 '#pagination'）
 * @param {object} data - { current_page, total_pages, total }
 * @param {function} onPageClick - function(pageNumber) 点击页码回调
 */
function renderPagination(container, data, onPageClick) {
    var el = $(container);
    if (!el.length) return;
    el.empty();

    var totalPages = data.total_pages;
    var curPage = data.current_page;

    if (totalPages <= 1) {
        var area = el.closest('#paginationArea');
        if (area.length) area.hide();
        return;
    }
    var area = el.closest('#paginationArea');
    if (area.length) area.show();

    var html = '';
    html += '<li class="page-item ' + (curPage === 1 ? 'disabled' : '') + '">';
    html += '<a class="page-link" href="#" data-page="' + (curPage - 1) + '">上一页</a></li>';

    var startPage = Math.max(1, curPage - 2);
    var endPage = Math.min(totalPages, curPage + 2);

    if (startPage > 1) {
        html += '<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>';
        if (startPage > 2) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }

    for (var i = startPage; i <= endPage; i++) {
        html += '<li class="page-item ' + (i === curPage ? 'active' : '') + '">';
        html += '<a class="page-link" href="#" data-page="' + i + '">' + i + '</a></li>';
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
        html += '<li class="page-item"><a class="page-link" href="#" data-page="' + totalPages + '">' + totalPages + '</a></li>';
    }

    html += '<li class="page-item ' + (curPage === totalPages ? 'disabled' : '') + '">';
    html += '<a class="page-link" href="#" data-page="' + (curPage + 1) + '">下一页</a></li>';

    el.html(html);

    el.off('click', '.page-link').on('click', '.page-link', function(e) {
        e.preventDefault();
        var page = $(this).data('page');
        if (page && !$(this).closest('.page-item').hasClass('disabled')) {
            if (typeof onPageClick === 'function') onPageClick(page);
        }
    });
}

/**
 * 统一搜索绑定（按钮点击 + 回车触发）
 * @param {string} inputId - 搜索输入框 ID
 * @param {string} btnId - 搜索按钮 ID
 * @param {function} callback - function() 搜索时调用
 */
function bindSearch(inputId, btnId, callback) {
    var input = $('#' + inputId);
    var btn = $('#' + btnId);

    btn.off('click').on('click', function() {
        if (typeof callback === 'function') callback();
    });

    input.off('keypress.search').on('keypress.search', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            if (typeof callback === 'function') callback();
        }
    });
}

/**
 * 统一删除确认流程
 * @param {object} options
 * @param {string} options.url - 删除接口 URL
 * @param {string|number} options.id - 要删除的记录 ID
 * @param {string} [options.modalId='deleteModal'] - 确认模态框 ID
 * @param {function} [options.onSuccess] - 删除成功回调
 * @param {string} [options.message='删除成功'] - 成功提示消息
 */
function confirmDelete(options) {
    var modalId = options.modalId || 'deleteModal';
    var deleteId = options.id;
    var deleteUrl = options.url;
    var successMsg = options.message || '删除成功';

    $('#' + modalId).modal('show');
    $('#' + modalId + 'Confirm').off('click').on('click', function() {
        ajaxPost(deleteUrl, { id: deleteId }, function(resp) {
            $('#' + modalId).modal('hide');
            showToast('success', successMsg);
            if (typeof options.onSuccess === 'function') options.onSuccess(resp);
        });
    });
}

/**
 * AJAX POST 封装（自动携带 CSRF Token）
 * @param {string} url - 请求 URL
 * @param {object} data - 请求数据
 * @param {function} onSuccess - function(resp) 成功回调
 * @param {function} [onError] - function(xhr) 失败回调
 */
function ajaxPost(url, data, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'POST',
        data: data,
        headers: { 'X-CSRFToken': getCSRFToken() },
        success: function(resp) {
            if (typeof onSuccess === 'function') onSuccess(resp);
        },
        error: function(xhr) {
            if (typeof onError === 'function') {
                onError(xhr);
            } else {
                var msg = '操作失败';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    msg = xhr.responseJSON.message;
                }
                showToast('error', msg);
            }
        }
    });
}

/**
 * AJAX GET 封装
 * @param {string} url - 请求 URL
 * @param {object} params - 查询参数
 * @param {function} onSuccess - function(resp) 成功回调
 * @param {function} [onError] - function(xhr) 失败回调
 */
function ajaxGet(url, params, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'GET',
        data: params,
        success: function(resp) {
            if (typeof onSuccess === 'function') onSuccess(resp);
        },
        error: function(xhr) {
            if (typeof onError === 'function') {
                onError(xhr);
            } else {
                showToast('error', '请求失败，请刷新页面重试');
            }
        }
    });
}

/**
 * 统一状态徽章 HTML 生成
 * @param {string} status - 状态文本
 * @returns {string} HTML 字符串
 */
function statusBadge(status) {
    var statusMap = {
        '未付款': 'status-unpaid',
        '未缴费': 'status-unpaid',
        '部分付款': 'status-partial',
        '部分缴费': 'status-partial',
        '已付款': 'status-paid',
        '已缴费': 'status-paid',
        '逾期': 'status-overdue',
        '有效': 'status-active',
        '正常': 'status-active',
        '活跃': 'status-active',
        '无效': 'status-inactive',
        '停用': 'status-inactive'
    };
    var cls = statusMap[status] || 'status-inactive';
    return '<span class="status-badge ' + cls + '">' + escapeHtml(status) + '</span>';
}

/**
 * 表格加载中占位 HTML
 * @param {number} colspan - 列数
 * @returns {string} HTML 字符串
 */
function tableLoadingHtml(colspan) {
    return '<tr><td colspan="' + colspan + '" class="text-center py-4"><i class="fa fa-spinner fa-spin fa-2x text-muted"></i><p class="mt-2 text-muted">加载中...</p></td></tr>';
}

/**
 * 表格空数据占位 HTML
 * @param {number} colspan - 列数
 * @param {string} [message='暂无数据'] - 提示消息
 * @returns {string} HTML 字符串
 */
function tableEmptyHtml(colspan, message) {
    message = message || '暂无数据';
    return '<tr><td colspan="' + colspan + '" class="text-center py-4 text-muted"><i class="fa fa-inbox fa-2x mb-2"></i><p>' + escapeHtml(message) + '</p></td></tr>';
}

/**
 * 表格错误占位 HTML
 * @param {number} colspan - 列数
 * @param {string} [message='加载失败'] - 提示消息
 * @returns {string} HTML 字符串
 */
function tableErrorHtml(colspan, message) {
    message = message || '加载失败';
    return '<tr><td colspan="' + colspan + '" class="text-center py-4 text-danger"><i class="fa fa-exclamation-circle fa-2x mb-2"></i><p>' + escapeHtml(message) + '</p></td></tr>';
}
