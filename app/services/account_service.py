# -*- coding: utf-8 -*-
"""
账户管理服务层
负责资金账户的CRUD、余额操作等
"""
import logging
from datetime import datetime
from utils.database import DBConnection
from utils.format_utils import format_datetime

logger = logging.getLogger(__name__)


class AccountService:
    """资金账户管理服务"""

    # ========== 账户 CRUD ==========

    def get_accounts(self, status=None):
        """获取账户列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT AccountID, AccountName, AccountType,
                       BankName, BankAccount,
                       Balance, IsDefault, Status, Remark,
                       CreateTime, UpdateTime
                FROM Account
            """
            params = []
            conditions = []
            if status:
                conditions.append("Status = ?")
                params.append(status)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY IsDefault DESC, AccountID ASC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'account_id': row.AccountID,
                    'account_name': row.AccountName,
                    'account_type': row.AccountType,
                    'bank_name': row.BankName or '',
                    'bank_account': row.BankAccount or '',
                    'balance': float(row.Balance),
                    'is_default': bool(row.IsDefault),
                    'status': row.Status,
                    'remark': row.Remark or '',
                    'create_time': format_datetime(row.CreateTime),
                    'update_time': format_datetime(row.UpdateTime),
                })
            return result

    def get_account_by_id(self, account_id):
        """获取单个账户详情"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AccountID, AccountName, AccountType,
                       BankName, BankAccount,
                       Balance, IsDefault, Status, Remark,
                       CreateTime, UpdateTime
                FROM Account
                WHERE AccountID = ?
            """, (account_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'account_id': row.AccountID,
                'account_name': row.AccountName,
                'account_type': row.AccountType,
                'bank_name': row.BankName or '',
                'bank_account': row.BankAccount or '',
                'balance': float(row.Balance),
                'is_default': bool(row.IsDefault),
                'status': row.Status,
                'remark': row.Remark or '',
            }

    def create_account(self, account_name, account_type, bank_name=None,
                       bank_account=None, is_default=False, remark=None):
        """创建账户"""
        if not account_name or not account_name.strip():
            raise ValueError("账户名称不能为空")
        if account_type not in ('Cash', 'Bank', 'WeChat'):
            raise ValueError("账户类型无效，必须是 Cash/Bank/WeChat")
        if account_type == 'Bank' and not bank_name:
            raise ValueError("银行账户必须填写银行名称")

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 如果设为默认账户，先取消其他默认
            if is_default:
                cursor.execute("UPDATE Account SET IsDefault = 0 WHERE IsDefault = 1")

            cursor.execute("""
                INSERT INTO Account (AccountName, AccountType, BankName, BankAccount,
                                     Balance, IsDefault, Status, Remark)
                OUTPUT INSERTED.AccountID
                VALUES (?, ?, ?, ?, 0, ?, N'有效', ?)
            """, account_name.strip(), account_type,
                bank_name.strip() if bank_name else None,
                bank_account.strip() if bank_account else None,
                1 if is_default else 0,
                remark.strip() if remark else None)

            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id

    def update_account(self, account_id, account_name=None, account_type=None,
                       bank_name=None, bank_account=None, is_default=None,
                       remark=None):
        """更新账户信息"""
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError("账户不存在")

        with DBConnection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if account_name is not None:
                if not account_name.strip():
                    raise ValueError("账户名称不能为空")
                updates.append("AccountName = ?")
                params.append(account_name.strip())

            if account_type is not None:
                if account_type not in ('Cash', 'Bank', 'WeChat'):
                    raise ValueError("账户类型无效")
                updates.append("AccountType = ?")
                params.append(account_type)

            if bank_name is not None:
                updates.append("BankName = ?")
                params.append(bank_name.strip() if bank_name else None)

            if bank_account is not None:
                updates.append("BankAccount = ?")
                params.append(bank_account.strip() if bank_account else None)

            if is_default is not None:
                if is_default:
                    cursor.execute("UPDATE Account SET IsDefault = 0 WHERE IsDefault = 1")
                updates.append("IsDefault = ?")
                params.append(1 if is_default else 0)

            if remark is not None:
                updates.append("Remark = ?")
                params.append(remark.strip() if remark else None)

            if not updates:
                return True

            updates.append("UpdateTime = GETDATE()")
            params.append(account_id)

            sql = f"UPDATE Account SET {', '.join(updates)} WHERE AccountID = ?"
            cursor.execute(sql, params)
            conn.commit()
            return True

    def toggle_account_status(self, account_id):
        """切换账户状态（有效/停用）"""
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError("账户不存在")
        if account['is_default'] and account['status'] == '有效':
            raise ValueError("默认账户不能停用")

        new_status = '停用' if account['status'] == '有效' else '有效'
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Account SET Status = ?, UpdateTime = GETDATE()
                WHERE AccountID = ?
            """, (new_status, account_id))
            conn.commit()
            return new_status

    # ========== 余额操作（内部方法，供 FinanceService 调用） ==========

    def _adjust_balance(self, cursor, account_id, amount, direction):
        """
        调整账户余额（在事务内调用，不自行 commit）

        Args:
            cursor: 已有事务的游标
            account_id: 账户ID
            amount: 金额（正数）
            direction: 'income' 或 'expense'
        """
        if direction == 'income':
            cursor.execute("""
                UPDATE Account SET Balance = Balance + ?, UpdateTime = GETDATE()
                WHERE AccountID = ?
            """, (amount, account_id))
        elif direction == 'expense':
            # 先检查余额是否足够
            cursor.execute("SELECT Balance FROM Account WHERE AccountID = ?", (account_id,))
            row = cursor.fetchone()
            if row and float(row.Balance) < amount:
                raise ValueError(f"账户余额不足（当前余额: ¥{float(row.Balance):.2f}）")
            cursor.execute("""
                UPDATE Account SET Balance = Balance - ?, UpdateTime = GETDATE()
                WHERE AccountID = ?
            """, (amount, account_id))

    def get_default_account_id(self):
        """获取默认账户ID"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT AccountID FROM Account WHERE IsDefault = 1 AND Status = N'有效'")
            row = cursor.fetchone()
            if row:
                return row.AccountID
            # 没有默认账户，取第一个有效账户
            cursor.execute("SELECT TOP 1 AccountID FROM Account WHERE Status = N'有效' ORDER BY AccountID")
            row = cursor.fetchone()
            return row.AccountID if row else None

    def get_balance_summary(self):
        """获取所有账户余额汇总"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) AS TotalAccounts,
                    ISNULL(SUM(CASE WHEN Status = N'有效' THEN Balance ELSE 0 END), 0) AS TotalBalance,
                    ISNULL(SUM(CASE WHEN AccountType = 'Cash' AND Status = N'有效' THEN Balance ELSE 0 END), 0) AS CashBalance,
                    ISNULL(SUM(CASE WHEN AccountType = 'Bank' AND Status = N'有效' THEN Balance ELSE 0 END), 0) AS BankBalance,
                    ISNULL(SUM(CASE WHEN AccountType = 'WeChat' AND Status = N'有效' THEN Balance ELSE 0 END), 0) AS WeChatBalance
                FROM Account
            """)
            row = cursor.fetchone()
            return {
                'total_accounts': row.TotalAccounts,
                'total_balance': float(row.TotalBalance),
                'cash_balance': float(row.CashBalance),
                'bank_balance': float(row.BankBalance),
                'wechat_balance': float(row.WeChatBalance),
            }
