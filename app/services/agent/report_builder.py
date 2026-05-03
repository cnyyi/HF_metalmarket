class ReportBuilder:
    def build(self, memory_data, risks):
        sections = []
        summary = self._build_summary(memory_data)
        if summary:
            sections.append(summary)
        details = self._build_details(memory_data)
        if details:
            sections.append(details)
        risk_section = self._build_risks(risks)
        if risk_section:
            sections.append(risk_section)
        suggestions = self._build_suggestions(risks)
        if suggestions:
            sections.append(suggestions)
        return '\n\n'.join(sections)

    def _build_summary(self, memory_data):
        lines = ['【总体情况】']
        has_data = False
        for step_id, data in memory_data.items():
            if isinstance(data, dict) and not data.get('error'):
                if 'total_receivable' in data:
                    lines.append(f"应收总额 ¥{data.get('total_receivable', 0):,.2f}，"
                                 f"已收 ¥{data.get('total_paid_receivable', 0):,.2f}，"
                                 f"未收 ¥{data.get('total_remaining_receivable', 0):,.2f}")
                    has_data = True
                if 'total_payable' in data:
                    lines.append(f"应付总额 ¥{data.get('total_payable', 0):,.2f}，"
                                 f"已付 ¥{data.get('total_paid_payable', 0):,.2f}，"
                                 f"未付 ¥{data.get('total_remaining_payable', 0):,.2f}")
                    has_data = True
                if 'total_income' in data:
                    lines.append(f"收入 ¥{data.get('total_income', 0):,.2f}，"
                                 f"支出 ¥{data.get('total_expense', 0):,.2f}，"
                                 f"结余 ¥{data.get('balance', 0):,.2f}")
                    has_data = True
                if 'merchant' in data:
                    m = data['merchant']
                    name = m.get('MerchantName') or m.get('merchant_name', '')
                    lines.append(f"商户：{name}")
                    has_data = True
                if 'query_mode' in data and 'contracts' in data:
                    lines.append(f"合同到期查询（{data['query_mode']}）：共 {data['total_count']} 份")
                    has_data = True
        return '\n'.join(lines) if has_data else ''

    def _build_details(self, memory_data):
        lines = ['【费用结构】']
        has_data = False
        for step_id, data in memory_data.items():
            if isinstance(data, dict) and 'contracts' in data and isinstance(data['contracts'], list):
                data = data['contracts']
            if isinstance(data, list) and len(data) > 0:
                first = data[0]
                if isinstance(first, dict):
                    name = first.get('merchant_name') or first.get('vendor_name') or first.get('name')
                    amount = first.get('remaining_amount') or first.get('total_amount') or first.get('amount')
                    if name and amount is not None:
                        for item in data[:10]:
                            n = item.get('merchant_name') or item.get('vendor_name') or item.get('name', '')
                            a = item.get('remaining_amount') or item.get('total_amount') or item.get('amount', 0)
                            lines.append(f"- {n}：¥{a:,.2f}")
                        if len(data) > 10:
                            lines.append(f"- ...共{len(data)}条")
                        has_data = True
        return '\n'.join(lines) if has_data else ''

    def _build_risks(self, risks):
        if not risks:
            return ''
        lines = ['【风险提示】']
        for r in risks:
            icon = '🔴' if r['level'] == 'high' else '🟡'
            lines.append(f"{icon} {r['message']}")
        return '\n'.join(lines)

    def _build_suggestions(self, risks):
        if not risks:
            return ''
        lines = ['【建议措施】']
        suggestions = set()
        for r in risks:
            if r['type'] == 'contract':
                suggestions.add('关注即将到期合同的续签情况')
            elif r['type'] == 'finance':
                suggestions.add('跟进逾期应收账款的催收')
            elif r['type'] == 'cost':
                suggestions.add('优化成本结构，降低集中度风险')
        for s in suggestions:
            lines.append(f"- {s}")
        return '\n'.join(lines)
