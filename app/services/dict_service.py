import datetime
from utils.database import execute_query, execute_update


class DictService:

    @staticmethod
    def get_dict_list(page=1, per_page=15, dict_type=None, keyword=None, is_active=None):
        base_query = """
            SELECT DictID, DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime, UpdateTime, UnitPrice
            FROM Sys_Dictionary
        """
        count_query = """
            SELECT COUNT(*) as cnt
            FROM Sys_Dictionary
        """

        conditions = []
        params = []

        if dict_type:
            conditions.append("DictType = ?")
            params.append(dict_type)

        if keyword:
            conditions.append("(DictCode LIKE ? OR DictName LIKE ? OR Description LIKE ?)")
            kw = f'%{keyword}%'
            params.extend([kw, kw, kw])

        if is_active is not None:
            conditions.append("IsActive = ?")
            params.append(is_active)

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        base_query += where_clause
        count_query += where_clause

        offset = (page - 1) * per_page
        base_query += " ORDER BY DictType, SortOrder, DictID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, per_page])

        results = execute_query(base_query, tuple(params), fetch_type='all')

        items = []
        for r in results:
            items.append({
                'dict_id': r.DictID,
                'dict_type': r.DictType,
                'dict_code': r.DictCode,
                'dict_name': r.DictName,
                'description': r.Description or '',
                'sort_order': r.SortOrder,
                'is_active': r.IsActive,
                'create_time': r.CreateTime.strftime('%Y-%m-%d %H:%M') if r.CreateTime else '',
                'update_time': r.UpdateTime.strftime('%Y-%m-%d %H:%M') if r.UpdateTime else '',
                'unit_price': float(r.UnitPrice) if r.UnitPrice is not None else None
            })

        count_params = tuple(params[:-2])
        count_result = execute_query(count_query, count_params, fetch_type='one')
        total_count = count_result.cnt
        total_pages = (total_count + per_page - 1) // per_page

        return items, total_count, total_pages

    @staticmethod
    def get_dict_by_id(dict_id):
        query = """
            SELECT DictID, DictType, DictCode, DictName, Description, SortOrder, IsActive, CreateTime, UpdateTime, UnitPrice
            FROM Sys_Dictionary
            WHERE DictID = ?
        """
        result = execute_query(query, (dict_id,), fetch_type='one')

        if not result:
            return None

        return {
            'dict_id': result.DictID,
            'dict_type': result.DictType,
            'dict_code': result.DictCode,
            'dict_name': result.DictName,
            'description': result.Description or '',
            'sort_order': result.SortOrder,
            'is_active': result.IsActive,
            'create_time': result.CreateTime.strftime('%Y-%m-%d %H:%M') if result.CreateTime else '',
            'update_time': result.UpdateTime.strftime('%Y-%m-%d %H:%M') if result.UpdateTime else '',
            'unit_price': float(result.UnitPrice) if result.UnitPrice is not None else None
        }

    @staticmethod
    def get_dict_types():
        query = """
            SELECT DISTINCT DictType FROM Sys_Dictionary ORDER BY DictType
        """
        results = execute_query(query, fetch_type='all')
        return [r.DictType for r in results]

    @staticmethod
    def create_dict(dict_type, dict_code, dict_name, description=None, sort_order=0, is_active=True, unit_price=None):
        existing = execute_query(
            "SELECT DictID FROM Sys_Dictionary WHERE DictType = ? AND DictCode = ?",
            (dict_type, dict_code),
            fetch_type='one'
        )
        if existing:
            return None

        insert_query = """
            INSERT INTO Sys_Dictionary (DictType, DictCode, DictName, Description, SortOrder, IsActive, UnitPrice, CreateTime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.datetime.now()
        execute_update(insert_query, (dict_type, dict_code, dict_name, description, sort_order, is_active, unit_price, now))

        result = execute_query(
            "SELECT DictID FROM Sys_Dictionary WHERE DictType = ? AND DictCode = ?",
            (dict_type, dict_code),
            fetch_type='one'
        )
        return result.DictID if result else None

    @staticmethod
    def update_dict(dict_id, dict_type, dict_code, dict_name, description=None, sort_order=0, is_active=True, unit_price=None):
        existing = execute_query(
            "SELECT DictID FROM Sys_Dictionary WHERE DictType = ? AND DictCode = ? AND DictID != ?",
            (dict_type, dict_code, dict_id),
            fetch_type='one'
        )
        if existing:
            return False

        update_query = """
            UPDATE Sys_Dictionary
            SET DictType = ?, DictCode = ?, DictName = ?, Description = ?, SortOrder = ?, IsActive = ?, UnitPrice = ?, UpdateTime = ?
            WHERE DictID = ?
        """
        now = datetime.datetime.now()
        rows = execute_update(update_query, (dict_type, dict_code, dict_name, description, sort_order, is_active, unit_price, now, dict_id))
        return rows > 0

    @staticmethod
    def delete_dict(dict_id):
        rows = execute_update("DELETE FROM Sys_Dictionary WHERE DictID = ?", (dict_id,))
        return rows > 0

    @staticmethod
    def batch_update_status(dict_ids, is_active):
        if not dict_ids:
            return 0
        placeholders = ','.join(['?'] * len(dict_ids))
        query = f"UPDATE Sys_Dictionary SET IsActive = ?, UpdateTime = ? WHERE DictID IN ({placeholders})"
        params = [is_active, datetime.datetime.now()] + list(dict_ids)
        rows = execute_update(query, tuple(params))
        return rows

    @staticmethod
    def batch_delete(dict_ids):
        if not dict_ids:
            return 0
        placeholders = ','.join(['?'] * len(dict_ids))
        query = f"DELETE FROM Sys_Dictionary WHERE DictID IN ({placeholders})"
        rows = execute_update(query, tuple(dict_ids))
        return rows

    @staticmethod
    def get_expense_items(dict_type='expense_item_expend'):
        """获取费用项字典列表（用于应收/应付费用类型下拉）

        Args:
            dict_type: 字典类型
                - expense_item_income  收入方向（应收账款）
                - expense_item_expend  支出方向（应付账款）

        Returns:
            list[dict]: [{'dict_id': int, 'dict_code': str, 'dict_name': str}, ...]
        """
        query = """
            SELECT DictID, DictCode, DictName
            FROM Sys_Dictionary
            WHERE DictType = ? AND IsActive = 1
            ORDER BY SortOrder
        """
        results = execute_query(query, (dict_type,), fetch_type='all')
        return [{
            'dict_id': r.DictID,
            'dict_code': r.DictCode,
            'dict_name': r.DictName
        } for r in results]
