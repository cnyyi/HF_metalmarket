import json
import logging

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, registry, memory):
        self.registry = registry
        self.memory = memory

    def execute_plan(self, plan, injected_kwargs):
        for step in plan:
            resolved_args = self._resolve_args(step.get('args', {}))
            resolved_args.update(injected_kwargs)
            try:
                result = self.registry.execute(step['tool'], **resolved_args)
            except Exception as e:
                logger.error(f"Tool {step['tool']} execution failed: {e}", exc_info=True)
                result = {'error': f'执行出错：{str(e)}'}
            self.memory.set(step['id'], result)
        return self.memory.get_all()

    def _resolve_args(self, args):
        resolved = {}
        for key, value in args.items():
            if isinstance(value, str) and value.startswith('$'):
                resolved[key] = self.memory.get(value[1:])
            else:
                resolved[key] = value
        return resolved
