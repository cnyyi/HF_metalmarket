var CustomerTransactionModal = (function() {
    var _modal = null;
    var _currentType = '';
    var _currentId = 0;
    var _currentName = '';
    var _currentFilter = '';
    var _currentPage = 1;

    var TAB_CONFIG = [
        { key: '', label: '全部', icon: 'fa-th-list' },
        { key: 'receivable', label: '应收', icon: 'fa-arrow-down' },
        { key: 'payable', label: '应付', icon: 'fa-arrow-up' },
        { key: 'prepayment', label: '预收/预付', icon: 'fa-exchange' },
        { key: 'deposit', label: '押金', icon: 'fa-shield' },
        { key: 'cashflow', label: '现金流水', icon: 'fa-money' }
    ];

    function _getTypeBadgeClass(type) {
        var map = {
            'receivable': 'bg-primary',
            'payable': 'bg-warning',
            'prepayment': 'bg-info',
            'deposit': 'bg-success',
            'cashflow': 'bg-secondary'
        };
        return map[type] || 'bg-secondary';
    }

    function _getStatusClass(status) {
        var map = {
            '未付款': 'status-unpaid',
            '部分付款': 'status-partial',
            '已付款': 'status-paid',
            '未核销': 'status-unpaid',
            '部分核销': 'status-partial',
            '已核销': 'status-paid',
            '收取中': 'status-unpaid',
            '部分退还': 'status-partial',
            '已结清': 'status-paid',
            '收入': 'status-paid',
            '支出': 'status-unpaid'
        };
        return map[status] || 'status-inactive';
    }

    function _buildModalHtml() {
        var html = '';
        html += '<div class="modal fade" id="customerTxModal" tabindex="-1" aria-hidden="true">';
        html += '<div class="modal-dialog modal-xl">';
        html += '<div class="modal-content">';
        html += '<div class="modal-header" style="background:linear-gradient(135deg,var(--color-primary,#3b82f6),var(--color-primary-dark,#1d4ed8));color:#fff;">';
        html += '<h5 class="modal-title"><i class="fa fa-history"></i> <span id="customerTxTitle">财务交易记录</span></h5>';
        html += '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>';
        html += '</div>';
        html += '<div class="modal-body">';

        html += '<div class="row mb-3" id="customerTxSummary">';
        html += '<div class="col"><div class="p-2 rounded text-center" style="background:var(--color-primary-light,#e8f0fe);"><div style="font-size:0.75rem;color:var(--color-text-muted);">应收余额</div><div class="fw-bold" style="font-size:1.1rem;color:var(--color-primary);" id="txSumReceivable">¥0</div></div></div>';
        html += '<div class="col"><div class="p-2 rounded text-center" style="background:var(--color-warning-light,#fff8e1);"><div style="font-size:0.75rem;color:var(--color-text-muted);">应付余额</div><div class="fw-bold" style="font-size:1.1rem;color:var(--color-warning);" id="txSumPayable">¥0</div></div></div>';
        html += '<div class="col"><div class="p-2 rounded text-center" style="background:var(--color-info-light,#e0f7fa);"><div style="font-size:0.75rem;color:var(--color-text-muted);">预收余额</div><div class="fw-bold" style="font-size:1.1rem;color:var(--color-info);" id="txSumPrepayment">¥0</div></div></div>';
        html += '<div class="col"><div class="p-2 rounded text-center" style="background:var(--color-success-light,#e8f5e9);"><div style="font-size:0.75rem;color:var(--color-text-muted);">押金余额</div><div class="fw-bold" style="font-size:1.1rem;color:var(--color-success);" id="txSumDeposit">¥0</div></div></div>';
        html += '<div class="col"><div class="p-2 rounded text-center" style="background:var(--color-danger-light,#fce4ec);"><div style="font-size:0.75rem;color:var(--color-text-muted);">净应收</div><div class="fw-bold" style="font-size:1.1rem;" id="txSumCashflow">¥0</div></div></div>';
        html += '</div>';

        html += '<ul class="nav nav-pills mb-3" id="customerTxTabs">';
        for (var i = 0; i < TAB_CONFIG.length; i++) {
            var tab = TAB_CONFIG[i];
            html += '<li class="nav-item">';
            html += '<a class="nav-link' + (i === 0 ? ' active' : '') + '" href="#" data-filter="' + tab.key + '"><i class="fa ' + tab.icon + '"></i> ' + tab.label + '</a>';
            html += '</li>';
        }
        html += '</ul>';

        html += '<div class="table-responsive">';
        html += '<table class="table table-sm table-striped table-hover">';
        html += '<thead><tr><th>类型</th><th>费用类型</th><th class="text-end">金额</th><th class="text-end">已核销</th><th class="text-end">余额</th><th>状态</th><th>日期</th><th>创建时间</th></tr></thead>';
        html += '<tbody id="customerTxBody">';
        html += '<tr><td colspan="8" class="text-center text-muted">加载中...</td></tr>';
        html += '</tbody>';
        html += '</table>';
        html += '</div>';

        html += '<div class="d-flex justify-content-center mt-2" id="customerTxPagination" style="display:none;">';
        html += '<ul class="pagination pagination-sm mb-0" id="customerTxPageList"></ul>';
        html += '</div>';

        html += '</div>';
        html += '<div class="modal-footer">';
        html += '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>';
        html += '</div>';
        html += '</div>';
        html += '</div>';
        html += '</div>';
        return html;
    }

    function _init() {
        if ($('#customerTxModal').length === 0) {
            $('body').append(_buildModalHtml());
        }

        $(document).on('click', '#customerTxTabs .nav-link', function(e) {
            e.preventDefault();
            $('#customerTxTabs .nav-link').removeClass('active');
            $(this).addClass('active');
            _currentFilter = $(this).data('filter');
            _currentPage = 1;
            _loadData();
        });

        $(document).on('click', '#customerTxPageList .page-link', function(e) {
            e.preventDefault();
            var page = $(this).data('page');
            if (page && page >= 1) {
                _currentPage = page;
                _loadData();
            }
        });
    }

    function _loadData() {
        var params = {
            customer_type: _currentType,
            customer_id: _currentId,
            page: _currentPage,
            per_page: 10
        };
        if (_currentFilter) {
            params.type = _currentFilter;
        }

        $.ajax({
            url: '/finance/customer/transactions',
            type: 'GET',
            data: params,
            success: function(resp) {
                if (resp.success) {
                    _renderData(resp.data);
                } else {
                    $('#customerTxBody').html('<tr><td colspan="8" class="text-center text-danger">' + escapeHtml(resp.message || '加载失败') + '</td></tr>');
                }
            },
            error: function() {
                $('#customerTxBody').html('<tr><td colspan="8" class="text-center text-danger">网络错误</td></tr>');
            }
        });
    }

    function _renderData(data) {
        var items = data.items;
        var tbody = $('#customerTxBody');

        if (data.summary) {
            var s = data.summary;
            $('#txSumReceivable').text('¥' + formatNumber(s.total_receivable));
            $('#txSumPayable').text('¥' + formatNumber(s.total_payable));
            $('#txSumPrepayment').text('¥' + formatNumber(s.total_prepayment));
            $('#txSumDeposit').text('¥' + formatNumber(s.total_deposit));

            var cfVal = s.total_cashflow;
            var cfEl = $('#txSumCashflow');
            cfEl.text('¥' + formatNumber(Math.abs(cfVal)));
            if (cfVal < 0) {
                cfEl.css('color', 'var(--color-danger)');
                cfEl.closest('.col').find('div[style]').first().find('div').first().text('净应付');
            } else {
                cfEl.css('color', 'var(--color-success)');
                cfEl.closest('.col').find('div[style]').first().find('div').first().text('净应收');
            }
        }

        if (!items || items.length === 0) {
            tbody.html('<tr><td colspan="8" class="text-center text-muted py-3"><i class="fa fa-inbox fa-2x mb-2 d-block"></i>暂无交易记录</td></tr>');
            $('#customerTxPagination').hide();
            return;
        }

        var html = '';
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            var badgeClass = _getTypeBadgeClass(item.type);
            var statusClass = _getStatusClass(item.status);

            html += '<tr>';
            html += '<td><span class="badge ' + badgeClass + '">' + escapeHtml(item.type_label) + '</span></td>';
            html += '<td>' + escapeHtml(item.expense_type_name || '-') + '</td>';
            html += '<td class="text-end">¥' + formatNumber(item.amount) + '</td>';
            html += '<td class="text-end">¥' + formatNumber(item.paid_amount) + '</td>';
            html += '<td class="text-end">¥' + formatNumber(item.remaining_amount) + '</td>';
            html += '<td><span class="status-badge ' + statusClass + '">' + escapeHtml(item.status) + '</span></td>';
            html += '<td>' + escapeHtml(item.transaction_date || '-') + '</td>';
            html += '<td>' + escapeHtml(item.create_time) + '</td>';
            html += '</tr>';
        }
        tbody.html(html);

        var totalPages = data.total_pages;
        var curPage = data.current_page;
        if (totalPages <= 1) {
            $('#customerTxPagination').hide();
        } else {
            var pageHtml = '';
            pageHtml += '<li class="page-item ' + (curPage === 1 ? 'disabled' : '') + '">';
            pageHtml += '<a class="page-link" href="#" data-page="' + (curPage - 1) + '">上一页</a></li>';

            var startP = Math.max(1, curPage - 2);
            var endP = Math.min(totalPages, curPage + 2);
            if (startP > 1) {
                pageHtml += '<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>';
                if (startP > 2) pageHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
            for (var p = startP; p <= endP; p++) {
                pageHtml += '<li class="page-item ' + (p === curPage ? 'active' : '') + '">';
                pageHtml += '<a class="page-link" href="#" data-page="' + p + '">' + p + '</a></li>';
            }
            if (endP < totalPages) {
                if (endP < totalPages - 1) pageHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
                pageHtml += '<li class="page-item"><a class="page-link" href="#" data-page="' + totalPages + '">' + totalPages + '</a></li>';
            }

            pageHtml += '<li class="page-item ' + (curPage === totalPages ? 'disabled' : '') + '">';
            pageHtml += '<a class="page-link" href="#" data-page="' + (curPage + 1) + '">下一页</a></li>';

            $('#customerTxPageList').html(pageHtml);
            $('#customerTxPagination').show();
        }
    }

    function show(customerType, customerId, customerName) {
        _currentType = customerType;
        _currentId = customerId;
        _currentName = customerName || '';
        _currentFilter = '';
        _currentPage = 1;

        $('#customerTxTitle').text(_currentName + ' - 财务交易记录');
        $('#customerTxTabs .nav-link').removeClass('active');
        $('#customerTxTabs .nav-link').first().addClass('active');
        $('#customerTxBody').html('<tr><td colspan="8" class="text-center text-muted"><i class="fa fa-spinner fa-spin"></i> 加载中...</td></tr>');
        $('#customerTxPagination').hide();

        if (!_modal) {
            _modal = new bootstrap.Modal(document.getElementById('customerTxModal'));
        }
        _modal.show();
        _loadData();
    }

    return {
        init: _init,
        show: show
    };
})();
