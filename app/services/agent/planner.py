import json
import logging
from openai import OpenAI
from flask import current_app
from app.services.agent.prompts import build_planner_prompt

logger = logging.getLogger(__name__)

RULE_MAP = {
    '应付': [{'id': 'step1', 'tool': 'query_payable_summary', 'args': {}}],
    '合同到期': [{'id': 'step1', 'tool': 'query_expiring_contracts', 'args': {'days': 30}}],
    '商户概况': [{'id': 'step1', 'tool': 'query_merchant_overview', 'args': {}}],
    '应收': [{'id': 'step1', 'tool': 'query_receivable_summary', 'args': {}}],
    '逾期': [{'id': 'step1', 'tool': 'query_overdue_receivables', 'args': {}}],
    '水电': [{'id': 'step1', 'tool': 'query_electricity_stats', 'args': {}}, {'id': 'step2', 'tool': 'query_water_stats', 'args': {}}],
    '趋势': [{'id': 'step1', 'tool': 'query_monthly_trend', 'args': {}}],
    '财务汇总': [{'id': 'step1', 'tool': 'query_finance_summary', 'args': {}}],
    '地块': [{'id': 'step1', 'tool': 'query_plots', 'args': {}}],
    '合同': [{'id': 'step1', 'tool': 'query_contracts', 'args': {}}],
    '押金': [{'id': 'step1', 'tool': 'query_deposit_summary', 'args': {}}],
    '预付': [{'id': 'step1', 'tool': 'query_prepayment_summary', 'args': {}}],
    '工资': [{'id': 'step1', 'tool': 'query_salary_stats', 'args': {'year_month': ''}}],
    '垃圾': [{'id': 'step1', 'tool': 'query_garbage_fees', 'args': {}}],
    '宿舍': [{'id': 'step1', 'tool': 'query_dorm_rooms', 'args': {}}],
    '磅秤': [{'id': 'step1', 'tool': 'query_scale_stats', 'args': {}}],
    '费用': [{'id': 'step1', 'tool': 'query_expense_item_summary', 'args': {}}],
}


class Planner:
    def __init__(self, get_client_fn, registry):
        self._get_client = get_client_fn
        self.registry = registry
        self._direct_response = None

    def plan(self, history, message, source, merchant_id, merchant_name, injected_kwargs):
        system_prompt = build_planner_prompt(source, merchant_id, merchant_name)
        tools = self.registry.get_all_schemas()

        messages = [{'role': 'system', 'content': system_prompt}]
        for msg in history:
            messages.append({'role': msg['role'], 'content': msg['content']})

        try:
            response = self._call_llm(messages, tools)
        except Exception as e:
            logger.error(f'Planner LLM call failed: {e}', exc_info=True)
            return self._rule_based_plan(message), []

        if response is None:
            return self._rule_based_plan(message), []

        finish_reason = response.get('finish_reason')
        content = response.get('content') or ''
        tool_calls = response.get('tool_calls')

        if finish_reason != 'tool_calls' or not tool_calls:
            self._direct_response = content
            return [], []

        plan = []
        tool_call_detail = []
        for i, tc in enumerate(tool_calls):
            fn_name = tc['function']['name']
            try:
                fn_args = json.loads(tc['function']['arguments'])
            except json.JSONDecodeError:
                fn_args = {}
            plan.append({
                'id': f'step{i + 1}',
                'tool': fn_name,
                'args': fn_args
            })
            tool_call_detail.append({
                'id': tc['id'],
                'name': fn_name,
                'arguments': fn_args
            })

        return plan, tool_call_detail

    def get_direct_response(self):
        return self._direct_response

    def _rule_based_plan(self, message):
        for keyword, plan in RULE_MAP.items():
            if keyword in message:
                return plan
        return []

    def _call_llm(self, messages, tools):
        api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-v4-pro')

        if not api_key:
            return {'content': 'AI 助手未配置，请联系管理员设置 DEEPSEEK_API_KEY。', 'finish_reason': 'stop', 'tool_calls': None}

        client = self._get_client()

        tools_param = []
        for t in tools:
            tools_param.append({'type': 'function', 'function': t['function']})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=4096,
            tools=tools_param if tools_param else None,
            tool_choice='auto' if tools_param else None
        )

        choice = response.choices[0]
        msg = choice.message

        tc_list = None
        if msg.tool_calls:
            tc_list = []
            for tc in msg.tool_calls:
                tc_list.append({
                    'id': tc.id,
                    'type': 'function',
                    'function': {
                        'name': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                })

        return {
            'content': msg.content,
            'finish_reason': choice.finish_reason,
            'tool_calls': tc_list
        }
