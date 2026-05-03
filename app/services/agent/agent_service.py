import json
import logging
from datetime import datetime
from openai import OpenAI
from flask import current_app
from utils.database import DBConnection
from app.services.agent.planner import Planner
from app.services.agent.executor import Executor
from app.services.agent.memory import Memory
from app.services.agent.tools import get_registry
from app.services.agent.chart_builder import ChartBuilder
from app.services.agent.risk_engine import RiskEngine
from app.services.agent.report_builder import ReportBuilder
from app.services.agent.prompts import build_planner_prompt, build_explainer_prompt

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self):
        self._client = None
        self._client_config = None

    def chat(self, user_id, conversation_id, message, source='admin', merchant_id=None, merchant_name=None):
        if not conversation_id:
            conversation_id = self._create_conversation(user_id, message, source)

        self._save_message(conversation_id, 'user', message)

        history = self._load_history(conversation_id)

        registry = get_registry()
        memory = Memory()
        planner = Planner(self._get_client, registry)
        executor = Executor(registry, memory)
        chart_builder = ChartBuilder()
        risk_engine = RiskEngine()
        report_builder = ReportBuilder()

        injected_kwargs = {'_merchant_id': merchant_id, '_source': source}

        plan, tool_call_detail = planner.plan(
            history, message, source, merchant_id, merchant_name, injected_kwargs
        )

        if plan:
            memory_data = executor.execute_plan(plan, injected_kwargs)
        else:
            memory_data = {}

        charts = chart_builder.build(memory_data)
        risks = risk_engine.analyze(memory_data)
        report = report_builder.build(memory_data, risks)

        if plan and memory_data:
            final_content = self._explain(
                history, message, plan, memory_data, report, source, merchant_id, merchant_name
            )
        else:
            final_content = planner.get_direct_response() or '暂无法回答该问题，请换个方式提问。'

        self._save_message(conversation_id, 'assistant', final_content,
                           generated_sql=json.dumps(tool_call_detail, ensure_ascii=False) if tool_call_detail else None)

        return {
            'conversation_id': conversation_id,
            'content': final_content,
            'chart': charts,
            'risks': risks,
            'steps': [{'id': s['id'], 'tool': s['tool'], 'args': s['args']} for s in plan] if plan else [],
            'tool_calls': tool_call_detail,
            'generated_sql': None,
            'query_result': None
        }

    def _explain(self, history, message, plan, memory_data, report, source, merchant_id, merchant_name):
        explainer_prompt = build_explainer_prompt(source, merchant_id, merchant_name)

        tool_results_summary = []
        for step_id, data in memory_data.items():
            result_str = json.dumps(data, ensure_ascii=False, default=str)
            tool_results_summary.append(f"[{step_id}] {result_str[:3000]}")

        messages = [
            {'role': 'system', 'content': explainer_prompt},
            {'role': 'user', 'content': message},
            {'role': 'assistant', 'content': f'查询结果：\n' + '\n'.join(tool_results_summary)}
        ]

        if report:
            messages.append({'role': 'user', 'content': '请基于以上查询结果，用自然语言回答用户的问题。参考以下报告结构：\n' + report})

        response = self._call_llm_simple(messages)
        if response:
            return response
        return report or '查询完成，但生成回答失败。'

    def get_conversations(self, user_id, source='admin'):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ConversationID, Title, Source, CreateTime, UpdateTime
                FROM AgentConversation
                WHERE UserID = ? AND Source = ?
                ORDER BY UpdateTime DESC
            """, (user_id, source))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'conversation_id': row.ConversationID,
                    'title': row.Title,
                    'source': row.Source,
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else '',
                    'update_time': row.UpdateTime.strftime('%Y-%m-%d %H:%M') if row.UpdateTime else ''
                })
            return result

    def get_history(self, conversation_id, user_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ConversationID FROM AgentConversation
                WHERE ConversationID = ? AND UserID = ?
            """, (conversation_id, user_id))
            if not cursor.fetchone():
                return []

            cursor.execute("""
                SELECT MessageID, Role, Content, GeneratedSQL, QueryResult, CreateTime
                FROM AgentMessage
                WHERE ConversationID = ?
                ORDER BY CreateTime ASC
            """, (conversation_id,))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                item = {
                    'message_id': row.MessageID,
                    'role': row.Role,
                    'content': row.Content,
                    'generated_sql': row.GeneratedSQL,
                    'query_result': row.QueryResult,
                    'create_time': row.CreateTime.strftime('%Y-%m-%d %H:%M') if row.CreateTime else ''
                }
                result.append(item)
            return result

    def create_conversation(self, user_id, source='admin'):
        return self._create_conversation(user_id, '新对话', source)

    def delete_conversation(self, conversation_id, user_id):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ConversationID FROM AgentConversation
                WHERE ConversationID = ? AND UserID = ?
            """, (conversation_id, user_id))
            if not cursor.fetchone():
                return False

            cursor.execute("DELETE FROM AgentMessage WHERE ConversationID = ?", (conversation_id,))
            cursor.execute("DELETE FROM AgentConversation WHERE ConversationID = ?", (conversation_id,))
            conn.commit()
            return True

    def _create_conversation(self, user_id, title, source):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO AgentConversation (UserID, Title, Source)
                OUTPUT INSERTED.ConversationID
                VALUES (?, ?, ?)
            """, (user_id, title[:200] if title else '新对话', source))
            conversation_id = cursor.fetchone()[0]
            conn.commit()
            return conversation_id

    def _save_message(self, conversation_id, role, content, generated_sql=None, query_result=None):
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO AgentMessage (ConversationID, Role, Content, GeneratedSQL, QueryResult)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, role, content, generated_sql, query_result))
            cursor.execute("""
                UPDATE AgentConversation SET UpdateTime = GETDATE(),
                    Title = ISNULL(NULLIF(Title, N'新对话'), ?)
                WHERE ConversationID = ? AND Title = N'新对话'
            """, (content[:200] if role == 'user' else None, conversation_id))
            conn.commit()

    def _load_history(self, conversation_id):
        max_rounds = current_app.config.get('AGENT_MAX_HISTORY_ROUNDS', 10)
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP (?) Role, Content
                FROM AgentMessage
                WHERE ConversationID = ?
                ORDER BY CreateTime DESC
            """, (max_rounds * 2, conversation_id))
            rows = cursor.fetchall()
            return [{'role': row.Role, 'content': row.Content} for row in reversed(rows)]

    def _get_client(self):
        api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

        current_config = (api_key, base_url)
        if self._client is not None and self._client_config == current_config:
            return self._client

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._client_config = current_config
        return self._client

    def _call_llm_simple(self, messages):
        api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-v4-pro')

        if not api_key:
            return None

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f'Explainer LLM call failed: {e}', exc_info=True)
            return None
