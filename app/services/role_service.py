import datetime
from app.models.role import Role
from app.models.permission import Permission
from utils.database import execute_query, execute_update, execute_bulk_update


class RoleService:

    @staticmethod
    def get_all_roles():
        query = """
            SELECT RoleID, RoleName, RoleCode, Description, IsActive, CreateTime, UpdateTime
            FROM Role
            ORDER BY RoleID
        """
        results = execute_query(query, fetch_type='all')
        roles = []
        for result in results:
            role = Role(
                role_id=result.RoleID,
                role_name=result.RoleName,
                role_code=result.RoleCode,
                description=result.Description,
                is_active=result.IsActive,
                create_time=result.CreateTime,
                update_time=result.UpdateTime
            )
            roles.append(role)
        return roles

    @staticmethod
    def get_role_by_id(role_id):
        query = """
            SELECT RoleID, RoleName, RoleCode, Description, IsActive, CreateTime, UpdateTime
            FROM Role
            WHERE RoleID = ?
        """
        result = execute_query(query, (role_id,), fetch_type='one')
        if not result:
            return None
        role = Role(
            role_id=result.RoleID,
            role_name=result.RoleName,
            role_code=result.RoleCode,
            description=result.Description,
            is_active=result.IsActive,
            create_time=result.CreateTime,
            update_time=result.UpdateTime
        )
        return role

    @staticmethod
    def create_role(role_name, role_code, description=None):
        check_query = "SELECT RoleID FROM Role WHERE RoleCode = ?"
        existing = execute_query(check_query, (role_code,), fetch_type='one')
        if existing:
            return None
        insert_query = """
            INSERT INTO Role (RoleName, RoleCode, Description, IsActive, CreateTime)
            VALUES (?, ?, ?, 1, ?)
        """
        execute_update(insert_query, (role_name, role_code, description, datetime.datetime.now()))
        return RoleService.get_role_by_code(role_code)

    @staticmethod
    def get_role_by_code(role_code):
        query = """
            SELECT RoleID, RoleName, RoleCode, Description, IsActive, CreateTime, UpdateTime
            FROM Role
            WHERE RoleCode = ?
        """
        result = execute_query(query, (role_code,), fetch_type='one')
        if not result:
            return None
        role = Role(
            role_id=result.RoleID,
            role_name=result.RoleName,
            role_code=result.RoleCode,
            description=result.Description,
            is_active=result.IsActive,
            create_time=result.CreateTime,
            update_time=result.UpdateTime
        )
        return role

    @staticmethod
    def update_role(role_id, role_name, description=None):
        update_query = """
            UPDATE Role
            SET RoleName = ?, Description = ?, UpdateTime = ?
            WHERE RoleID = ?
        """
        execute_update(update_query, (role_name, description, datetime.datetime.now(), role_id))
        return RoleService.get_role_by_id(role_id)

    @staticmethod
    def delete_role(role_id):
        if role_id <= 3:
            return False
        delete_rp_query = "DELETE FROM RolePermission WHERE RoleID = ?"
        execute_update(delete_rp_query, (role_id,))
        delete_ur_query = "DELETE FROM UserRole WHERE RoleID = ?"
        execute_update(delete_ur_query, (role_id,))
        delete_role_query = "DELETE FROM Role WHERE RoleID = ?"
        result = execute_update(delete_role_query, (role_id,))
        return result > 0

    @staticmethod
    def get_all_permissions_grouped():
        query = """
            SELECT PermissionID, PermissionName, PermissionCode, Description, ModuleName, OperationCode, SortOrder, IsActive, CreateTime, UpdateTime
            FROM Permission
            WHERE IsActive = 1 AND OperationCode IN (N'view', N'create', N'edit', N'delete', N'reading', N'pay')
            ORDER BY ModuleName, SortOrder
        """
        results = execute_query(query, fetch_type='all')
        grouped = {}
        for result in results:
            module_name = getattr(result, 'ModuleName', None) or '未分类'
            permission = Permission(
                permission_id=result.PermissionID,
                permission_name=result.PermissionName,
                permission_code=result.PermissionCode,
                description=result.Description,
                module_name=result.ModuleName,
                operation_code=getattr(result, 'OperationCode', None),
                sort_order=getattr(result, 'SortOrder', 0),
                is_active=result.IsActive,
                create_time=result.CreateTime,
                update_time=result.UpdateTime
            )
            if module_name not in grouped:
                grouped[module_name] = []
            grouped[module_name].append(permission)
        return grouped

    @staticmethod
    def get_role_permissions(role_id):
        query = "SELECT PermissionID FROM RolePermission WHERE RoleID = ?"
        results = execute_query(query, (role_id,), fetch_type='all')
        return {result.PermissionID for result in results}

    @staticmethod
    def update_role_permissions(role_id, permission_ids):
        delete_query = "DELETE FROM RolePermission WHERE RoleID = ?"
        execute_update(delete_query, (role_id,))
        if permission_ids:
            insert_query = "INSERT INTO RolePermission (RoleID, PermissionID) VALUES (?, ?)"
            params_list = [(role_id, pid) for pid in permission_ids]
            execute_bulk_update(insert_query, params_list)
        return True

    @staticmethod
    def get_all_permissions():
        query = """
            SELECT PermissionID, PermissionName, PermissionCode, Description, ModuleName, OperationCode, SortOrder, IsActive, CreateTime, UpdateTime
            FROM Permission
            ORDER BY ModuleName, SortOrder
        """
        results = execute_query(query, fetch_type='all')
        permissions = []
        for result in results:
            permission = Permission(
                permission_id=result.PermissionID,
                permission_name=result.PermissionName,
                permission_code=result.PermissionCode,
                description=result.Description,
                module_name=result.ModuleName,
                operation_code=getattr(result, 'OperationCode', None),
                sort_order=getattr(result, 'SortOrder', 0),
                is_active=result.IsActive,
                create_time=result.CreateTime,
                update_time=result.UpdateTime
            )
            permissions.append(permission)
        return permissions
