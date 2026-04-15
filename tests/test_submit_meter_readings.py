# -*- coding: utf-8 -*-
"""
submit_meter_readings 单元测试
==============================
覆盖以下场景：
1. 正常电表抄表（已绑定合同，读数合理）
2. 未绑定合同的表 → 应返回明确错误提示（非 SQL 515 错误）
3. 当前读数 < 上次读数 → 校验失败
4. 空数据提交
5. 水表抄表正常流程
6. 非法日期格式 → 回退到当前日期
7. 批量部分失败（第2个未绑定）→ 立即返回失败
8. 用量计算正确性验证
9. ContractID 字段确实被传入 INSERT（回归测试）

运行方式:
    cd /d d:\\BaiduSyncdisk\\HF_metalmarket
    python -m pytest tests/test_submit_meter_readings.py -v

Mock 策略:
    直接 patch pyodbc.connect —— 所有数据库连接的最终源头，
    这样无论代码从哪一层导入 DBConnection 都会被拦截。
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _make_contract_row(unit_price=1.2, contract_id=42):
    """构造合同关联表的 fetchone 返回值"""
    r = MagicMock()
    r.UnitPrice = unit_price
    r.ContractID = contract_id
    return r


def _make_meter_row(meter_number='EM001', last_reading=100,
                    multiplier=1, contract_id=None,
                    merchant_name='', merchant_id=None):
    """模拟 WaterMeter/ElectricityMeter.get_by_id 的 SELECT 返回行"""
    r = MagicMock()
    r.MeterNumber = meter_number
    r.MeterType = 'electricity'
    r.InstallationLocation = ''
    r.MeterMultiplier = multiplier
    r.InstallationDate = None
    r.InitReading = last_reading
    r.Status = 1
    r.CreateTime = None
    r.UpdateTime = None
    r.ContractID = contract_id
    r.MerchantName = merchant_name
    r.MerchantID = merchant_id
    return r


class TestSubmitMeterReadings(unittest.TestCase):
    """
    submit_meter_readings 核心逻辑单元测试
    
    Mock 层级: pyodbc.connect → 覆盖全栈所有数据库调用
    """

    @classmethod
    def setUpClass(cls):
        from app import create_app
        from config import DevelopmentConfig
        cls.app = create_app(DevelopmentConfig)
        cls.app_ctx = cls.app.app_context()
        cls.app_ctx.push()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'app_ctx'):
            cls.app_ctx.pop()

    def _build_state(self):
        """
        构建 mock 数据库状态。
        
        返回 state dict，测试方法通过配置它来控制 mock 行为：
          .mock_conn       连接对象
          .mock_cursor     游标对象  
          .inserts         [(sql_frag, params)] 收集的 INSERT 调用
          .id_seq          [n] SCOPE_IDENTITY 自增序列起始值
          .contract_map    {'water'|'electricity': (price, cid)} 合同绑定
          .meter_rows      {meter_id: row} 表数据
        """
        s = {
            'conn': MagicMock(),
            'cursor': MagicMock(),
            'inserts': [],
            'id_seq': [100],
            'contract_map': {},
            'meter_rows': {},
            'exec_log': [],  # 调试：所有 execute 调用记录
        }

        conn = s['conn']
        cur = s['cursor']

        # ★ 关键：conn.cursor() 直接返回游标对象
        # 因为代码中使用方式是: cursor = conn.cursor() (无 with)
        # 不是: with conn.cursor() as cursor:
        conn.cursor.return_value = cur
        conn.commit = MagicMock()
        conn.rollback = MagicMock()

        # ★ 核心：智能 execute 拦截器

        def smart_exec(sql, params=None):
            su = (sql or '').upper().strip()
            s['exec_log'].append((su[:100], params))

            # ① 自增 ID
            if 'SCOPE_IDENTITY' in su:
                rid = s['id_seq'][0]
                s['id_seq'][0] += 1
                cur.fetchone.return_value = [rid]

            # ② UtilityReading INSERT → 记录参数供断言
            elif 'INSERT INTO UTILITYREADING' in su and params is not None:
                s['inserts'].append((su, list(params)))  # 保存完整 upper SQL

            # ③ ContractWaterMeter 查询（FROM 子句中的主表）
            elif ('FROM CONTRACTWATERMETER' in su):
                b = s['contract_map'].get('water')
                cur.fetchone.return_value = _make_contract_row(*b) if b else None

            # ④ ContractElectricityMeter 查询（FROM 子句中的主表）
            elif ('FROM CONTRACTELECTRICITYMETER' in su):
                b = s['contract_map'].get('electricity')
                cur.fetchone.return_value = _make_contract_row(*b) if b else None

            # ⑤ WaterMeter / ElectricityMeter 的 get_by_id SELECT
            #     注意：该查询包含 LEFT JOIN ContractXxxMeter，
            #           所以必须放在 Contract 查询匹配之后！
            elif (('FROM WATERMETER' in su or 'FROM ELECTRICITYMETER' in su)
                  and 'WHERE' in su):
                mid = params[0] if params else None
                row = s['meter_rows'].get(mid)
                cur.fetchone.return_value = row if row else None

            # ⑥ 默认：无结果
            else:
                cur.fetchone.return_value = None
                cur.fetchall.return_value = []

        cur.execute = smart_exec

        # ★★★ 关键：直接 patch utils.database.get_connection 返回 mock 连接 ★★★
        gc_call_count = [0]
        
        def _mock_get_conn():
            gc_call_count[0] += 1
            return conn
        
        s['_gc_patch'] = patch('utils.database.get_connection',
                                side_effect=_mock_get_conn)
        s['_gc_patch'].start()
        s['gc_call_count'] = gc_call_count

        # 延迟导入服务类（此时 get_connection 已被 mock）
        from app.services.utility_service import UtilityService
        s['service'] = UtilityService()

        return s

    @staticmethod
    def _cleanup(s):
        if '_gc_patch' in s:
            s['_gc_patch'].stop()

    # ════════════════════════════════════════════
    # 测试用例
    # ════════════════════════════════════════════

    def test_01_normal_electricity_submit_success(self):
        """电表已绑定合同，读数合理 → 抄表成功"""
        s = self._build_state()
        try:
            s['contract_map']['electricity'] = (2.0, 5)
            s['meter_rows'][1] = _make_meter_row('EM001', 100)

            r = s['service'].submit_meter_readings(
                'electricity',
                [{'meter_id': 1, 'current_reading': 150}],
                reading_date='2026-04-13')

            self.assertTrue(r['success'], f"期望成功: {r.get('message')}")
            self.assertIn('成功提交', r.get('message', ''))
        finally:
            self._cleanup(s)

    def test_02_unbound_electricity_returns_clear_error(self):
        """
        ★ 核心回归测试 ★
        
        电表未绑定合同 → 必须返回"尚未绑定合同"业务错误，
        不能是 SQL Server "Cannot insert NULL into column ContractID" 异常。
        """
        s = self._build_state()
        try:
            # 有表数据但无合同绑定 → contract_map 不设 electricity
            s['meter_rows'][999] = _make_meter_row('UNBOUND_EM', 50)

            r = s['service'].submit_meter_readings(
                'electricity',
                [{'meter_id': 999, 'current_reading': 200}])

            self.assertFalse(r['success'])
            msg = r.get('message', '')
            self.assertIn(
                '尚未绑定合同', msg,
                f"期望'尚未绑定合同'提示, 实际: {msg}")
        finally:
            self._cleanup(s)

    def test_03_unbound_water_returns_clear_error(self):
        """水表未绑定合同同样需要保护"""
        s = self._build_state()
        try:
            s['meter_rows'][888] = _make_meter_row('UNBOUND_WM', 200)
            # 不设 contract_map['water']

            r = s['service'].submit_meter_readings(
                'water',
                [{'meter_id': 888, 'current_reading': 300}])

            self.assertFalse(r['success'])
            self.assertIn('尚未绑定合同', r.get('message', ''))
        finally:
            self._cleanup(s)

    def test_04_current_less_than_last_fails(self):
        """当前 < 上次 → 校验失败"""
        s = self._build_state()
        try:
            s['contract_map']['electricity'] = (1.5, 10)
            s['meter_rows'][1] = _make_meter_row('EM001', 100)

            r = s['service'].submit_meter_readings(
                'electricity',
                [{'meter_id': 1, 'current_reading': 80}])

            self.assertFalse(r['success'])
            self.assertIn('不能小于上次读数', r.get('message', ''))
        finally:
            self._cleanup(s)

    def test_05_empty_readings_returns_success(self):
        """空数据提交 → 成功（0 条记录被处理）"""
        s = self._build_state()
        try:
            r = s['service'].submit_meter_readings('electricity', [])
            # 当前实现：空列表时 for 循环不执行，直接 commit + return success
            self.assertTrue(r['success'])
            self.assertIn('成功提交', r.get('message', ''))
        finally:
            self._cleanup(s)

    def test_06_water_normal_submit_success(self):
        """水表正常抄表"""
        s = self._build_state()
        try:
            s['contract_map']['water'] = (3.5, 20)
            s['meter_rows'][10] = _make_meter_row('WM005', 400)

            r = s['service'].submit_meter_readings(
                'water',
                [{'meter_id': 10, 'current_reading': 500}],
                reading_date='2026-04-13')

            self.assertTrue(r['success'], f"水表应成功: {r.get('message')}")
        finally:
            self._cleanup(s)

    def test_07_invalid_date_format_falls_back(self):
        """非法日期格式 → 回退到今天，不崩溃"""
        s = self._build_state()
        try:
            s['contract_map']['electricity'] = (1.0, 1)
            s['meter_rows'][1] = _make_meter_row(last_reading=100)

            r = s['service'].submit_meter_readings(
                'electricity',
                [{'meter_id': 1, 'current_reading': 200}],
                reading_date='not-a-date')

            self.assertTrue(r['success'],
                            f"非法日期不应导致失败: {r.get('message')}")
        finally:
            self._cleanup(s)

    def test_08_batch_second_unbound_stops(self):
        """
        批量第1个已绑定、第2个未绑定 → 第2个处报错
        """
        s = self._build_state()
        try:
            s['meter_rows'][1] = _make_meter_row('EM001', 100)
            s['meter_rows'][2] = _make_meter_row('EM002', 200)

            # 让合同查询在第2次调用时返回 None
            call_n = [0]
            orig_exec = s['cursor'].execute

            def seq_exec(sql, params=None):
                su = (sql or '').upper().strip()
                if 'SCOPE_IDENTITY' in su:
                    rid = s['id_seq'][0]; s['id_seq'][0] += 1
                    s['cursor'].fetchone.return_value = [rid]
                elif 'CONTRACTELECTRICITYMETER' in su and 'SELECT' in su:
                    call_n[0] += 1
                    if call_n[0] == 1:
                        s['cursor'].fetchone.return_value = \
                            _make_contract_row(1.0, 1)
                    else:
                        s['cursor'].fetchone.return_value = None
                elif (('FROM ELECTRICITYMETER' in su) and 'WHERE' in su
                      and 'CONTRACT' not in su):
                    mid = params[0] if params else None
                    row = s['meter_rows'].get(mid)
                    s['cursor'].fetchone.return_value = row if row else None
                else:
                    s['cursor'].fetchone.return_value = None
                    s['cursor'].fetchall.return_value = []

            s['cursor'].execute = seq_exec

            r = s['service'].submit_meter_readings(
                'electricity',
                [
                    {'meter_id': 1, 'current_reading': 200},
                    {'meter_id': 2, 'current_reading': 300},
                ])

            self.assertFalse(r['success'])
            self.assertIn('尚未绑定合同', r.get('message', ''))
        finally:
            self._cleanup(s)

    def test_09_usage_calculation_correctness(self):
        """
        用量公式验证:
          usage = (current - last) * multiplier
          amount = usage * unit_price
        
        例: last=100, current=105, multiplier=10, price=2.0
            → usage=50, amount=100
        """
        s = self._build_state()
        try:
            s['contract_map']['electricity'] = (2.0, 1)
            s['meter_rows'][1] = _make_meter_row('EM001', 100, 10)

            r = s['service'].submit_meter_readings(
                'electricity',
                [{'meter_id': 1, 'current_reading': 105}])

            self.assertTrue(r['success'])
            self.assertEqual(len(s['inserts']), 1)
            _, p = s['inserts'][0]
            self.assertAlmostEqual(p[4], 50.0, places=2)   # Usage
            self.assertAlmostEqual(p[6], 100.0, places=2)  # TotalAmount
        finally:
            self._cleanup(s)

    def test_10_contract_id_not_null_in_insert(self):
        """
        ★ 核心回归测试 ★
        
        确保 INSERT INTO UtilityReading 包含 ContractID 且值不为 NULL。
        
        原始 bug: f-string 注入修复时漏掉 ContractID 字段
                 → SQL Error 515 Cannot insert NULL
        """
        s = self._build_state()
        try:
            s['contract_map']['electricity'] = (1.5, 99)
            s['meter_rows'][1] = _make_meter_row('EM001', 100)

            s['service'].submit_meter_readings(
                'electricity',
                [{'meter_id': 1, 'current_reading': 200}])

            self.assertEqual(len(s['inserts']), 1)
            sql_frag, params = s['inserts'][0]

            self.assertIn('CONTRACTID', sql_frag)
            self.assertIsNotNone(params[-1],
                                 "ContractID=NULL 会触发 SQL Error 515")
            self.assertEqual(params[-1], 99)
        finally:
            self._cleanup(s)


# ────────────────────────────────────────────────
# 可选集成测试（需真实数据库）
# ────────────────────────────────────────────────

class TestIntegrationWithRealDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._on = os.environ.get('RUN_INTEGRATION_TESTS', '') == '1'
        if cls._on:
            from app import create_app
            from config import DevelopmentConfig
            cls.app = create_app(DevelopmentConfig)
            cls.app_ctx = cls.app.app_context()
            cls.app_ctx.push()

    @classmethod
    def tearDownClass(cls):
        if cls._on and hasattr(cls, 'app_ctx'):
            cls.app_ctx.pop()

    def test_flag_off_skips(self):
        if not self._on:
            self.skipTest("设置 RUN_INTEGRATION_TESTS=1 启用")

    def test_real_empty_submission(self):
        if not self._on:
            self.skipTest("设置 RUN_INTEGRATION_TESTS=1 启用")
        from app.services.utility_service import UtilityService
        self.assertFalse(UtilityService().submit_meter_readings(
            'electricity', [])['success'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
