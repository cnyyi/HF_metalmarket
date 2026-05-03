class Memory:
    def __init__(self):
        self._data = {}

    def set(self, step_id, result):
        self._data[step_id] = result

    def get(self, path):
        parts = path.split('.')
        value = self._data.get(parts[0])
        for key in parts[1:]:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def get_all(self):
        return dict(self._data)

    def clear(self):
        self._data = {}
