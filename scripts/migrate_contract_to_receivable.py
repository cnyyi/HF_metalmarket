"""将合同表已有数据插入应收账款表

映射关系：
- MerchantID → MerchantID + CustomerID
- ExpenseTypeID = 1（租金）
- ActualAmount → Amount + RemainingAmount
- Description = 合同名称 + 合同编号
- StartDate → DueDate
- ReferenceID = ContractID, ReferenceType = 'contract'
- CustomerType = 'Merchant'
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import create_app
from config.development import DevelopmentConfig

app = create_app(DevelopmentConfig)

with app.app_context():
    from utils.database import DBConnection
    with DBConnection() as conn:
        cursor = conn.cursor()

        # 先检查是否已有合同关联的应收，避免重复插入
        cursor.execute("SELECT COUNT(*) as cnt FROM Receivable WHERE ReferenceType = 'contract'")
        existing = cursor.fetchone().cnt
        if existing > 0:
            print(f"已有 {existing} 条合同关联的应收记录，跳过插入（避免重复）")
        else:
            # 插入合同数据到应收账款
            cursor.execute("""
                INSERT INTO Receivable (
                    MerchantID, ExpenseTypeID, Amount, Description,
                    DueDate, Status, PaidAmount, RemainingAmount,
                    ReferenceID, ReferenceType, CustomerType, CustomerID
                )
                SELECT
                    c.MerchantID,
                    1,                          -- ExpenseTypeID = 租金
                    c.ActualAmount,             -- Amount
                    c.ContractName + N'（' + c.ContractNumber + N'）',  -- Description
                    c.StartDate,                -- DueDate
                    N'未付款',                   -- Status
                    0,                          -- PaidAmount
                    c.ActualAmount,             -- RemainingAmount
                    c.ContractID,               -- ReferenceID
                    N'contract',                -- ReferenceType
                    N'Merchant',                -- CustomerType
                    c.MerchantID                -- CustomerID
                FROM Contract c
                ORDER BY c.ContractID
            """)
            conn.commit()
            inserted = cursor.rowcount
            print(f"成功插入 {inserted} 条合同应收记录")

        # 验证结果
        cursor.execute("""
            SELECT r.ReceivableID, r.MerchantID, m.MerchantName, r.Amount,
                   r.Description, r.DueDate, r.Status, r.ReferenceID
            FROM Receivable r
            LEFT JOIN Merchant m ON r.MerchantID = m.MerchantID
            WHERE r.ReferenceType = N'contract'
            ORDER BY r.ReceivableID
        """)
        rows = cursor.fetchall()
        print(f"\n当前合同应收记录共 {len(rows)} 条：")
        for r in rows:
            print(f"  应收ID={r.ReceivableID} | 商户ID={r.MerchantID} | 商户={r.MerchantName} | "
                  f"金额={r.Amount} | 描述={r.Description} | 到期={r.DueDate} | 状态={r.Status} | "
                  f"合同ID={r.ReferenceID}")
