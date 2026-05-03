import json
import logging
from datetime import datetime
from openai import OpenAI
from flask import current_app
from utils.database import DBConnection
from app.services.agent_prompt_builder import build_system_prompt
from app.services.agent_tools import get_registry

logger = logging.getLogger(__name__)


class AgentService:
    """AI 数据查询助手服务。

    流程：用户提问 → LLM (含 tools) → tool_calls → 执行工具 → 结果喂回 LLM → 自然语言回答
    """

    def __init__(self):
        self._client = None
        self._client_config = None

    def chat(self, user_id, conversation_id, message, source='admin', merchant_id=None, merchant_name=None):
        if not conversation_id:
            conversation_id = self._create_conversation(user_id, message, source)

        self._save_message(conversation_id, 'user', message)

        history = self._load_history(conversation_id)
        system_prompt = build_system_prompt(source, merchant_id, merchant_name)

        messages = [{'role': 'system', 'content': system_prompt}]
        for msg in history:
            messages.append({'role': msg['role'], 'content': msg['content']})

        registry = get_registry()
        tools = registry.get_all_schemas()

        injected_kwargs = {'_merchant_id': merchant_id, '_source': source}

        final_content, tool_call_detail = self._chat_with_tools(
            messages, tools, registry, injected_kwargs
        )

        self._save_message(conversation_id, 'assistant', final_content,
                           generated_sql=json.dumps(tool_call_detail, ensure_ascii=False) if tool_call_detail else None)

        return {
            'conversation_id': conversation_id,
            'content': final_content,
            'tool_calls': tool_call_detail,
            'generated_sql': None,
            'query_result': None
        }

    def _chat_with_tools(self, messages, tools, registry, injected_kwargs):
        max_iterations = 5
        tool_call_detail = []

        for iteration in range(max_iterations):
            response = self._call_llm_with_tools(messages, tools)

            if response is None:
                return 'AI 服务暂时不可用，请稍后重试。', tool_call_detail

            finish_reason = response.get('finish_reason')
            content = response.get('content') or ''

            if finish_reason == 'tool_calls' and response.get('tool_calls'):
                tool_calls = response['tool_calls']
                assistant_tool_msg = {
                    'role': 'assistant',
                    'content': content or None,
                    'tool_calls': tool_calls
                }
                messages.append(assistant_tool_msg)

                for tc in tool_calls:
                    fn_name = tc['function']['name']
                    try:
                        fn_args = json.loads(tc['function']['arguments'])
                    except json.JSONDecodeError:
                        fn_args = {}
                    fn_args.update(injected_kwargs)

                    try:
                        result = registry.execute(fn_name, **fn_args)
                    except Exception as e:
                        logger.error(f'Tool {fn_name} execution failed: {e}', exc_info=True)
                        result = f'\u6267\u884c\u51fa\u9519\uff1a{str(e)}'

                    result_str = json.dumps(result, ensure_ascii=False, default=str) if not isinstance(result, str) else result
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tc['id'],
                        'content': result_str[:8000]
                    })

                    tool_call_detail.append({
                        'id': tc['id'],
                        'name': fn_name,
                        'arguments': fn_args,
                        'result_preview': result_str[:500]
                    })

                continue

            return content, tool_call_detail

        return '\u95ee\u9898\u8f83\u590d\u6742\uff0c\u5df2\u67e5\u8be2\u90e8\u5206\u6570\u636e\u3002\u60a8\u53ef\u4ee5\u7ee7\u7eed\u8ffd\u95ee\u7ec6\u8282\u3002', tool_call_detail

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
        """获取或创建 OpenAI 客户端（懒加载单例，配置变更时重建）。"""
        api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

        current_config = (api_key, base_url)
        if self._client is not None and self._client_config == current_config:
            return self._client

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._client_config = current_config
        return self._client

    def _call_llm_with_tools(self, messages, tools):
        api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-v4-pro')

        if not api_key:
            return {'content': 'AI 助手未配置，请联系管理员设置 DEEPSEEK_API_KEY。', 'finish_reason': 'stop', 'tool_calls': None}

        try:
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

            tool_calls = None
            if msg.tool_calls:
                tool_calls = []
                for tc in msg.tool_calls:
                    tool_calls.append({
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
                'tool_calls': tool_calls
            }
        except Exception as e:
            logger.error(f'DeepSeek API \u8c03\u7528\u5931\u8d25: {e}', exc_info=True)
            return None
