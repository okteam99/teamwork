"""v8.299:测试基建成本显性化 + 退役类改造纪律 + 并行派发第三问。

来源:matrixpower BL-038/BL-039 两个 feature 全链路的规范增补提案(已是条文形态)。
逐条过了收录判据(v8.285「与模型默认行为的距离」),七条全部落在**逆默认**或**不可知**:

  A1 机械收敛与语义变更分两步 —— 模型默认**一起改**(都要动这些文件,顺手)
  A2 退役类按口径分张台账 —— 模型默认**算一个总数**,数字接近就以为核过了
  A3 测试基建税必须记下来 —— 模型默认要么顺手改(范围失控)要么无视(税永远隐形)
  B1 退役 BL 的 current_state 增记测试痕迹 —— 模型不可知的经验:成本主体在测试改写
  C1 派发第三问「验证目标有重叠吗」—— 模型默认按产物切分就认为正交了
  C2 同编译单元并行的三项声明 —— 模型不可知:独立构建目录挡不住源目录 lock
  C3 三条硬约束的中断安全职责 —— 零成本(不加规则 · 只补 why,防它被当官僚主义砍掉)
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class TestRetirementLedgerByPopulation(unittest.TestCase):
    """A2:不同口径的总数**不可互相印证** —— 强行对账会产出虚假的「数字吻合」。

    实证:TECH 与 TC 各算出「35 处/7 文件」并都自称与 PRD 吻合,实为两个互斥 population;
    真实是 25/6(调用面)、71/6(构造面)、18/5(约束面),第三张是评审才发现的 —— 对应 18 个必红测试。
    """

    def test_tech_template_has_three_populations(self):
        t = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
        for pop in ("调用面", "构造面", "约束面"):
            self.assertIn(pop, t, f"退役台账缺口径:{pop}")

    def test_total_is_explicitly_not_a_gate(self):
        """总数当门 = 把「口径不同」的错误伪装成「核过了」。"""
        t = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
        self.assertIn("总数不作验收门", t)
        self.assertIn("不可互相印证", t, "缺这半句 → 下次还会拿两个 population 对账")

    def test_blueprint_hard_rule_carries_it(self):
        """模板只在起草时被读;硬规则才在评审时被核。"""
        t = (ROOT / "stages" / "blueprint-stage.md").read_text(encoding="utf-8")
        self.assertIn("不可互相印证", t)

    def test_blueprint_rule_numbers_still_unique(self):
        """插规则要顺延编号 —— 编号重复会让「见规则 N」的互指失效(v8.293 踩过)。"""
        t = (ROOT / "stages" / "blueprint-stage.md").read_text(encoding="utf-8")
        nums = re.findall(r"^(\d+)\. ", t, re.M)
        self.assertEqual(len(nums), len(set(nums)), f"硬规则编号重复:{nums}")


class TestMechanicalThenSemantic(unittest.TestCase):
    """A1:合并成一个改-跑-修循环后,每次失败都要先分辨「收敛错了还是语义错了」。"""

    def test_step_zero_is_prescribed_with_criterion(self):
        t = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
        self.assertIn("语义零变更", t, "缺「步骤 0 纯机械」= 会被合并回去")
        self.assertIn("收敛错了还是语义错了", t, "缺可归因性判据 → 规则退化成拍脑袋的阈值")


class TestInfraTaxMustBeRecorded(unittest.TestCase):
    """A3:串行约束若来自测试基建而非被测逻辑 —— 不在本 feature 顺手改,但必须记下来。"""

    def test_both_halves_present(self):
        t = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
        self.assertIn("不在本 feature 内顺手改", t, "缺范围纪律 → 改造面失控")
        self.assertIn("必须记下来", t, "缺留痕 → 每个后续 feature 都在付这个税且无人知")


class TestRetirementCostInPlanning(unittest.TestCase):
    """B1:规划期只按「新增能力」估工作量,会系统性低估 3~5 倍。"""

    def test_planning_contract_requires_test_footprint(self):
        t = (ROOT / "docs" / "feature-planning.md").read_text(encoding="utf-8")
        self.assertIn("测试痕迹", t)
        self.assertIn("一次 grep 即得", t, "缺「成本极低」说明 → 会被当成额外负担跳过")

    def test_workstream_field_carries_it(self):
        t = (ROOT / "templates" / "workstream.md").read_text(encoding="utf-8")
        self.assertIn("测试痕迹", t, "WS 模板未要求填 → 规划期还是不会估")


class TestDispatchThirdQuestion(unittest.TestCase):
    """C1:按产物归属切分容易让**验证目标**跨线 —— 切分看着正交,验证目标却不正交。"""

    def test_skill_parallel_section_has_third_question(self):
        t = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("验证目标", t)
        self.assertIn("不做该验证", t, "缺「其余路显式声明不做」→ 重叠只被发现不被消除")


class TestSameCompilationUnitDispatch(unittest.TestCase):
    """C2:三项声明缺任一项都会产出无人认领的收尾项。"""

    def test_three_declarations_present(self):
        t = (ROOT / "agents" / "README.md").read_text(encoding="utf-8")
        self.assertIn("构建隔离", t)
        self.assertIn("验证边界", t)
        self.assertIn("lint 归属", t)

    def test_build_dir_isolation_is_not_enough(self):
        """独立构建目录挡不住源目录 lock —— 不写明就会以为设了 CARGO_TARGET_DIR 就万事大吉。"""
        t = (ROOT / "agents" / "README.md").read_text(encoding="utf-8")
        self.assertIn("不足以消除争抢", t)

    def test_unclaimed_followup_is_named_as_the_failure_mode(self):
        t = (ROOT / "agents" / "README.md").read_text(encoding="utf-8")
        self.assertIn("无人认领", t, "不点名失败形态 → 三条声明会被当成可选建议")


class TestInterruptSafetyIsDesignIntent(unittest.TestCase):
    """C3:三条硬约束的第二重职责 —— 中断安全。

    零成本条款:不新增规则,只给已有规则补 why。补 why 的价值在于**防它被当成官僚主义砍掉**
    (本 session 砍了很多「手段规定」,而这三条是有硬收益的,得让人看得见收益)。
    """

    def test_two_safe_states_named(self):
        t = (ROOT / "agents" / "README.md").read_text(encoding="utf-8")
        self.assertIn("已落盘且可编译", t)
        self.assertIn("未落盘", t)
        self.assertIn("半提交", t, "未点名要避免的坏状态")

    def test_stated_as_consequence_not_luck(self):
        t = (ROOT / "agents" / "README.md").read_text(encoding="utf-8")
        self.assertIn("不是运气", t, "缺这句 → 读者会以为那次恢复干净是巧合,规则就失去说服力")


class TestSlimmingGateMeasuresValueNotVolume(unittest.TestCase):
    """v8.299 的元发现:体积门首次咬人就咬错了。

    `tech.md < 250 行` 拦下的是三条**逆默认 + 带实证**的规则 —— 而逆默认正是 v8.283
    分类学里最高价值的那类。体积门度量错了东西:300 行全是逆默认规则的模板,
    比 200 行全是填充示例的更瘦。已换成价值门(每条硬规则必须带 why)。
    """

    def test_no_raw_line_cap_on_tech_template(self):
        src = (ROOT / "tools" / "tests" / "test_template_slimming_v8283.py").read_text(encoding="utf-8")
        self.assertNotIn("tech.md 应已瘦身到 250 行内", src, "体积门复活")

    def test_value_gate_in_place(self):
        t = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(t.count("why"), 3, "硬规则不带 why = 纯注意力税")

    def test_content_side_gates_still_guard_bloat(self):
        """去掉体积门不等于放任膨胀 —— 内容型门仍在(教学示例/手段规定不得回归)。"""
        src = (ROOT / "tools" / "tests" / "test_template_slimming_v8283.py").read_text(encoding="utf-8")
        self.assertIn("test_teaching_examples_trimmed", src)
        self.assertIn("test_tdd_not_prescribed", src)




class TestRunTestsSharding(unittest.TestCase):
    """`tools/run_tests.py` 的装箱(R-SP-1:脚本必须有 test · happy / edge / failure)。

    实测:按文件大小近似装箱 → 27.5s(分片间最大差 17s);写回实测耗时后 → **17.3s**(差 1.1s)。
    所以缓存不是锦上添花 —— 首跑必然不均,自学是它能用的前提。
    """

    def _mod(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "tw_run_tests", ROOT / "tools" / "run_tests.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    class _F:
        def __init__(self, name, size=1000):
            self.name = name
            self._s = size

        def stat(self):
            return type("S", (), {"st_size": self._s})()

    def test_happy_balances_by_measured_weight(self):
        m = self._mod()
        files = [self._F(f"t{i}.py") for i in range(6)]
        w = {"t0.py": 10, "t1.py": 9, "t2.py": 2, "t3.py": 2, "t4.py": 1, "t5.py": 1}
        b = m.shard(files, w, 2)
        loads = [sum(w[f.name] for f in bucket) for bucket in b]
        self.assertEqual(sum(loads), 25)
        self.assertLessEqual(max(loads) - min(loads), 3, f"装箱不均:{loads}")

    def test_edge_falls_back_to_size_when_no_weights(self):
        """首跑无缓存 → 用字节数近似(不均但能跑 · 跑完自学)。"""
        m = self._mod()
        files = [self._F("big.py", 90000), self._F("small.py", 1000)]
        b = [x for x in m.shard(files, {}, 2) if x]
        self.assertEqual(len(b), 2, "无权重时应仍能分片")
        self.assertEqual(sorted(f.name for bucket in b for f in bucket),
                         ["big.py", "small.py"], "不得丢文件")

    def test_edge_more_shards_than_files(self):
        m = self._mod()
        b = m.shard([self._F("only.py")], {}, 8)
        self.assertEqual(sum(len(x) for x in b), 1, "文件不得重复或丢失")
        self.assertEqual(len([x for x in b if x]), 1, "空片由调用方跳过")

    def test_failure_zero_or_negative_shards_does_not_crash(self):
        m = self._mod()
        files = [self._F(f"t{i}.py") for i in range(3)]
        for n in (0, -1):
            b = m.shard(files, {}, n)
            self.assertEqual(sum(len(x) for x in b), 3, f"n={n} 时丢了文件")

    def test_runner_is_python_not_bash(self):
        """R-SP-1:业务脚本一律 python3 —— 初版写成了 .sh,自己违反了正在编辑的规则。"""
        self.assertTrue((ROOT / "tools" / "run_tests.py").exists())
        self.assertFalse((ROOT / "tools" / "run-tests.sh").exists(), "bash 版应已删除")

    def test_policy_states_criterion_not_just_advice(self):
        t = (ROOT / "standards" / "scripts-policy.md").read_text(encoding="utf-8")
        self.assertIn("只优化 > 50ms", t, "缺量化触发线 → 又变成凭感觉优化")
        self.assertIn("共享 setup,不是合并断言", t, "缺手段判据 → 会去合并断言(省不到还丢定位)")
        self.assertIn("只写规范不配机器门", t, "未声明这是会衰减的手段规定")


if __name__ == "__main__":
    unittest.main(verbosity=2)
