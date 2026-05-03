class ChartBuilder:
    def build(self, memory_data):
        charts = []
        for step_id, data in memory_data.items():
            if isinstance(data, dict) and data.get('error'):
                continue
            chart = self._try_build(data)
            if chart:
                charts.append(chart)
        return charts[0] if len(charts) == 1 else (charts if charts else None)

    def _try_build(self, data):
        if isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict):
                if self._is_time_series(first):
                    return self._build_line(data)
                if self._is_category_count(first):
                    return self._build_bar(data)
                if self._is_name_value(first):
                    return self._build_pie(data)
        if isinstance(data, dict):
            if self._is_fee_breakdown_dict(data):
                return self._build_pie_from_dict(data)
        return None

    def _is_time_series(self, item):
        return 'month' in item and ('income' in item or 'expense' in item)

    def _is_category_count(self, item):
        return 'status' in item and 'count' in item

    def _is_name_value(self, item):
        name_keys = {'merchant_name', 'vendor_name', 'plot_type', 'business_type', 'name'}
        value_keys = {'total_amount', 'remaining_amount', 'amount', 'fee_amount', 'value', 'total_area'}
        has_name = bool(name_keys & set(item.keys()))
        has_value = bool(value_keys & set(item.keys()))
        return has_name and has_value

    def _is_fee_breakdown_dict(self, data):
        value_keys = {'total_income', 'total_expense', 'total_receivable', 'total_payable',
                      'balance', 'total_remaining_receivable', 'total_remaining_payable'}
        return bool(value_keys & set(data.keys()))

    def _build_line(self, data):
        months = [item.get('month', '') for item in data]
        series = []
        if 'income' in data[0]:
            series.append({'name': '收入', 'data': [item.get('income', 0) for item in data]})
        if 'expense' in data[0]:
            series.append({'name': '支出', 'data': [item.get('expense', 0) for item in data]})
        return {'type': 'line', 'title': '收支趋势', 'xAxis': months, 'series': series}

    def _build_bar(self, data):
        names = [item.get('status', item.get('plot_type', '')) for item in data]
        values = [item.get('count', item.get('total_amount', 0)) for item in data]
        return {'type': 'bar', 'title': '分类统计', 'xAxis': names, 'series': [{'name': '数量', 'data': values}]}

    def _build_pie(self, data):
        pie_data = []
        for item in data:
            name = (item.get('merchant_name') or item.get('vendor_name') or
                    item.get('plot_type') or item.get('business_type') or item.get('name', ''))
            value = (item.get('remaining_amount') or item.get('total_amount') or
                     item.get('amount') or item.get('fee_amount') or item.get('value') or
                     item.get('total_area', 0))
            if name and value:
                pie_data.append({'name': name, 'value': value})
        if not pie_data:
            return None
        return {'type': 'pie', 'title': '数据分布', 'data': pie_data}

    def _build_pie_from_dict(self, data):
        pie_data = []
        label_map = {
            'total_receivable': '应收总额', 'total_paid_receivable': '已收金额',
            'total_remaining_receivable': '未收金额', 'total_payable': '应付总额',
            'total_paid_payable': '已付金额', 'total_remaining_payable': '未付金额',
            'total_income': '总收入', 'total_expense': '总支出', 'balance': '结余',
        }
        for key, label in label_map.items():
            val = data.get(key)
            if val and isinstance(val, (int, float)) and val > 0:
                pie_data.append({'name': label, 'value': val})
        if not pie_data:
            return None
        return {'type': 'pie', 'title': '财务概况', 'data': pie_data}
