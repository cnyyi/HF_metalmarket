# 数据库迁移脚本：添加商户业务类型字段

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from utils.database import execute_update, execute_query


def add_business_type_field():
    """
    在Merchant表中添加BusinessType字段
    """
    print("=" * 80)
    print("数据库迁移：添加商户业务类型字段")
    print("=" * 80)
    
    # 检查字段是否已存在
    check_query = """
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Merchant'
        AND COLUMN_NAME = 'BusinessType'
    """
    
    result = execute_query(check_query, fetch_type='one')
    
    if result.count > 0:
        print("✓ BusinessType字段已存在，无需添加")
        return True
    
    # 添加BusinessType字段
    add_column_query = """
        ALTER TABLE Merchant
        ADD BusinessType NVARCHAR(100) NULL
    """
    
    try:
        execute_update(add_column_query)
        print("✓ 成功添加BusinessType字段")
        
        # 添加字段说明
        add_description_query = """
            EXEC sp_addextendedproperty 
                @name = N'MS_Description', 
                @value = N'业务类型', 
                @level0type = N'SCHEMA', @level0name = N'dbo',
                @level1type = N'TABLE',  @level1name = N'Merchant',
                @level2type = N'COLUMN', @level2name = N'BusinessType'
        """
        
        try:
            execute_update(add_description_query)
            print("✓ 成功添加字段说明")
        except Exception as e:
            print(f"⚠ 添加字段说明失败（可能已存在）: {e}")
        
        # 验证字段添加成功
        verify_query = """
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Merchant'
            AND COLUMN_NAME = 'BusinessType'
        """
        
        verify_result = execute_query(verify_query, fetch_type='one')
        
        if verify_result:
            print("\n字段信息：")
            print(f"  字段名称: {verify_result.COLUMN_NAME}")
            print(f"  数据类型: {verify_result.DATA_TYPE}({verify_result.CHARACTER_MAXIMUM_LENGTH})")
            print(f"  允许空值: {verify_result.IS_NULLABLE}")
        
        print("\n✓ 数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        return False


if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        success = add_business_type_field()
        sys.exit(0 if success else 1)