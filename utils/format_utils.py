# -*- coding: utf-8 -*-
import datetime


def format_date(val, fmt='%Y-%m-%d'):
    if not val:
        return ''
    if isinstance(val, str):
        return val[:10] if len(val) >= 10 else val
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime(fmt)
    return str(val)


def format_datetime(val, fmt='%Y-%m-%d %H:%M'):
    if not val:
        return ''
    if isinstance(val, str):
        return val[:16] if len(val) >= 16 else val
    if isinstance(val, datetime.datetime):
        return val.strftime(fmt)
    if isinstance(val, datetime.date):
        return datetime.datetime.combine(val, datetime.time.min).strftime(fmt)
    return str(val)


def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
