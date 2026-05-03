class RiskEngine:
    def analyze(self, memory_data):
        risks = []
        for step_id, data in memory_data.items():
            if isinstance(data, dict) and data.get('error'):
                continue
            risks.extend(self._check_contract_risks(step_id, data))
            risks.extend(self._check_finance_risks(step_id, data))
            risks.extend(self._check_cost_risks(step_id, data))
        return risks

    def _check_contract_risks(self, step_id, data):
        risks = []
        if isinstance(data, dict):
            contracts_list = data.get('contracts')
            if isinstance(contracts_list, list) and len(contracts_list) > 0:
                expiring_count = len(contracts_list)
                if expiring_count >= 3:
                    risks.append({'level': 'high', 'type': 'contract',
                                  'message': f'{expiring_count}个合同即将到期，请关注续签'})
                else:
                    risks.append({'level': 'medium', 'type': 'contract',
                                  'message': f'{expiring_count}个合同即将到期'})
            contracts_info = data.get('contracts', {})
            if isinstance(contracts_info, dict) and contracts_info.get('active', 0) > 0:
                nearest = contracts_info.get('nearest_end_date')
                if nearest:
                    from datetime import datetime
                    try:
                        end_date = datetime.strptime(nearest, '%Y-%m-%d')
                        days_left = (end_date - datetime.now()).days
                        if days_left <= 30:
                            risks.append({'level': 'high', 'type': 'contract',
                                          'message': f'最近合同将于{nearest}到期（{days_left}天）'})
                        elif days_left <= 60:
                            risks.append({'level': 'medium', 'type': 'contract',
                                          'message': f'最近合同将于{nearest}到期（{days_left}天）'})
                    except ValueError:
                        pass
        return risks

    def _check_finance_risks(self, step_id, data):
        risks = []
        if isinstance(data, dict):
            overdue = data.get('overdue_receivable')
            if isinstance(overdue, dict):
                total = overdue.get('total_amount', 0)
                count = overdue.get('count', 0)
                if count > 0 and total > 0:
                    risks.append({'level': 'high', 'type': 'finance',
                                  'message': f'逾期应收 ¥{total:,.2f}（{count}笔）'})
            remaining_recv = data.get('total_remaining_receivable', 0)
            remaining_pay = data.get('total_remaining_payable', 0)
            if remaining_recv > 0 and remaining_pay > 0 and remaining_recv > remaining_pay * 3:
                risks.append({'level': 'medium', 'type': 'finance',
                              'message': f'应收余额远超应付余额（应收 ¥{remaining_recv:,.2f} vs 应付 ¥{remaining_pay:,.2f}）'})
        if isinstance(data, list) and self._looks_like_overdue(data):
            total = sum(item.get('remaining_amount', 0) for item in data)
            if total > 0:
                risks.append({'level': 'high', 'type': 'finance',
                              'message': f'逾期未收 ¥{total:,.2f}（{len(data)}笔）'})
        return risks

    def _check_cost_risks(self, step_id, data):
        risks = []
        if isinstance(data, list) and len(data) > 0 and self._is_name_value_list(data):
            values = [item.get('remaining_amount') or item.get('total_amount') or item.get('amount', 0) for item in data]
            total = sum(values)
            if total > 0:
                for item in data:
                    val = item.get('remaining_amount') or item.get('total_amount') or item.get('amount', 0)
                    if val / total > 0.7:
                        name = item.get('merchant_name') or item.get('vendor_name') or item.get('name', '某项')
                        risks.append({'level': 'medium', 'type': 'cost',
                                      'message': f'{name}占比超过70%，成本集中度较高'})
                        break
        return risks

    def _looks_like_contracts(self, data):
        if not data:
            return False
        first = data[0]
        return 'end_date' in first or 'contract_no' in first

    def _looks_like_overdue(self, data):
        if not data:
            return False
        first = data[0]
        return 'remaining_amount' in first and 'due_date' in first

    def _is_name_value_list(self, data):
        if not data:
            return False
        first = data[0]
        name_keys = {'merchant_name', 'vendor_name', 'name'}
        value_keys = {'remaining_amount', 'total_amount', 'amount'}
        return bool(name_keys & set(first.keys())) and bool(value_keys & set(first.keys()))
