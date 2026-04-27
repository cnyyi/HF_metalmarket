# -*- coding: utf-8 -*-


def build_where(conditions, prefix=' WHERE '):
    if not conditions:
        return '', []
    clause = prefix + ' AND '.join(conditions)
    return clause, []


def paginate(cursor, base_query, count_query, params, page, per_page,
             order_by=None, sum_query=None):
    """
    通用分页查询

    Args:
        cursor: 数据库游标（已有连接）
        base_query: 基础 SELECT 语句（不含 WHERE/OFFSET）
        count_query: 基础 COUNT 语句（不含 WHERE）
        params: WHERE 条件参数列表
        page: 当前页码（从1开始）
        per_page: 每页条数
        order_by: 排序子句，如 "r.ReceivableID DESC"
        sum_query: 可选的汇总 SELECT 语句（不含 WHERE）

    Returns:
        dict: {
            'rows': list,
            'total_count': int,
            'total_pages': int,
            'current_page': int,
            'sum_row': Row|None
        }
    """
    offset = (page - 1) * per_page

    if order_by:
        base_query += f" ORDER BY {order_by}"

    base_query += " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"

    query_params = list(params)
    query_params.extend([offset, per_page])

    cursor.execute(base_query, query_params)
    rows = cursor.fetchall()

    count_params = list(params)
    cursor.execute(count_query, count_params)
    total_count = cursor.fetchone()[0]

    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

    sum_row = None
    if sum_query:
        cursor.execute(sum_query, count_params)
        sum_row = cursor.fetchone()

    return {
        'rows': rows,
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': page,
        'sum_row': sum_row,
    }


def paginate_result(items, total_count, page, per_page, **extra):
    """
    构建统一的分页返回结构

    Args:
        items: 当前页数据列表
        total_count: 总记录数
        page: 当前页码
        per_page: 每页条数
        **extra: 额外字段（如 summary）

    Returns:
        dict: {
            'items': list,
            'total_count': int,
            'total_pages': int,
            'current_page': int,
            **extra
        }
    """
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
    result = {
        'items': items,
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': page,
    }
    result.update(extra)
    return result
