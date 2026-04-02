# 数据库工具类
import pyodbc
import logging
from flask import current_app
from functools import wraps

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_connection():
    """
    获取数据库连接
    """
    try:
        conn = pyodbc.connect(current_app.config['ODBC_CONNECTION_STRING'])
        return conn
    except Exception as e:
        logger.error(f"获取数据库连接失败: {e}")
        raise


def close_connection(conn):
    """
    关闭数据库连接
    """
    if conn:
        try:
            conn.close()
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")


def execute_query(query, params=None, fetch_type='all'):
    """
    执行查询操作
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch_type: 查询结果类型 ('all', 'one', 'none')
        
    Returns:
        查询结果
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_type == 'all':
            result = cursor.fetchall()
        elif fetch_type == 'one':
            result = cursor.fetchone()
        else:
            result = None
            
        return result
    except Exception as e:
        logger.error(f"执行查询失败: {query}\n错误信息: {e}")
        raise
    finally:
        if conn:
            close_connection(conn)


def execute_update(query, params=None):
    """
    执行更新操作（INSERT, UPDATE, DELETE）
    
    Args:
        query: SQL更新语句
        params: 更新参数
        
    Returns:
        受影响的行数
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        logger.error(f"执行更新失败: {query}\n错误信息: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            close_connection(conn)


def execute_bulk_update(query, params_list):
    """
    执行批量更新操作
    
    Args:
        query: SQL更新语句
        params_list: 参数列表
        
    Returns:
        受影响的行数
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        logger.error(f"执行批量更新失败: {query}\n错误信息: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            close_connection(conn)


def get_table_columns(table_name):
    """
    获取表的列信息
    
    Args:
        table_name: 表名
        
    Returns:
        列信息列表
    """
    query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """
    return execute_query(query, (table_name,), fetch_type='all')


def table_exists(table_name):
    """
    检查表是否存在
    
    Args:
        table_name: 表名
        
    Returns:
        布尔值
    """
    query = f"""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = ?
    """
    result = execute_query(query, (table_name,), fetch_type='one')
    return result.count > 0
