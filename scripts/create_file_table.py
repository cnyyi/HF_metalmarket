# -*- coding: utf-8 -*-
"""
创建文件管理表
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from config import Config


def create_file_attachment_table():
    """创建文件管理表"""
    conn = pyodbc.connect(Config.ODBC_CONNECTION_STRING)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FileAttachment' AND xtype='U')
            CREATE TABLE FileAttachment (
                FileID INT PRIMARY KEY IDENTITY,
                FileName NVARCHAR(200) NOT NULL,
                OriginalName NVARCHAR(200),
                FilePath NVARCHAR(500) NOT NULL,
                FileSize INT,
                FileType NVARCHAR(50),
                BizType NVARCHAR(50) NOT NULL,
                BizID INT,
                CreateBy INT,
                CreateTime DATETIME DEFAULT GETDATE()
            )
        """)
        
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_file_biz' AND object_id = OBJECT_ID('FileAttachment'))
            CREATE INDEX idx_file_biz ON FileAttachment(BizType, BizID)
        """)
        
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_file_create' AND object_id = OBJECT_ID('FileAttachment'))
            CREATE INDEX idx_file_create ON FileAttachment(CreateBy)
        """)
        
        conn.commit()
        print("FileAttachment 表创建成功!")
        
    except Exception as e:
        conn.rollback()
        print(f"创建失败: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    create_file_attachment_table()
