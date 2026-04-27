# -*- coding: utf-8 -*-
"""
工资管理服务层
负责员工工资档案管理、月度工资核算、审核发放等业务逻辑
"""
import logging
from datetime import datetime, date
from utils.database import DBConnection
from utils.format_utils import format_date, format_datetime

logger = logging.getLogger(__name__)


class SalaryService:
    """工资管理服务"""

    # ========== 工资档案管理 ==========

    def get_profiles(self, page=1, per_page=10, search=None, status=None):
        """获取工资档案列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT sp.ProfileID, sp.UserID, u.RealName, u.Username, u.Phone,
                       sp.BaseSalary, sp.PostSalary, sp.Subsidy,
                       sp.Insurance, sp.HousingFund,
                       sp.EffectiveDate, sp.Status, sp.Description,
                       sp.CreateTime, sp.UpdateTime
                FROM SalaryProfile sp
                INNER JOIN [User] u ON sp.UserID = u.UserID
            """

            count_query = "SELECT COUNT(*) FROM SalaryProfile sp INNER JOIN [User] u ON sp.UserID = u.UserID"

            conditions = []
            params = []

            if search:
                conditions.append("(u.RealName LIKE ? OR u.Username LIKE ? OR u.Phone LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p, p])

            if status:
                conditions.append("sp.Status = ?")
                params.append(status)

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY sp.ProfileID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            result_list = []
            for row in rows:
                result_list.append({
                    'profile_id': row.ProfileID,
                    'user_id': row.UserID,
                    'real_name': row.RealName or '',
                    'username': row.Username or '',
                    'phone': row.Phone or '',
                    'base_salary': float(row.BaseSalary),
                    'post_salary': float(row.PostSalary),
                    'subsidy': float(row.Subsidy),
                    'insurance': float(row.Insurance),
                    'housing_fund': float(row.HousingFund),
                    'effective_date': format_date(row.EffectiveDate),
                    'status': row.Status,
                    'description': row.Description or '',
                    'create_time': format_datetime(row.CreateTime),
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': result_list,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    def get_profile_by_id(self, profile_id):
        """获取单个工资档案"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sp.ProfileID, sp.UserID, u.RealName, u.Username, u.Phone,
                       sp.BaseSalary, sp.PostSalary, sp.Subsidy,
                       sp.Insurance, sp.HousingFund,
                       sp.EffectiveDate, sp.Status, sp.Description,
                       sp.CreateTime, sp.UpdateTime
                FROM SalaryProfile sp
                INNER JOIN [User] u ON sp.UserID = u.UserID
                WHERE sp.ProfileID = ?
            """, (profile_id,))
            return cursor.fetchone()

    def get_profile_by_user(self, user_id):
        """获取某用户当前有效的工资档案"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 sp.ProfileID, sp.UserID, u.RealName,
                       sp.BaseSalary, sp.PostSalary, sp.Subsidy,
                       sp.Insurance, sp.HousingFund,
                       sp.EffectiveDate, sp.Status, sp.Description
                FROM SalaryProfile sp
                INNER JOIN [User] u ON sp.UserID = u.UserID
                WHERE sp.UserID = ? AND sp.Status = N'有效'
                ORDER BY sp.EffectiveDate DESC
            """, (user_id,))
            return cursor.fetchone()

    def create_profile(self, user_id, base_salary=0, post_salary=0, subsidy=0,
                       insurance=0, housing_fund=0, effective_date=None,
                       description=None):
        """创建工资档案"""
        if not user_id:
            raise ValueError("请选择员工")
        if not effective_date:
            raise ValueError("请选择生效日期")

        # 检查同一用户同一日期是否已有档案
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM SalaryProfile
                WHERE UserID = ? AND EffectiveDate = ?
            """, (user_id, effective_date))
            if cursor.fetchone()[0] > 0:
                raise ValueError("该员工在此日期已有工资档案")

            cursor.execute("""
                INSERT INTO SalaryProfile (
                    UserID, BaseSalary, PostSalary, Subsidy,
                    Insurance, HousingFund, EffectiveDate, Status, Description
                ) OUTPUT INSERTED.ProfileID
                VALUES (?, ?, ?, ?, ?, ?, ?, N'有效', ?)
            """, (user_id, float(base_salary), float(post_salary), float(subsidy),
                  float(insurance), float(housing_fund), effective_date, description))

            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
            return new_id

    def update_profile(self, profile_id, base_salary=None, post_salary=None,
                       subsidy=None, insurance=None, housing_fund=None,
                       status=None, description=None):
        """更新工资档案"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            sets = []
            params = []

            if base_salary is not None:
                sets.append("BaseSalary = ?")
                params.append(float(base_salary))
            if post_salary is not None:
                sets.append("PostSalary = ?")
                params.append(float(post_salary))
            if subsidy is not None:
                sets.append("Subsidy = ?")
                params.append(float(subsidy))
            if insurance is not None:
                sets.append("Insurance = ?")
                params.append(float(insurance))
            if housing_fund is not None:
                sets.append("HousingFund = ?")
                params.append(float(housing_fund))
            if status is not None:
                sets.append("Status = ?")
                params.append(status)
            if description is not None:
                sets.append("Description = ?")
                params.append(description)

            if not sets:
                return False

            sets.append("UpdateTime = GETDATE()")
            params.append(profile_id)

            sql = f"UPDATE SalaryProfile SET {', '.join(sets)} WHERE ProfileID = ?"
            cursor.execute(sql, params)
            conn.commit()
            return True

    def delete_profile(self, profile_id):
        """删除工资档案（仅允许删除未使用的）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            # 检查是否有关联的工资记录
            cursor.execute("""
                SELECT COUNT(*) FROM SalaryRecord
                WHERE UserID IN (SELECT UserID FROM SalaryProfile WHERE ProfileID = ?)
            """, (profile_id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("该员工已有工资记录，不能删除档案，请改为停用")

            cursor.execute("DELETE FROM SalaryProfile WHERE ProfileID = ?", (profile_id,))
            conn.commit()
            return True

    # ========== 月度工资核算 ==========

    def get_salary_records(self, page=1, per_page=10, year_month=None,
                           status=None, search=None):
        """获取月度工资单列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT sr.RecordID, sr.UserID, u.RealName, u.Username, u.Phone,
                       sr.YearMonth, sr.BaseSalary, sr.PostSalary, sr.Subsidy,
                       sr.OvertimePay, sr.Bonus, sr.OtherIncome, sr.GrossPay,
                       sr.Insurance, sr.HousingFund, sr.Tax, sr.Deduction,
                       sr.TotalDeduction, sr.NetPay,
                       sr.WorkDays, sr.ActualDays,
                       sr.Status, sr.PayableID, sr.Description,
                       sr.CreateTime, sr.UpdateTime
                FROM SalaryRecord sr
                INNER JOIN [User] u ON sr.UserID = u.UserID
            """

            count_query = "SELECT COUNT(*) FROM SalaryRecord sr INNER JOIN [User] u ON sr.UserID = u.UserID"

            conditions = []
            params = []

            if year_month:
                conditions.append("sr.YearMonth = ?")
                params.append(year_month)

            if status:
                conditions.append("sr.Status = ?")
                params.append(status)

            if search:
                conditions.append("(u.RealName LIKE ? OR u.Username LIKE ?)")
                p = f'%{search}%'
                params.extend([p, p])

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause

            offset = (page - 1) * per_page
            base_query += " ORDER BY sr.YearMonth DESC, sr.RecordID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, per_page])

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            count_params = params[:-2]
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            result_list = []
            for row in rows:
                result_list.append({
                    'record_id': row.RecordID,
                    'user_id': row.UserID,
                    'real_name': row.RealName or '',
                    'username': row.Username or '',
                    'year_month': row.YearMonth or '',
                    'base_salary': float(row.BaseSalary),
                    'post_salary': float(row.PostSalary),
                    'subsidy': float(row.Subsidy),
                    'overtime_pay': float(row.OvertimePay),
                    'bonus': float(row.Bonus),
                    'other_income': float(row.OtherIncome),
                    'gross_pay': float(row.GrossPay),
                    'insurance': float(row.Insurance),
                    'housing_fund': float(row.HousingFund),
                    'tax': float(row.Tax),
                    'deduction': float(row.Deduction),
                    'total_deduction': float(row.TotalDeduction),
                    'net_pay': float(row.NetPay),
                    'work_days': row.WorkDays or 0,
                    'actual_days': row.ActualDays or 0,
                    'status': row.Status,
                    'payable_id': row.PayableID,
                    'description': row.Description or '',
                    'create_time': format_datetime(row.CreateTime),
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': result_list,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    def get_salary_record_by_id(self, record_id):
        """获取单条工资记录"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sr.RecordID, sr.UserID, u.RealName, u.Username, u.Phone,
                       sr.YearMonth, sr.BaseSalary, sr.PostSalary, sr.Subsidy,
                       sr.OvertimePay, sr.Bonus, sr.OtherIncome, sr.GrossPay,
                       sr.Insurance, sr.HousingFund, sr.Tax, sr.Deduction,
                       sr.TotalDeduction, sr.NetPay,
                       sr.WorkDays, sr.ActualDays,
                       sr.Status, sr.PayableID, sr.ApprovedBy, sr.ApprovedTime,
                       sr.Description, sr.CreateTime, sr.UpdateTime
                FROM SalaryRecord sr
                INNER JOIN [User] u ON sr.UserID = u.UserID
                WHERE sr.RecordID = ?
            """, (record_id,))
            return cursor.fetchone()

    def generate_monthly_salary(self, year_month, user_ids=None):
        """
        批量生成月度工资单
        从员工工资档案读取基础数据，生成待审核的工资记录

        Args:
            year_month: 工资月份 YYYY-MM
            user_ids: 指定员工ID列表，None表示全部有效档案

        Returns:
            dict: {success, message, generated_count}
        """
        if not year_month:
            raise ValueError("请指定工资月份")

        with DBConnection() as conn:
            cursor = conn.cursor()

            # 获取有效工资档案
            archive_sql = """
                SELECT sp.UserID, sp.BaseSalary, sp.PostSalary, sp.Subsidy,
                       sp.Insurance, sp.HousingFund
                FROM SalaryProfile sp
                WHERE sp.Status = N'有效'
            """
            archive_params = []

            if user_ids:
                placeholders = ','.join(['?'] * len(user_ids))
                archive_sql += f" AND sp.UserID IN ({placeholders})"
                archive_params = list(user_ids)

            cursor.execute(archive_sql, archive_params)
            profiles = cursor.fetchall()

            if not profiles:
                return {'success': False, 'message': '没有可用的工资档案', 'generated_count': 0}

            generated = 0
            skipped = 0

            for profile in profiles:
                # 检查是否已存在
                cursor.execute("""
                    SELECT COUNT(*) FROM SalaryRecord
                    WHERE UserID = ? AND YearMonth = ?
                """, (profile.UserID, year_month))

                if cursor.fetchone()[0] > 0:
                    skipped += 1
                    continue

                # 计算应发和实发
                base_salary = float(profile.BaseSalary)
                post_salary = float(profile.PostSalary)
                subsidy = float(profile.Subsidy)
                insurance = float(profile.Insurance)
                housing_fund = float(profile.HousingFund)

                gross_pay = base_salary + post_salary + subsidy  # 无变动项时的应发
                total_deduction = insurance + housing_fund
                net_pay = gross_pay - total_deduction

                cursor.execute("""
                    INSERT INTO SalaryRecord (
                        UserID, YearMonth,
                        BaseSalary, PostSalary, Subsidy,
                        OvertimePay, Bonus, OtherIncome, GrossPay,
                        Insurance, HousingFund, Tax, Deduction, TotalDeduction, NetPay,
                        WorkDays, ActualDays, Status
                    ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?, 0, 0, ?, 0, 0, N'待审核')
                """, (
                    profile.UserID, year_month,
                    base_salary, post_salary, subsidy,
                    gross_pay,
                    insurance, housing_fund,
                    net_pay
                ))
                generated += 1

            conn.commit()

        msg = f'成功生成 {generated} 条工资记录'
        if skipped > 0:
            msg += f'，跳过 {skipped} 条（已存在）'

        return {'success': True, 'message': msg, 'generated_count': generated}

    def update_salary_record(self, record_id, data):
        """更新工资单各项（变动项：加班费、奖金、其他收入、扣款、个税等）"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            # 先获取当前记录，校验状态
            cursor.execute("SELECT Status FROM SalaryRecord WHERE RecordID = ?", (record_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("工资记录不存在")
            if row.Status != '待审核':
                raise ValueError("只有待审核状态的工资单可以编辑")

            # 读取所有字段值
            base_salary = float(data.get('base_salary', 0))
            post_salary = float(data.get('post_salary', 0))
            subsidy = float(data.get('subsidy', 0))
            overtime_pay = float(data.get('overtime_pay', 0))
            bonus = float(data.get('bonus', 0))
            other_income = float(data.get('other_income', 0))
            insurance = float(data.get('insurance', 0))
            housing_fund = float(data.get('housing_fund', 0))
            tax = float(data.get('tax', 0))
            deduction = float(data.get('deduction', 0))
            work_days = int(data.get('work_days', 0))
            actual_days = int(data.get('actual_days', 0))
            description = data.get('description', '')

            # 自动计算合计
            gross_pay = base_salary + post_salary + subsidy + overtime_pay + bonus + other_income
            total_deduction = insurance + housing_fund + tax + deduction
            net_pay = gross_pay - total_deduction

            cursor.execute("""
                UPDATE SalaryRecord SET
                    BaseSalary = ?, PostSalary = ?, Subsidy = ?,
                    OvertimePay = ?, Bonus = ?, OtherIncome = ?,
                    GrossPay = ?,
                    Insurance = ?, HousingFund = ?, Tax = ?, Deduction = ?,
                    TotalDeduction = ?, NetPay = ?,
                    WorkDays = ?, ActualDays = ?,
                    Description = ?, UpdateTime = GETDATE()
                WHERE RecordID = ?
            """, (
                base_salary, post_salary, subsidy,
                overtime_pay, bonus, other_income,
                gross_pay,
                insurance, housing_fund, tax, deduction,
                total_deduction, net_pay,
                work_days, actual_days,
                description, record_id
            ))

            conn.commit()

        return {
            'success': True,
            'message': '更新成功',
            'gross_pay': gross_pay,
            'total_deduction': total_deduction,
            'net_pay': net_pay
        }

    def delete_salary_record(self, record_id):
        """删除工资记录（仅允许删除待审核状态）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Status FROM SalaryRecord WHERE RecordID = ?", (record_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("工资记录不存在")
            if row.Status != '待审核':
                raise ValueError("只有待审核状态的工资单可以删除")

            cursor.execute("DELETE FROM SalaryRecord WHERE RecordID = ?", (record_id,))
            conn.commit()
            return True

    # ========== 审核与发放 ==========

    def approve_salary(self, record_id, approved_by):
        """审核工资单"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE SalaryRecord
                SET Status = N'已审核', ApprovedBy = ?, ApprovedTime = GETDATE(), UpdateTime = GETDATE()
                WHERE RecordID = ? AND Status = N'待审核'
            """, (approved_by, record_id))

            if cursor.rowcount == 0:
                raise ValueError("审核失败：记录不存在或状态不是待审核")

            conn.commit()
            return True

    def batch_approve_salary(self, record_ids, approved_by):
        """批量审核工资单"""
        if not record_ids:
            raise ValueError("请选择要审核的工资单")

        with DBConnection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(record_ids))
            cursor.execute(f"""
                UPDATE SalaryRecord
                SET Status = N'已审核', ApprovedBy = ?, ApprovedTime = GETDATE(), UpdateTime = GETDATE()
                WHERE RecordID IN ({placeholders}) AND Status = N'待审核'
            """, [approved_by] + list(record_ids))

            affected = cursor.rowcount
            conn.commit()

        return {'success': True, 'message': f'成功审核 {affected} 条工资单', 'affected': affected}

    def pay_salary(self, record_id, created_by, payment_method='转账', transaction_date=None):
        """
        发放工资 — 联动财务模块

        流程：
        1. 验证工资单状态为"已审核"
        2. 创建应付账款（费用类型=工资）
        3. 付款核销（Payable → PaymentRecord → CashFlow）
        4. 更新工资单状态为"已发放"，关联 PayableID
        """
        record = self.get_salary_record_by_id(record_id)
        if not record:
            raise ValueError("工资记录不存在")
        if record.Status != '已审核':
            raise ValueError("只有已审核的工资单才能发放")

        net_pay = float(record.NetPay)
        if net_pay <= 0:
            raise ValueError("实发金额必须大于0")

        if not transaction_date:
            transaction_date = date.today().strftime('%Y-%m-%d')

        # 获取"工资"费用类型的 DictID
        from app.services.dict_service import DictService
        expense_items = DictService.get_expense_items('expense_item_expend')
        salary_type_id = None
        for item in expense_items:
            if item['dict_name'] == '工资':
                salary_type_id = item['dict_id']
                break
        if not salary_type_id:
            raise ValueError("字典中未找到'工资'费用类型，请先执行迁移脚本")

        try:
            with DBConnection() as conn:
                cursor = conn.cursor()

                # 1. 创建应付账款
                cursor.execute("""
                    INSERT INTO Payable (VendorName, ExpenseTypeID, Amount, DueDate,
                                         Status, PaidAmount, RemainingAmount, Description,
                                         CustomerType, CustomerID)
                    OUTPUT INSERTED.PayableID
                    VALUES (?, ?, ?, ?, N'未付款', 0, ?, ?, N'Internal', ?)
                """, (
                    record.RealName,  # VendorName 用员工姓名
                    salary_type_id,
                    net_pay,
                    transaction_date,
                    net_pay,
                    f'{record.YearMonth}月工资 — {record.RealName}',
                    record.UserID
                ))
                payable_row = cursor.fetchone()
                payable_id = payable_row[0] if payable_row else None

                # 2. 创建付款记录
                cursor.execute("""
                    INSERT INTO PaymentRecord (
                        PayableID, VendorName, Amount, PaymentMethod,
                        TransactionDate, Description, CreatedBy, CustomerType
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, N'Internal')
                """, (
                    payable_id,
                    record.RealName,
                    net_pay,
                    payment_method,
                    transaction_date,
                    f'{record.YearMonth}月工资发放 — {record.RealName}',
                    created_by
                ))
                cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                payment_id = cursor.fetchone()[0]

                # 3. 更新应付状态为已付款
                cursor.execute("""
                    UPDATE Payable
                    SET PaidAmount = ?, RemainingAmount = 0, Status = N'已付款', UpdateTime = GETDATE()
                    WHERE PayableID = ?
                """, (net_pay, payable_id))

                # 4. 创建现金流水（支出）
                cursor.execute("""
                    INSERT INTO CashFlow (
                        Amount, Direction, ExpenseTypeID, Description,
                        TransactionDate, ReferenceID, ReferenceType, CreatedBy
                    ) VALUES (?, N'支出', ?, ?, ?, ?, N'salary_payment', ?)
                """, (
                    net_pay,
                    salary_type_id,
                    f'{record.YearMonth}月工资发放 — {record.RealName}',
                    transaction_date,
                    payment_id,
                    created_by
                ))

                # 5. 更新工资单状态
                cursor.execute("""
                    UPDATE SalaryRecord
                    SET Status = N'已发放', PayableID = ?, UpdateTime = GETDATE()
                    WHERE RecordID = ?
                """, (payable_id, record_id))

                conn.commit()

            return {
                'success': True,
                'message': f'工资发放成功，实发 ¥{net_pay:.2f}',
                'payable_id': payable_id
            }

        except Exception as e:
            logger.error(f'工资发放失败: {e}')
            raise

    # ========== 工资条查看（员工自助） ==========

    def get_my_salary_records(self, user_id, page=1, per_page=12):
        """获取某员工的工资条列表"""
        with DBConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM SalaryRecord WHERE UserID = ?
            """, (user_id,))
            total_count = cursor.fetchone()[0]

            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT RecordID, YearMonth, BaseSalary, PostSalary, Subsidy,
                       OvertimePay, Bonus, OtherIncome, GrossPay,
                       Insurance, HousingFund, Tax, Deduction,
                       TotalDeduction, NetPay,
                       WorkDays, ActualDays, Status, Description, CreateTime
                FROM SalaryRecord
                WHERE UserID = ?
                ORDER BY YearMonth DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (user_id, offset, per_page))
            rows = cursor.fetchall()

            result_list = []
            for row in rows:
                result_list.append({
                    'record_id': row.RecordID,
                    'year_month': row.YearMonth or '',
                    'base_salary': float(row.BaseSalary),
                    'post_salary': float(row.PostSalary),
                    'subsidy': float(row.Subsidy),
                    'overtime_pay': float(row.OvertimePay),
                    'bonus': float(row.Bonus),
                    'other_income': float(row.OtherIncome),
                    'gross_pay': float(row.GrossPay),
                    'insurance': float(row.Insurance),
                    'housing_fund': float(row.HousingFund),
                    'tax': float(row.Tax),
                    'deduction': float(row.Deduction),
                    'total_deduction': float(row.TotalDeduction),
                    'net_pay': float(row.NetPay),
                    'work_days': row.WorkDays or 0,
                    'actual_days': row.ActualDays or 0,
                    'status': row.Status,
                    'description': row.Description or '',
                    'create_time': format_datetime(row.CreateTime),
                })

            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

            return {
                'items': result_list,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page
            }

    # ========== 辅助方法 ==========

    def get_users_without_profile(self):
        """获取没有工资档案的员工列表（用于创建档案时选择）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.UserID, u.RealName, u.Username, u.Phone
                FROM [User] u
                WHERE u.IsActive = 1
                  AND u.UserID NOT IN (
                      SELECT UserID FROM SalaryProfile WHERE Status = N'有效'
                  )
                ORDER BY u.RealName
            """)
            rows = cursor.fetchall()
            return [{
                'user_id': r.UserID,
                'real_name': r.RealName or '',
                'username': r.Username or '',
                'phone': r.Phone or ''
            } for r in rows]

    def get_monthly_summary(self, year_month):
        """获取某月工资汇总统计"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) AS TotalCount,
                    ISNULL(SUM(GrossPay), 0) AS TotalGross,
                    ISNULL(SUM(NetPay), 0) AS TotalNet,
                    ISNULL(SUM(TotalDeduction), 0) AS TotalDeduction,
                    SUM(CASE WHEN Status = N'待审核' THEN 1 ELSE 0 END) AS PendingCount,
                    SUM(CASE WHEN Status = N'已审核' THEN 1 ELSE 0 END) AS ApprovedCount,
                    SUM(CASE WHEN Status = N'已发放' THEN 1 ELSE 0 END) AS PaidCount
                FROM SalaryRecord
                WHERE YearMonth = ?
            """, (year_month,))
            row = cursor.fetchone()

            if row and row.TotalCount > 0:
                return {
                    'total_count': row.TotalCount,
                    'total_gross': float(row.TotalGross),
                    'total_net': float(row.TotalNet),
                    'total_deduction': float(row.TotalDeduction),
                    'pending_count': row.PendingCount,
                    'approved_count': row.ApprovedCount,
                    'paid_count': row.PaidCount
                }
            return None

    def get_available_months(self):
        """获取已有工资记录的月份列表（用于筛选）"""
        with DBConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT YearMonth FROM SalaryRecord ORDER BY YearMonth DESC
            """)
            rows = cursor.fetchall()
            return [r.YearMonth for r in rows]
