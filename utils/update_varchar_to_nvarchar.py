# 将所有varchar字段修改为nvarchar类型的工具脚本
import os
import sys
import pyodbc
import re

# 将项目根目录添加到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 导入配置
from config import Config


def get_all_varchar_columns(connection_string):
    """
    获取数据库中所有varchar类型的列
    
    Args:
        connection_string: 数据库连接字符串
        
    Returns:
        包含表名和列名的字典列表
    """
    query = """
        SELECT 
            TABLE_NAME, 
            COLUMN_NAME, 
            DATA_TYPE, 
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE DATA_TYPE = 'varchar'
        AND TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    
    with pyodbc.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]


def get_column_constraints(connection_string, table_name, column_name):
    """
    获取列上的所有约束
    
    Args:
        connection_string: 数据库连接字符串
        table_name: 表名
        column_name: 列名
        
    Returns:
        约束信息列表
    """
    query = """
        SELECT 
            tc.CONSTRAINT_NAME,
            tc.CONSTRAINT_TYPE,
            INDEX_NAME = CASE WHEN tc.CONSTRAINT_TYPE = 'UNIQUE' THEN i.NAME END,
            IS_PRIMARY_KEY = CASE WHEN i.is_primary_key = 1 THEN 1 ELSE 0 END
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        INNER JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu 
            ON tc.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
        LEFT JOIN sys.indexes i 
            ON tc.CONSTRAINT_NAME = i.NAME
            AND tc.TABLE_NAME = OBJECT_NAME(i.object_id)
        WHERE tc.TABLE_NAME = ?
        AND ccu.COLUMN_NAME = ?
    """
    
    with pyodbc.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (table_name, column_name))
            return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]


def update_column_to_nvarchar(connection_string, table_name, column_info):
    """
    将列类型从varchar修改为nvarchar
    
    Args:
        connection_string: 数据库连接字符串
        table_name: 表名
        column_info: 列信息字典
        
    Returns:
        布尔值，表示是否修改成功
    """
    column_name = column_info['COLUMN_NAME']
    length = column_info['CHARACTER_MAXIMUM_LENGTH']
    is_nullable = column_info['IS_NULLABLE']
    column_default = column_info['COLUMN_DEFAULT']
    
    # 构建新的数据类型
    if length == -1:
        new_data_type = 'nvarchar(max)'
    else:
        new_data_type = f'nvarchar({length})'
    
    # 构建空值约束
    null_constraint = 'NOT NULL' if is_nullable == 'NO' else 'NULL'
    
    # 处理User表的特殊情况（SQL Server关键字）
    if table_name == 'User':
        table_name = '[User]'
    
    # 构建ALTER TABLE语句
    alter_sql = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} {new_data_type} {null_constraint}"
    
    # 暂时不处理默认约束，因为这会导致语法错误
    # if column_default:
    #     alter_sql += f" CONSTRAINT DF_{table_name}_{column_name} DEFAULT {column_default}"
    
    try:
        with pyodbc.connect(connection_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(alter_sql)
                print(f"✓ 成功将 {table_name}.{column_name} 修改为 {new_data_type}")
                return True
    except Exception as e:
        print(f"✗ 修改 {table_name}.{column_name} 失败: {e}")
        return False


def main():
    """
    主函数
    """
    print("开始将所有varchar字段修改为nvarchar类型...")
    
    # 获取数据库连接字符串
    connection_string = Config.ODBC_CONNECTION_STRING
    
    # 获取所有varchar类型的列
    print("正在获取所有varchar类型的列...")
    varchar_columns = get_all_varchar_columns(connection_string)
    print(f"共找到 {len(varchar_columns)} 个varchar类型的列")
    
    # 遍历所有列并修改类型
    success_count = 0
    failure_count = 0
    
    for column_info in varchar_columns:
        table_name = column_info['TABLE_NAME']
        column_name = column_info['COLUMN_NAME']
        
        print(f"\n处理 {table_name}.{column_name}...")
        
        # 获取列上的约束
        constraints = get_column_constraints(connection_string, table_name, column_name)
        
        if constraints:
            print(f"  发现 {len(constraints)} 个约束:")
            for constraint in constraints:
                print(f"    - {constraint['CONSTRAINT_TYPE']}: {constraint['CONSTRAINT_NAME']}")
            
            # 对于被约束引用的列，我们需要先删除约束，修改列类型，然后重新创建约束
            # 这里简化处理，直接尝试修改（对于唯一约束可能会失败）
            print("  尝试直接修改列类型...")
            if update_column_to_nvarchar(connection_string, table_name, column_info):
                success_count += 1
            else:
                failure_count += 1
        else:
            # 没有约束，直接修改
            if update_column_to_nvarchar(connection_string, table_name, column_info):
                success_count += 1
            else:
                failure_count += 1
    
    print(f"\n修改完成!")
    print(f"成功: {success_count} 个列")
    print(f"失败: {failure_count} 个列")
    print(f"总列数: {len(varchar_columns)}")


if __name__ == "__main__":
    main()
