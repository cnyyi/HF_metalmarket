# -*- coding: utf-8 -*-
import re
from datetime import datetime


def generate_serial_no(cursor, prefix, table_name, column_name, date_format='%Y%m%d', seq_length=3):
    """
    生成流水号（格式：前缀+日期+序号）

    示例：
        generate_serial_no(cursor, 'CF', 'CashFlow', 'TransactionNo')
        → 'CF20260420001'

        generate_serial_no(cursor, 'EO', 'ExpenseOrder', 'OrderNo')
        → 'EO20260420001'

    Args:
        cursor: 数据库游标（在事务内）
        prefix: 前缀，如 'CF', 'EO'
        table_name: 查询序号的表名
        column_name: 查询序号的列名
        date_format: 日期格式，默认 '%Y%m%d'
        seq_length: 序号位数，默认3

    Returns:
        str: 生成的流水号
    """
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
        raise ValueError(f"Invalid table_name: {table_name}")
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', column_name):
        raise ValueError(f"Invalid column_name: {column_name}")

    today = datetime.now().strftime(date_format)
    like_pattern = f'{prefix}{today}%'

    cursor.execute(f"""
        SELECT {column_name} FROM {table_name}
        WHERE {column_name} LIKE ?
        ORDER BY {column_name} DESC
    """, (like_pattern,))
    row = cursor.fetchone()

    if row:
        last_val = row[0] if isinstance(row[0], str) else getattr(row, column_name, '')
        prefix_len = len(prefix) + len(today)
        try:
            last_seq = int(last_val[prefix_len:])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            new_seq = 1
    else:
        new_seq = 1

    return f'{prefix}{today}{new_seq:0{seq_length}d}'
