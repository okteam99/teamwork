#!/usr/bin/env python3
"""
state.py — Teamwork Feature state.json maintenance tool.

红线：
1. 声明式接口：禁止暴露 jq path / json patch / dot-notation；每个改动语义化命名子命令。
2. cite-only output：默认返回 updated_fields + cited_fields，不返回全 state.json。
3. R3 自动满足：每次调用 = 一次原子 read-modify-write，不留中段。
4. 逃生舱有代价：raw-write 自动追加 concerns WARN「raw-write 跳过校验」。

命令清单单源 = `state.py --help`(本文件 build_parser)：
- 读:snapshot(status) / validate / raw-read
- 写:raw-write(逃生舱)/ init-feature / recover / add-concern / pause-mark /
  reset-prev / jump-to-stage / change-review-roles / set-mode / test-baseline
- 流程:各 stage 的 -start / -complete / -fix / -retry(_v8_engine 注册)+ ship-phase(_v8_ship)
- 评审:external-review(出 subagent 冷审配方)
- 汇总:audit-raw-writes / prepare-check / planning-check / ws-progress / ws-lint / stage-cost
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ─── 常量 ──────────────────────────────────────────────────────────────

LEGAL_STAGES = {
    "goal",
    "ui_design",
    "panorama_sync",   # 退役 stage · 仅为历史 state(completed_stages)兼容保留枚举
    "blueprint",
    "diagnose",
    "dev",
    "review",
    "test",
    "browser_e2e",
    "pm_acceptance",
    "ship",
    "completed",
}

GATE_NAMES = ("input_satisfied", "process_satisfied", "output_satisfied")

# ship 两段式:ship1 终点 = pushed(MR 已建 · 等用户平台合并)· 合并后 ship-finalize 清场
# (合并检测在平台侧完成 · 状态机不设 merged 值;放弃/关闭走 closed_unmerged/abandoned)
SHIP_PHASE_ENUM = {None, "archived", "pushed", "closed_unmerged"}
SHIP_SHIPPED_ENUM = {None, "archived", "pushed", "closed_unmerged", "abandoned"}
SHIP_GIT_HOSTS = {"github", "gitlab", "gitlab-self-hosted", "gitee", "bitbucket", "unknown"}
SHIP_MR_METHODS = {"cli-gh", "cli-glab", "url-fallback", "unknown-platform"}

CONCERN_SEVERITY = {"INFO", "WARN", "ERROR"}

# 各 flow_type 的 canonical 转移图（current_stage → legal_next_stages）
# 注：ui_design / browser_e2e 是可选 Stage（PMO 在 enter-stage 时按 spec 决策跳过 vs 启用）
FEATURE_FLOW: dict[str, list[str]] = {
    # goal/ui_design → dev 直边 = **lite 档**(装配形态 · 非独立 preset):blueprint 被跳过时走这条。
    # 用户拍板「lite 是不是可以被 full 装配出来」→ 是:lite 有 PRD(长在 goal 入口上)· 与 full
    # 的唯一结构差是「跳 blueprint」· 立成 preset 会多一张图 + 一次 re-init,装配旋钮零成本。
    "goal": ["ui_design", "blueprint", "dev"],
    "ui_design": ["blueprint", "dev"],   # 全景变更判级并入 ui_design 出口(panorama_sync stage 退役 · 用户拍板)
    "blueprint": ["dev"],
    "dev": ["review"],
    "review": ["test", "dev"],          # review 失败回 dev
    "test": ["browser_e2e", "pm_acceptance"],
    "browser_e2e": ["pm_acceptance"],
    "pm_acceptance": ["ship", "dev"],   # 拒绝回 dev
    "ship": ["completed"],
    "completed": [],
}

BUG_FLOW: dict[str, list[str]] = {
    "diagnose": ["dev"],                 # v8.107:根因细查 + 修复方案 · 🔴 用户确认后才进 dev(防修偏)
    "dev": ["review"],
    "review": ["test", "dev"],
    "test": ["pm_acceptance"],
    "pm_acceptance": ["ship", "dev"],
    "ship": ["completed"],
    "completed": [],
}

# Micro:最轻流程(改文案 / 改配置)· v8.250 = execute → ship(去 dev 门禁 + pm_acceptance)
# execute = 零门禁自由执行(自选 model/subagent/workflow/测试 · 无规范限制 · 只守 worktree 路径 + 准入白名单)
# 用户验收从 pm_acceptance 挪到 ship1 MR diff review。
MICRO_FLOW: dict[str, list[str]] = {
    "execute": ["ship"],
    "ship": ["completed"],
    "completed": [],
}

# Tiny:零文档但要 review/验收的档(用户拍板「tiny dev → review(单路 architect)→ pm_acceptance → ship」)
# 与 micro 的分界 = 要不要人看代码:micro 用户在 ship1 MR diff 上验收 · tiny 有独立 architect 单路 + PM 验收。
# 与 lite 的分界 = 四轴的「验证成本」轴:diff 可验(tiny · 无 test stage)vs 需跑链路(lite · 保留 test)。
# 规格载体 = dev brief 里的理解卡(无 PRD/TC)· 故 tiny 无 goal/blueprint —— 只能独立成 preset。
TINY_FLOW: dict[str, list[str]] = {
    "dev": ["review"],
    "review": ["pm_acceptance", "dev"],   # review 失败回 dev(与 full 同口径 · 只是下一跳跳过 test)
    "pm_acceptance": ["ship", "dev"],
    "ship": ["completed"],
    "completed": [],
}

# Floor:最轻的**有证据门**档(v8.343 · 用户:「理论上拆出的力度最小可以直接 dev + ship」)。
# 与 micro 的分界不是「更轻/更重」而是**拿什么换轻**:micro 拿掉证据门、准入靠白名单兜着;
# floor 保留全部测试证据门(所以能接真逻辑改动)、拿掉的是评审与独立验收口。
# 用户主权没丢 —— 验收在 ship1 的 MR diff(micro 原设计),ship 在任何组合里都减不掉。
FLOOR_FLOW: dict[str, list[str]] = {
    "dev": ["ship"],
    "ship": ["completed"],
    "completed": [],
}

# Feature Planning / 问题排查 不进状态机:由 PMO 主对话执行(详 docs/feature-planning.md)
# v8.220(用户拍板):对外 flow_type 收缩为 {Feature, Bug} —— Micro 是「同一种工作的重量档」
# 非独立工作形态(audit 实测合计仅 11%)· 降为 Feature 的 **preset**(链与角色由 preset 决定)。
FLOW_BY_TYPE = {
    "Feature": FEATURE_FLOW,          # = preset full · **也是 lite**(lite = 跳 blueprint 的装配形态)
    "Feature:micro": MICRO_FLOW,      # 原 Micro
    "Feature:tiny": TINY_FLOW,        # v8.342:零文档 + 单路 architect + PM 验收
    "Feature:floor": FLOOR_FLOW,      # v8.343:最轻有证据门档 · dev → ship
    "Bug": BUG_FLOW,
}

PUBLIC_FLOW_TYPES = ("Feature", "Bug")
# preset = **有真结构差**的档才立(判据:不立 preset 就走不通的链边)。
# - micro:跳 review/test/pm_acceptance(execute → ship)
# - tiny :无 goal/blueprint 入口(dev 起 · 跳 test)
# - lite :**不在这里** —— 它与 full 的差是「跳 blueprint」一条边,FEATURE_FLOW 加直边即可,
#         由 execution_hints.blueprint_needed 装配旋钮驱动(用户拍板「lite 是不是可以被 full 装配出来」)。
# v8.223 退旧 lite 档 · v8.293 彻底删「敏捷需求」legacy —— 它的链是 Feature 链的 needs-ui=false
# 剖面(纯冗余)· 轻量由动态 roster + clarity 承担;三份 flow-key 实现曾对它解析出不同的图
# (state.py→full / _v8_engine.py→lite · 且后者注释谎称「严格同口径」)—— 删掉根治。
# 🔴 本版把 lite 做成装配形态而非 preset,正是不重蹈「多一张图 = 多一处口径分叉」。
FEATURE_PRESETS = ("full", "medium", "lite", "tiny", "floor", "micro")
# 有独立**静态**图的档(仅作无 plan 存量 state 的回退 · 新 feature 一律由 plan 推导)。
# lite/medium 不在此列:它们的链是 FEATURE_FLOW 的子路径,回退到 FEATURE_FLOW 即可。
_STRUCTURAL_PRESETS = ("micro", "tiny", "floor")
LEGACY_FLOW_ALIASES = {"Micro": ("Feature", "micro")}


# ─── 装配维度矩阵(v8.343 · 链的单源)────────────────────────────────────
#
# 用户拍板:「把流程、环节、评审力度三个维度拆开,交给 AI 组装」。
# 澄清后的四维 + 一开关(「流程」与「环节」是同一维的两种粒度 · 合成一维):
#
#   D1 spec_depth    ∈ none / prd / prd_tech   —— 有规格风险吗?方案空间值得先写再做吗?
#   D2 evidence_gate ∈ False / True            —— 有行为面吗?有 → 必开(测试是唯一行为证据)
#   D3 verify_depth  ∈ self / test / test_e2e  —— dev 自证够吗?要独立跑链路吗?
#   D4 review        —— 逐评审点:路数 × 角色(× 模型)· 「这一路不派最可能漏什么」
#   (开关) ui        —— **事实判断不是力度**:有 UI 改动就进,与轻重无关
#
# 验收位置并进 D4:pm_acceptance 0 路 = 验收挪到 ship1 MR diff(micro 原设计)。
SPEC_DEPTHS = ("none", "prd", "prd_tech")
VERIFY_DEPTHS = ("self", "test", "test_e2e")
REVIEW_POINTS = ("goal", "blueprint", "review", "pm_acceptance")

# 🔴 **降档时留哪一路 = 看实测产出,不看直觉**(v8.346 年检实证 · 289 行台账 / 3 项目):
#   逐 stage 的真 finding 产出 external > architect —— goal 275:178 · blueprint 76:57 · review 87:53
#   (总量 1546:735 = 2.1× · external 采纳率 82.3%)。v8.341-343 初版把轻档单路配成 architect,
#   理由「异质冷审边际收益压不过协调开销」是**推的、没有数据支撑**,砍掉的恰是产出最高的一路。
#   现在单路默认 = external:它还天然满足「单路必错开模型」不变式(architect 单路得额外保证)。
#   architect 不是没价值 —— 它在**有 TECH 可对照**时最强,所以 medium/full 的 blueprint 仍可加回;
#   但「只留一路」时,留 external。
# 档 = **命名的默认元组 + 一句入场问句**。矩阵能推导链之后,「档」不再有结构特权 ——
# 加一档就是加一行(medium 就是用户在本版实现中途提的,一行落地)。
# 🔴 档是**起手点不是终点**:装配的正常产物是**维度元组**,AI 有权拧任意一维
#    (`--dims` / `revise-plan`)· 只选个档名不拧 = 退化情形,不是默认姿态。
TIER_DIMS: dict[str, dict] = {
    # 无行为面(测试无从写起)· 准入白名单兜底 —— v8.343 起 micro 的定义就是这一句,
    # 不再是「最轻的档」(最轻是 floor)。
    "micro": {"spec_depth": "none", "evidence_gate": False, "verify_depth": "self",
              "ui": False, "review": {"review": [], "pm_acceptance": []}},
    # 有行为面 · 测试能完全证明它对 · 无契约面 → 证据门开、评审全 0(验收在 MR diff)。
    "floor": {"spec_depth": "none", "evidence_gate": True, "verify_depth": "self",
              "ui": False, "review": {"review": [], "pm_acceptance": []}},
    # 测试证得了实现,但值得一双眼看 diff。
    "tiny": {"spec_depth": "none", "evidence_gate": True, "verify_depth": "self",
             "ui": False, "review": {"review": ["external"], "pm_acceptance": ["pm"]}},
    # 有规格风险(要 PRD)但方案空间小到不值得先写一份 TECH 再照着写。
    "lite": {"spec_depth": "prd", "evidence_gate": True, "verify_depth": "test",
             "ui": False, "review": {"goal": [], "review": ["external"],
                                     "pm_acceptance": ["pm"]}},
    # 方案空间值得先写 TECH,但风险还不到要两路并行冷审 —— goal/blueprint 各**单路**
    # (goal 用 fast 合并帽:PL 质疑 + 覆盖方向制并作一路 · 模型照错开)。
    "medium": {"spec_depth": "prd_tech", "evidence_gate": True, "verify_depth": "test",
               "ui": False, "review": {"goal": ["fast"], "blueprint": ["external"],
                                       "review": ["external"], "pm_acceptance": ["pm"]}},
    "full": {"spec_depth": "prd_tech", "evidence_gate": True, "verify_depth": "test",
             "ui": False, "review": {"goal": ["pl", "external"],
                                     "blueprint": ["architect", "external"],
                                     "review": ["architect", "external"],
                                     "pm_acceptance": ["pm"]}},
}

# 每档一句**可判入场问句**(判据不是「改动大小」· 是风险的种类)
TIER_ADMISSION: dict[str, str] = {
    "micro": "这改动有行为面吗?没有(文案/样式/资源/配置常量/注释)—— 测试无从写起",
    "floor": "有行为面,但测试能完全证明它对吗?能,且不动契约面 —— 验收在 ship1 MR diff",
    "tiny": "测试证得了实现,但值得一双眼看 diff 吗?值得",
    "lite": "有规格风险(会不会在做错的东西)吗?有 → 要 PRD;但方案空间小到只有一种写法 → 不写 TECH",
    "medium": "方案空间值得先写 TECH,但风险到了要两路并行冷审吗?没到 → goal/blueprint 各单路",
    "full": "契约面宽 / 影响面广 / 方案分叉多 —— 两路并行冷审的边际收益压得过开销",
}


def tier_dims(tier: str) -> dict:
    """档名 → 默认维度元组(深拷贝 · 防调用方改到常量)。"""
    import copy
    return copy.deepcopy(TIER_DIMS.get(tier or "full", TIER_DIMS["full"]))


def merge_dims(base: dict, override: Optional[dict]) -> dict:
    """档默认 + AI 自定覆盖 → 最终维度(review 逐评审点浅合并 · 其余整值覆盖)。

    custom 装配走这里:起手选档 · 拧哪维就传哪维 · 不传的沿用档默认。
    """
    import copy
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if k == "review" and isinstance(v, dict):
            out.setdefault("review", {}).update(v)
        else:
            out[k] = v
    return out


def derive_chain(dims: dict) -> list[str]:
    """维度 → 线性 stage 链(不含 completed)· 装配卡「流程阶段」槽照此渲染。"""
    chain: list[str] = []
    sd = dims.get("spec_depth", "prd_tech")
    if sd in ("prd", "prd_tech"):
        chain.append("goal")
    if dims.get("ui"):                       # 事实判断(有没有 UI 改动)· 与轻重正交
        chain.append("ui_design")
    if sd == "prd_tech":
        chain.append("blueprint")
    # D2:证据门关 = execute(零门禁自由执行)· 开 = dev(测试证据四门)
    chain.append("dev" if dims.get("evidence_gate", True) else "execute")

    rv = dims.get("review") or {}
    if rv.get("review"):            # 评审点 0 路 = 该 stage 不进(review stage 就是这个评审点)
        chain.append("review")
    vd = dims.get("verify_depth", "test")
    if vd in ("test", "test_e2e"):
        chain.append("test")
    if vd == "test_e2e":
        chain.append("browser_e2e")
    if rv.get("pm_acceptance"):
        chain.append("pm_acceptance")
    chain.append("ship")             # 🔴 ship 在任何组合里都减不掉(用户看见改动的最后一处)
    return chain


def derive_flow_graph(dims: dict) -> dict[str, list[str]]:
    """🔴 维度 → 转移图(**链的单源**)。

    v8.343:链不再由「每档一张静态图」维护 —— 那样计划(assembly_plan)与图是两份
    手写载体,必漂(v8.324 教训)。矩阵推出链,图就是计划本身。
    静态 FLOW_BY_TYPE 保留为**无 plan 的存量 state 回退**;两者对五个 preset 必须逐一相等
    (机器锁 · 一旦漂移测试当场红)。
    """
    chain = derive_chain(dims)
    graph: dict[str, list[str]] = {a: [b] for a, b in zip(chain, chain[1:])}
    graph["ship"] = ["completed"]
    graph["completed"] = []
    # 🔴 回退边不因降档消失:评审/验收打回照样回 dev(减的是路数,不是返工路径)
    for point in ("review", "pm_acceptance"):
        if point in graph and "dev" in chain:
            graph[point].append("dev")
    return graph


def build_assembly_plan(tier: str, override: Optional[dict] = None,
                        set_at: str = "prepare", axes: Optional[dict] = None) -> dict:
    """档 + 自定覆盖 → assembly_plan(计划的**独立的家**)。

    v8.343:计划此前散在 `execution_hints` 的三个 boolean 里,而同一个 dict 还装着执行度量
    (test_baseline_excluded / integration_new_failures …)—— 计划与度量混住,导致计划无法被
    整体渲染/比对/校准,装配卡只能手写。手写载体与机器载体必漂(v8.324)。
    立独立结构后:装配卡从 plan 渲染 · 修订记 delta · ship 台账记方向 → 校准闭环才有数据源。
    """
    return {
        "tier": tier,                      # 起手档名(记录用 · 维度才是权威)
        "set_at": set_at,                  # prepare(无 goal 的档)/ goal(调研后装配)
        "dims": merge_dims(tier_dims(tier), override),
        "axes": axes or {},                # 四轴证据:方向 / 契约面 / 影响面 / 验证成本
        "revisions": [],                   # 显式修订点的 delta 台账(加减同价 · 各记一行证据)
    }


def plan_dims(state: dict) -> Optional[dict]:
    """state → 装配计划的维度(无 plan 返 None · 调用方回退静态图)。"""
    plan = state.get("assembly_plan") or {}
    dims = plan.get("dims")
    return dims if isinstance(dims, dict) else None


def validate_dims(dims: dict) -> list[str]:
    """§1.3 一致性约束 —— 拆维度必然产生不连贯组合 · 这里挡掉(返回违规描述列表)。

    只查**组合连贯性**;模型错开 / PRD·TECH 高档是硬不变式,不进矩阵(既有机器门守)。
    """
    bad: list[str] = []
    sd = dims.get("spec_depth")
    vd = dims.get("verify_depth")
    gate = dims.get("evidence_gate", True)
    rv = dims.get("review") or {}

    if sd not in SPEC_DEPTHS:
        bad.append(f"spec_depth={sd!r} 非法 · 应属 {SPEC_DEPTHS}")
    if vd not in VERIFY_DEPTHS:
        bad.append(f"verify_depth={vd!r} 非法 · 应属 {VERIFY_DEPTHS}")
    for k in rv:
        if k not in REVIEW_POINTS:
            bad.append(f"评审点 {k!r} 非法 · 应属 {REVIEW_POINTS}")

    # ①② 规格深度决定哪些冷审点**存在**(N/A ≠ 0 路:0 路是在链上不派 · N/A 是不在链上)
    if sd == "none" and (rv.get("goal") or rv.get("blueprint")):
        bad.append("spec_depth=none 时无 goal/blueprint stage · 其冷审点不适用(不能配路数)")
    if sd == "prd" and rv.get("blueprint"):
        bad.append("spec_depth=prd 时不进 blueprint · 其冷审点不适用(TECH 不产 · 无对象可审)")
    # ③④ 证据门与验证深度联动:没有测试证据,test stage 无从接
    if not gate and vd != "self":
        bad.append("evidence_gate=关 时无测试证据 · verify_depth 只能是 self(test stage 无从接)")
    if gate is False and sd != "none":
        bad.append("evidence_gate=关 仅适用于无行为面的改动 · 不应同时要求规格文档")
    return bad


def resolve_flow_graph(flow_type: str, preset: str = "full", dims: Optional[dict] = None) -> dict:
    """按 (flow_type, preset[, dims]) 解析转移图 · legacy flow_type 自动归一。

    v8.343:**有 dims 就推导**(assembly_plan 是链的单源)· 无 dims 回退静态图
    (存量 state / Bug 流)。两条路径不是并行口径 —— 静态图是回退,且被机器锁住
    「推导边 ⊆ 静态边」,漂了当场红。
    """
    if flow_type in LEGACY_FLOW_ALIASES:
        flow_type, preset = LEGACY_FLOW_ALIASES[flow_type]
    if flow_type == "Feature" and dims:
        return derive_flow_graph(dims)
    if flow_type == "Feature" and preset in _STRUCTURAL_PRESETS:
        return FLOW_BY_TYPE[f"Feature:{preset}"]
    return FLOW_BY_TYPE.get(flow_type, {})


def internal_flow_key(flow_type: str, preset: str = "full") -> str:
    """(public 或 legacy)flow → 内部图/表键(Micro 键保留 · v8.222 物化校验统一入口)。"""
    ft, pre = normalize_flow(flow_type, preset)
    if ft == "Feature" and pre in _STRUCTURAL_PRESETS:
        return pre.capitalize()          # micro → Micro · tiny → Tiny
    return ft


def normalize_flow(flow_type: str, preset: str = None):
    """(legacy 或新)flow_type → (public_flow_type, preset)。"""
    if flow_type in LEGACY_FLOW_ALIASES:
        return LEGACY_FLOW_ALIASES[flow_type]
    return flow_type, (preset or "full")

# 不进状态机的流程类型(init-feature 拒绝创建 state.json · PMO 主对话直接执行)
NON_STATE_MACHINE_FLOWS = {"Feature Planning", "问题排查"}

# snapshot tier 字段集
SNAPSHOT_CORE_FIELDS = (
    "feature_id",
    "sub_project",
    "flow_type",
    "current_stage",
    "completed_stages",
    "legal_next_stages",
    "ship.phase",
    "ship.shipped",
    "ship.merge_target_push_failed",
    "blocking.pending_user_confirmations",
    "blocking.pending_external_deps",
    "updated_at",
)

SNAPSHOT_STAGE_FIELDS = SNAPSHOT_CORE_FIELDS + (
    "stage_contracts",
    "planned_execution",
    "executor_history",
    "environment_config.merge_target",
    "environment_config.branch",
    "worktree.path",
    "worktree.branch",
)


# ─── IO ────────────────────────────────────────────────────────────────


def state_path(feature: str) -> Path:
    p = Path(feature) / "state.json"
    if not p.exists():
        # 输出保持 JSON(与 JsonErrorArgumentParser「全输出可 json.load」承诺一致)
        die(2, json.dumps({
            "verdict": "FAIL",
            "error": f"state.json not found: {p}",
            "hint": "确认 --feature 指向含 state.json 的 artifact_root · 或先跑 state.py init-feature 创建",
        }, ensure_ascii=False, indent=2))
    return p


# 注:主工作区拦截(ship2/finalize 必在主工作区)由 _v8_ship._ship_finalize_precheck
# 独立实现(TEAMWORK_BYPASS_MAIN_WORKTREE 旁路)· state.py 不再持有副本。


# ─── Checksum guard (v7.3.10+P0-148) ───────────────────────────────────
# state.json checksum 自防护 · 跨宿主物理拦截直写 state.json。
# 设计：state.py 每次写都更新 `_state_checksum` · 每次读先 verify · 不一致 → fail。
# 旁路：TEAMWORK_BYPASS_CHECKSUM=1（仅 recover 子命令 / migration / debug）。

CHECKSUM_FIELD = "_state_checksum"
CHECKSUM_BYPASS_ENV = "TEAMWORK_BYPASS_CHECKSUM"


def _compute_checksum(state: dict[str, Any]) -> str:
    """canonical sha256(state without _state_checksum field)."""
    cleaned = {k: v for k, v in state.items() if k != CHECKSUM_FIELD}
    canonical = json.dumps(cleaned, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _verify_checksum(state: dict[str, Any], path: Path) -> None:
    """Verify state.json checksum · die(2) on mismatch (unless bypassed)."""
    if os.environ.get(CHECKSUM_BYPASS_ENV):
        return
    stored = state.get(CHECKSUM_FIELD)
    if stored is None:
        # Legacy state.json (pre-P0-148) — accept silently · 下次写自动 stamp
        return
    expected = _compute_checksum(state)
    if stored != expected:
        die(2, json.dumps({
            "verdict": "FAIL",
            "error": "state.json checksum mismatch · 检测到 state.py 之外的直接修改",
            "path": str(path),
            "stored_prefix": stored[:24],
            "expected_prefix": expected[:24],
            "hint": (
                "选项 1: 用 `state.py recover --feature {path} --reason \"...\"` "
                "重新认证 checksum（追加 concerns WARN audit）\n"
                "选项 2: 设 TEAMWORK_BYPASS_CHECKSUM=1 旁路（仅 debug / migration · 不留 audit）\n"
                "选项 3: `git checkout {path}` 从 git 恢复"
            ),
            "ref": "scripts-policy.md § R7(c) evidence-binding · v7.3.10+P0-148",
        }, ensure_ascii=False, indent=2))


def load_state(feature: str) -> dict[str, Any]:
    path = state_path(feature)
    state = json.loads(path.read_text(encoding="utf-8"))
    _verify_checksum(state, path)
    return state


def die(code: int, msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def get_dotted(obj: Any, dotted: str) -> Any:
    cur = obj
    for seg in dotted.split("."):
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return None
    return cur


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write(path: Path, state: dict[str, Any]) -> None:
    """同目录 temp file + os.replace · 同分区原子。"""
    state["updated_at"] = now_iso()
    state["updated_by"] = state.get("updated_by") or "pmo"
    try:
        from _v8_engine import STATE_SCHEMA_VERSION as _ssv  # 单源 · 模块缓存后零开销
        state["_schema_version"] = _ssv
    except ImportError:
        pass
    # v7.3.10+P0-148 checksum guard：每次写后 stamp 新 checksum（基于 _state_checksum 外字段）
    state[CHECKSUM_FIELD] = _compute_checksum(state)
    fd, tmp = tempfile.mkstemp(prefix=".state.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def collect_cited(state: dict[str, Any], cite: str | None) -> dict[str, Any]:
    if not cite:
        return {}
    out = {}
    for f in cite.split(","):
        f = f.strip()
        if f:
            out[f] = get_dotted(state, f)
    return out


def diff_dotted(before: dict, after: dict, fields: list[str]) -> dict[str, Any]:
    """计算指定 dotted 字段的前后差异（用于 updated_fields 输出）。"""
    out = {}
    for f in fields:
        b = get_dotted(before, f)
        a = get_dotted(after, f)
        if b != a:
            out[f] = a
    return out


# ─── snapshot ──────────────────────────────────────────────────────────


def cmd_snapshot(args: argparse.Namespace) -> None:
    state = load_state(args.feature)

    # raw-write 主动告警(v8.12 · 治本"raw-write 出现 = 状态机缺口"无 PMO 提示)
    from _v8_engine import compute_raw_write_audit
    rw_audit = compute_raw_write_audit(state)

    if args.tier == "full":
        emit({
            "verdict": "OK",
            "snapshot": state,
            **({"raw_write_audit": rw_audit} if rw_audit else {}),
        })
        return

    fields = SNAPSHOT_CORE_FIELDS if args.tier == "core" else SNAPSHOT_STAGE_FIELDS
    snap = {f: get_dotted(state, f) for f in fields}

    extra = {}
    if args.cite:
        for f in args.cite.split(","):
            f = f.strip()
            if f and f not in snap:
                extra[f] = get_dotted(state, f)

    emit(
        {
            "verdict": "OK",
            "tier": args.tier,
            "snapshot": snap,
            **({"cited_extra": extra} if extra else {}),
            **({"raw_write_audit": rw_audit} if rw_audit else {}),
        }
    )


# ─── validate ──────────────────────────────────────────────────────────


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    cur = state.get("current_stage")
    if cur not in LEGAL_STAGES:
        errors.append(f"current_stage 非法值: {cur!r} ∉ {sorted(LEGAL_STAGES)}")

    flow_type = state.get("flow_type")
    if flow_type not in PUBLIC_FLOW_TYPES and flow_type not in LEGACY_FLOW_ALIASES:
        errors.append(
            f"flow_type 非法值: {flow_type!r} ∉ {list(PUBLIC_FLOW_TYPES)}"
            "(legacy Micro 自动归一 · 不进状态机的流程类型不应有 state.json)"
        )

    completed = state.get("completed_stages") or []
    if not isinstance(completed, list):
        errors.append("completed_stages 必须是数组")
    else:
        for s in completed:
            if s not in LEGAL_STAGES:
                errors.append(f"completed_stages 含非法值: {s!r}")

    legal_next = state.get("legal_next_stages") or []
    if not isinstance(legal_next, list):
        errors.append("legal_next_stages 必须是数组")

    contracts = state.get("stage_contracts") or {}
    if not isinstance(contracts, dict):
        errors.append("stage_contracts 必须是对象")
    else:
        for stage_name, c in contracts.items():
            if not isinstance(c, dict):
                errors.append(f"stage_contracts.{stage_name} 必须是对象")
                continue
            for gate in GATE_NAMES:
                if gate not in c:
                    errors.append(f"stage_contracts.{stage_name}.{gate} 缺失")
            # gate 顺序：output 不能在 process 前 / process 不能在 input 前
            i_ok = c.get("input_satisfied") is True
            p_ok = c.get("process_satisfied") is True
            o_ok = c.get("output_satisfied") is True
            if p_ok and not i_ok:
                errors.append(
                    f"stage_contracts.{stage_name}: process_satisfied=true 但 input_satisfied=false"
                )
            if o_ok and not p_ok:
                errors.append(
                    f"stage_contracts.{stage_name}: output_satisfied=true 但 process_satisfied=false"
                )

    # ship 状态机
    ship = state.get("ship") or {}
    phase = ship.get("phase")
    if phase not in SHIP_PHASE_ENUM:
        errors.append(f"ship.phase 非法值: {phase!r} ∉ {sorted(x for x in SHIP_PHASE_ENUM if x)}")
    shipped = ship.get("shipped")
    if shipped not in SHIP_SHIPPED_ENUM:
        errors.append(
            f"ship.shipped 非法值: {shipped!r} ∉ {sorted(x for x in SHIP_SHIPPED_ENUM if x)}"
        )
    if phase == "pushed" and not ship.get("feature_head_commit"):
        errors.append("ship.phase=pushed 但 feature_head_commit 缺失（第二段 finalize 依赖）")

    # evidence-binding（治本 P0-101 / P0-119）
    ecr = state.get("external_cross_review", {}) or {}
    avail = ecr.get("available_external_clis")
    evidence = ecr.get("detection_evidence")
    # 仅当数组非空（已探测出至少一项）或已 decided 时强校验 evidence
    has_detection_signal = (isinstance(avail, list) and len(avail) > 0) or ecr.get("decided_at")
    if has_detection_signal and not evidence:
        errors.append(
            "external_cross_review 已声明探测结果但 detection_evidence 缺失（P0-101）"
        )

    schema_docs = state.get("global_schema_docs")
    schema_evidence = state.get("global_schema_docs_evidence")
    if isinstance(schema_docs, list) and len(schema_docs) > 0 and not schema_evidence:
        errors.append("global_schema_docs 已填但 global_schema_docs_evidence 缺失（P0-119）")

    # artifact_root 一致性
    root = state.get("artifact_root")
    if not root:
        errors.append("artifact_root 缺失（P0-41 写操作硬门禁前提）")

    return errors


def cmd_validate(args: argparse.Namespace) -> None:
    state = load_state(args.feature)
    errors = validate_state(state)
    if errors:
        emit({"verdict": "FAIL", "errors": errors, "error_count": len(errors)})
        sys.exit(1)
    emit(
        {
            "verdict": "PASS",
            "checks_passed": [
                "stage enum",
                "flow_type enum",
                "stage_contracts gate ordering",
                "ship phase/shipped enum",
                "ship pushed completeness",
                "evidence-binding (P0-101 / P0-119)",
                "artifact_root present",
            ],
        }
    )


# ─── raw-read ──────────────────────────────────────────────────────────


def cmd_raw_read(args: argparse.Namespace) -> None:
    state = load_state(args.feature)
    from _v8_engine import compute_raw_write_audit
    rw_audit = compute_raw_write_audit(state)

    if args.field:
        val = get_dotted(state, args.field)
        emit({
            "verdict": "OK",
            "field": args.field,
            "value": val,
            **({"raw_write_audit": rw_audit} if rw_audit else {}),
        })
        return
    emit({
        "verdict": "OK",
        "warning": "raw-read 全量返回 · 仅 debug/migration 使用",
        "state": state,
        **({"raw_write_audit": rw_audit} if rw_audit else {}),
    })


def cmd_raw_write(args: argparse.Namespace) -> None:
    """🚪 逃生舱：跳过 schema/状态机校验直写 · 自动追加 concerns WARN。

    每条 --set key=val · val 优先按 JSON 解析（true/false/null/number/array/object）失败则当字符串。
    """
    if not args.set:
        die(2, json.dumps({"verdict": "FAIL", "error": "至少一个 --set key=val"},
                          ensure_ascii=False, indent=2))
    if not args.reason:
        die(2, json.dumps({"verdict": "FAIL",
                           "error": "raw-write 必带 --reason · 该理由会自动写入 concerns"},
                          ensure_ascii=False, indent=2))
    path = state_path(args.feature)
    state = json.loads(path.read_text(encoding="utf-8"))

    applied: list[tuple[str, Any]] = []
    for kv in args.set:
        if "=" not in kv:
            die(2, json.dumps({"verdict": "FAIL", "error": f"--set 需 key=val 形式: {kv!r}"},
                              ensure_ascii=False, indent=2))
        k, _, raw = kv.partition("=")
        try:
            val = json.loads(raw)
        except json.JSONDecodeError:
            val = raw
        # 写入 dotted path · 自动建中间 dict
        cur = state
        segs = k.split(".")
        for seg in segs[:-1]:
            cur = cur.setdefault(seg, {})
            if not isinstance(cur, dict):
                die(2, json.dumps({"verdict": "FAIL",
                                   "error": f"--set {k}: 中段 {seg!r} 非 dict 无法下钻"},
                                  ensure_ascii=False, indent=2))
        cur[segs[-1]] = val
        applied.append((k, val))

    state.setdefault("concerns", []).append(
        f"{now_iso()} WARN raw-write 跳过校验 · 改动 {len(applied)} 字段 · 理由：{args.reason}"
    )

    # raw-write 明确允许 invalid state · 不做写前 validate
    atomic_write(path, state)
    emit({
        "verdict": "OK",
        "warning": "raw-write 跳过 schema/状态机校验 · 已记 concerns WARN",
        "applied": [{"path": k, "value": v} for k, v in applied],
        "reason": args.reason,
    })


# ─── P4: add-concern ─────────────────────────────────────────────────
#
# 注:cmd_pm_decision(v7 fossil · 写 stage_contracts.pm_acceptance.decision
# 顶层位 · v8 规范是 evidence.decision)已物理删除 —— 是 landmine,留着会
# 让 reader 漂移(治本 ADMIN-F013 case · 详 _v8_stage_specs._pm_decision_value)。


def cmd_add_concern(args: argparse.Namespace) -> None:
    """v8.172:append 一条 concern 到 state.concerns(审计锚 · auto/skip+WARN 自决留痕)。

    治本:SKILL/goal-stage 多处文档引用 `add-concern --severity WARN --message`(命令曾被
    误删 · 实证 audit ×3:AI 想记 incidental-scope concern 失败 · 只能塞 commit message)。
    格式同既有 append(reset-prev 等):`<ISO> <SEVERITY> <message>`。
    """
    path = state_path(args.feature)
    state = load_state(args.feature)
    entry = f"{now_iso()} {args.severity} {args.message}"
    state.setdefault("concerns", []).append(entry)
    state["updated_at"] = now_iso()
    state["updated_by"] = "add-concern"
    atomic_write(path, state)
    emit({
        "verdict": "OK",
        "action": "add-concern",
        "severity": args.severity,
        "message": args.message,
        "concerns_count": len(state["concerns"]),
        "entry": entry,
    })



def cmd_review_preventability(args: argparse.Namespace) -> None:
    """v8.281:评审收敛后记录「起草可预防性」—— 本次 findings 里多少起草时本可预防 + 缺哪条起草考虑点。

    非门禁 · 纯数据采集(不记不拦 ship · 台账列留空是有效前缀)· ship 聚合进「🛡️ 起草可预防性」列。
    用途:年检据此判 PRD/TECH **起草考虑点**(PL六问 / TECH 简洁性自查 / 起草思考规范)到底缺不缺 ——
    同一条「缺的考虑点」跨 feature 反复出现 = 真缺口 · 补进框架考虑点或项目复发清单;
    全是 emergent(涌现真问题)= 考虑点没问题别动。判据同 v8.278:findings 82% 真 · 砍轮=漏 bug ·
    真杠杆是把**可预防子集**在起草时挡掉(不是砍评审)。
    """
    path = state_path(args.feature)
    state = load_state(args.feature)
    entry = {
        "stage": args.stage,
        "preventable": max(0, int(getattr(args, "preventable", 0) or 0)),
        "total": max(0, int(getattr(args, "total", 0) or 0)),
        "missing": [m.strip() for m in (getattr(args, "missing", "") or "").split(";") if m.strip()],
        "note": (getattr(args, "note", "") or "").strip(),
        "at": now_iso(),
    }
    state.setdefault("authoring_preventability", []).append(entry)
    state["updated_at"] = now_iso()
    state["updated_by"] = "review-preventability"
    atomic_write(path, state)
    # v8.346(年检实证):可预防率 70.5%(1461/2072),而 KNOWLEDGE 复发防御清单
    # aon-core 0 条 / aib 0 条 / supersdk 3 条 —— **读取端接线了、写入端从来没有**
    # (dev brief 每次让 AI 读它,却没有任何动作把 finding 沉淀回去)。
    # 这里把骨架现成给出:数据算好了不让人誊抄(v8.323 形状)· 判断留人/AI(教训文本要判断)。
    _defense = None
    if entry["preventable"] > 0:
        _fid = state.get("feature_id") or "<FEATURE-ID>"
        _defense = {
            "why": (f"本次 {entry['preventable']}/{entry['total']} 条 finding 起草时本可预防 —— "
                    "不沉淀 = 下个 feature 原样再犯一次(可预防率常年 70% 的根因)"),
            "target": "project-specs/KNOWLEDGE.md § 复发防御清单",
            "skeleton": (f"## 复发防御清单 · <一句主题>({_fid} · {now_iso()[:10]})\n\n"
                         f"- 🔴 **<写成「写时防」的祈使句,不是「本次发现了什么」>**。"
                         f"<判据 + 回归要覆盖什么>\n"),
            "rule": "🔴 写**下次起草时能照着做**的话 · 不写事故复述(清单是给起草读的,不是给复盘读的)",
        }

    emit({"verdict": "OK", "action": "review-preventability", "stage": entry["stage"],
          **({"defense_list_entry": _defense} if _defense else {}),
          "recorded": entry,
          "note": "已记录 · ship 聚合进台账「🛡️ 起草可预防性」列(年检据此分析起草考虑点缺不缺)"})


def cmd_stage_cost(args: argparse.Namespace) -> None:
    """v8.295:stage 收敛后记录**耗时归因** —— 这段时间里哪些轮次是协调开销、最大的一笔是什么。

    为什么需要:机器已经采到 duration / await / active_minutes(v8.276),但那只有**数字**,
    没有「时间花在哪」。实证 SVC-PLATFORM-F260726 复盘的最大发现恰恰是归因 ——
    blueprint 6 波往返里波 5、6 是**纯文档对齐无设计价值**,双文档同步吃掉 ~35% 轮次 / ~25% token。
    这类归因**只有 stage 结束时当场记得住**;ship 时回填要靠产物 mtime 反推(复盘干的就是这苦活)。

    🔴 为什么这不是又一道「环节化自检」(v8.283 判定会衰减的那类):
    它不是让 AI 自查做得好不好 —— 是采**一个 AI 自己算不出、后面也复原不了的事实**。
    且它是**验证优化是否起效的唯一手段**:v8.294 的收敛期归一 / TC 边界 / 投机窗准入都声称能砍
    协调开销,没有这列数据就无法证伪。

    非门禁 · 纯采集(不记不拦 ship · 台账列留空 = 有效前缀 · 同 v8.281)。
    """
    path = state_path(args.feature)
    state = load_state(args.feature)
    rounds = max(0, int(getattr(args, "rounds", 0) or 0))
    overhead = max(0, int(getattr(args, "overhead_rounds", 0) or 0))
    if overhead > rounds:
        emit({"verdict": "FAIL", "action": "stage-cost",
              "error": f"--overhead-rounds({overhead}) 不能大于 --rounds({rounds})"})
        sys.exit(1)
    entry = {
        "stage": args.stage,
        "rounds": rounds,
        "overhead_rounds": overhead,
        "kinds": [k.strip() for k in (getattr(args, "kinds", "") or "").split(";") if k.strip()],
        "note": (getattr(args, "note", "") or "").strip(),
        "at": now_iso(),
    }
    state.setdefault("stage_cost", []).append(entry)
    state["updated_at"] = now_iso()
    state["updated_by"] = "stage-cost"
    atomic_write(path, state)
    emit({"verdict": "OK", "action": "stage-cost", "stage": entry["stage"],
          "recorded": entry,
          "note": "已记录 · ship 聚合进台账「⏱️ 耗时归因」列"
                  "(年检据此判协调开销占比趋势 · 验证提效改动是否真起效)"})


def cmd_pause_mark(args: argparse.Namespace) -> None:
    """v8.192:标记 stage 内暂停点开始(计时排毒 · emit R5 暂停点时跑)。

    下一个流程命令(xx-start/complete/fix/retry)自动闭合 · 等待墙钟累计进该 stage 的
    await_minutes · 耗时分析工作/等待分离(resume 侧零纪律)。重复 mark = 覆盖(取最新)。
    """
    path = state_path(args.feature)
    state = load_state(args.feature)
    state["open_pause"] = {
        "stage": state.get("current_stage") or "",
        "label": (getattr(args, "label", None) or "").strip() or "R5 pause",
        "started_at": now_iso(),
    }
    state["updated_at"] = now_iso()
    state["updated_by"] = "pause-mark"
    atomic_write(path, state)
    emit({"verdict": "OK", "action": "pause-mark", "stage": state["open_pause"]["stage"],
          "label": state["open_pause"]["label"],
          "note": "下一个流程命令自动闭合 · 等待墙钟计入该 stage await_minutes(不算工作)"})


# ─── ws-progress:WS 进度 rollup（v8.174）──────────────────────────────
# 治本:WS 文档只有「规划态」(features[].status=pending/planned)· 无「执行态」进度。
# 执行态单一源在各子项目 ROADMAP 的「状态」列(职责单一 · 禁手抄进 WS)→ 只能派生。
# 本命令 glob 全仓 ROADMAP.md · 按「关联 WS」列过滤 · 确定性汇总成进度块(写回 WS 标记区)。

_WS_PROG_START = "<!-- WS-PROGRESS:START"
_WS_PROG_END = "<!-- WS-PROGRESS:END -->"
_WS_DAG_START = "<!-- WS-DAG:START"
_WS_DAG_END = "<!-- WS-DAG:END -->"
# ROADMAP「状态」列词表(单源 · templates/roadmap.md §表格维护规则 与此对齐):
# 完成态收别名「已交付/已上线」—— 实战:项目 ROADMAP 混用「✅ 已交付」被判待开始 → 进度 0/N 假象 +
# ready_to_start 失灵。匹配按「剥前导 emoji 后的起始词」· 防「基本已完成，待测试」子串误判完成。
_WS_STATUS_DONE = ("已完成", "已交付", "已上线")
_WS_STATUS_DOING = ("进行中",)
_WS_STATUS_CANCELLED = ("已取消",)
_WS_STATUS_PENDING_WORDS = ("待开始", "待启动", "已规划", "待前置", "待确认", "草稿", "待排期")
_WS_STATUS_ICON = {"已完成": "✅", "进行中": "🔄", "已取消": "🗑️"}
_WS_STATUS_LEAD_STRIP = re.compile(r"^[\s✅🔄⏳🔒📝🗑️*_`~•·>-]+")


def _ws_status_bucket(st: str) -> tuple[str, bool]:
    """状态格 → (规范桶, 是否词表可识别)。桶 ∈ 已完成/进行中/已取消/等待依赖/待开始/未匹配。

    词表外写法归「待开始」且标不可识别 —— 上层 surface 警告 · 不静默吞(治词表漂移无人发现)。
    """
    s = (st or "").strip()
    if not s:
        return "待开始", True
    if "未匹配" in s or "未写入" in s:
        return "未匹配", True
    core = _WS_STATUS_LEAD_STRIP.sub("", s)
    for words, canon in ((_WS_STATUS_DONE, "已完成"), (_WS_STATUS_DOING, "进行中"),
                         (_WS_STATUS_CANCELLED, "已取消")):
        if any(core.startswith(w) for w in words):
            return canon, True
    if "等待" in s:
        return "等待依赖", True
    if any(w in s for w in _WS_STATUS_PENDING_WORDS):
        return "待开始", True
    return "待开始", False


# WS/ROADMAP 全仓 rglob 的排除集(单源):显式目录名 + 任何隐藏目录段。
# 🔴 .worktree 必须排除 —— 并行 feature worktree 内是旧基线副本 · 命中即「算旧写旧」+
# 污染他人工作区(工具写进别的 worktree · verdict 却 OK)。隐藏段规则兜住自定义 worktree 根。
_WS_SCAN_SKIP = {"node_modules", ".git", ".worktree", "_archive", "dist", "build",
                 ".next", "vendor"}


def _ws_scan_ok(p: Path, root: Path) -> bool:
    """rglob 候选过滤:目录段命中排除集或以 . 开头 → 排除(只判 root 以内的段)。"""
    try:
        parts = p.relative_to(root).parts
    except ValueError:
        parts = p.parts
    return not any(seg in _WS_SCAN_SKIP or seg.startswith(".") for seg in parts[:-1])


def _ws_nums(text: str) -> set[int]:
    """从一段文本抽出所有 WS 编号(容 WS-01 / WS-1 / `WS-02`)→ {int}。"""
    return {int(n) for n in re.findall(r"WS-?0*(\d+)", text or "", re.I)}


def _ws_short(fid: str, ws_label: str) -> str:
    """feature 临时 id 短名:WS-03-K0 → K0 · WS-03-S1 → S1（DAG 节点 / 总览用）。"""
    return re.sub(r"^WS-?\d+-", "", (fid or "").strip()) or (fid or "")


def _parse_ws_features(ws_file: Path) -> list[dict]:
    """raw-scan WS frontmatter 的 `features:` 列 → [{id,target,bl,deps,status,scope}]。

    治本(v8.177):跨子项目/legacy 格式的 feature(如 K0=SDK-F040 在 SDK ROADMAP 无「关联 WS」列)
    只在 WS 自己的名册里登记 · ws-progress 必须读名册才不漏。frontmatter 是 list-of-dict(简单
    key:value 解析器不支持)→ 限定在 TEAMWORK-MACHINE 注释区行扫描。
    """
    try:
        text = ws_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    mc = re.search(r"<!--\s*TEAMWORK-MACHINE.*?\n(.*?)\n-->", text, re.S)
    head = mc.group(1) if mc else text.split("\n# ", 1)[0]   # 退路:首个 body H1 之前
    feats: list[dict] = []
    cur: dict | None = None
    in_feats = False
    for ln in head.splitlines():
        if re.match(r"^\s{0,2}features:\s*(#.*)?$", ln):
            in_feats = True
            continue
        if not in_feats:
            continue
        if re.match(r"^[A-Za-z_]\w*:", ln):        # 回到顶层另一键 → features 段结束
            break
        m_id = re.match(r"^\s*-\s*id:\s*(.+?)\s*(#.*)?$", ln)
        if m_id:
            if cur:
                feats.append(cur)
            cur = {"id": m_id.group(1).strip().strip("\"'"), "target": "", "bl": "",
                   "deps": [], "status": "", "scope": "", "goal_plain": ""}
            continue
        if cur is None:
            continue
        m_kv = re.match(r"^\s*(target|bl|status|scope|dependencies|goal_plain):\s*(.*?)\s*$", ln)
        if m_kv:
            k, v = m_kv.group(1), m_kv.group(2).strip().strip("\"'")
            if k == "dependencies":
                inner = v.strip().lstrip("[").rstrip("]").strip()
                cur["deps"] = [d.strip().strip("\"'") for d in inner.split(",") if d.strip()]
            elif k == "bl":
                cur["bl"] = "" if v in ("null", "~", "") else v
            else:
                cur[k] = v
    if cur:
        feats.append(cur)
    return feats


def _parse_roadmap_rows(path: Path, id_allow: set[str] | None = None) -> list[dict]:
    """解析一个 ROADMAP.md 内**所有** Feature 表 → [{bl,name,status,stage,f_id,ws}]。

    按列名定位(Feature ID / 功能名称 / 状态 / 当前阶段 / 对应 F编号 / 关联 WS)· 容列序/多余列/
    多表。v8.177:① 表头门槛降到 BL+状态(「关联 WS」列可缺 · 吃 legacy 表)② 行 id 除 BL-NNN 外
    放行 id_allow(WS 名册声明的跨子项目 id 如 SDK-F040)。
    """
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    aliases = {
        "bl": ("Feature ID", "Feature  ID"),
        "name": ("功能名称",),
        "status": ("状态",),
        "stage": ("当前阶段",),
        "f_id": ("对应 F编号", "对应F编号", "F编号"),
        "ws": ("关联 WS", "关联WS"),
    }
    rows: list[dict] = []
    col: dict[str, int] = {}
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            col = {}          # 离开表 → 表头失效
            continue
        cells = [c.strip().strip("`").strip() for c in s.strip("|").split("|")]
        if cells and all(set(c) <= set("-: ") for c in cells if c):
            continue          # |---|---| 分隔行
        if not col:
            found: dict[str, int] = {}
            for key, names in aliases.items():
                for i, c in enumerate(cells):
                    if any(n in c for n in names):
                        found[key] = i
                        break
            if {"bl", "status"} <= found.keys():
                col = found    # v8.177:有 BL+状态即认表头(关联WS 列可缺 · legacy 表)
            continue

        def cell(key: str) -> str:
            i = col.get(key)
            return cells[i] if i is not None and i < len(cells) else ""
        bl = cell("bl")
        if not (re.match(r"BL-?\d+", bl, re.I) or (id_allow and bl in id_allow)):
            continue           # 非 BL 行跳过 · 但放行名册声明的 id(SDK-F040 等)
        rows.append({
            "bl": bl, "name": cell("name"), "status": cell("status") or "待开始",
            "stage": cell("stage"), "f_id": cell("f_id"), "ws": cell("ws"),
        })
    return rows


def _render_ws_progress(ws_label: str, items: list[dict], n_roadmaps: int,
                        roster_driven: bool) -> tuple[str, list[dict]]:
    """汇总行 + 总览表(markdown)· items 含 subproject/short 字段。

    返回 (block, unrecognized):词表外状态写法列表(feature 短名 + 原文)· 上层 surface。
    """
    counts: dict[str, int] = {}
    unrecognized: list[dict] = []
    for it in items:
        b, known = _ws_status_bucket(it["status"])
        counts[b] = counts.get(b, 0) + 1
        if not known:
            unrecognized.append({"feature": it.get("short") or it["bl"],
                                 "status": it["status"]})
    total = sum(v for k, v in counts.items() if k != "已取消")
    done = counts.get("已完成", 0)
    seq = [("进行中", counts.get("进行中", 0)), ("待开始", counts.get("待开始", 0)),
           ("等待依赖", counts.get("等待依赖", 0)), ("未匹配", counts.get("未匹配", 0)),
           ("已取消", counts.get("已取消", 0))]
    tail = " · ".join(f"{n} {k}" for k, n in seq if n)
    src = (f"名册 {len(items)} feature · 状态自 {n_roadmaps} 个 ROADMAP 匹配"
           if roster_driven else f"自 {n_roadmaps} 个 ROADMAP 汇总")
    if not items:
        head = "进度 暂无数据(本 WS 的 feature 尚未写入任何 ROADMAP · 规划完成后自动出现)"
    else:
        head = f"进度 {done}/{total} 已完成" + (f" · {tail}" if tail else "")
    lines = [head, f"（{src} · {now_iso()}）", ""]
    if unrecognized:
        lines.insert(1, "⚠️ 状态词不在词表(按待开始计 · 词表见 templates/roadmap.md):" +
                     " · ".join(f"{u['feature']}「{u['status'][:24]}」" for u in unrecognized))
    if items:
        lines += ["| feature | BL | 涉及子项目 | 功能 | 大白话目标 | 状态 | 当前阶段 | F |",
                  "|---------|----|-----------|------|-----------|------|----------|---|"]
        for it in sorted(items, key=lambda x: (x.get("subproject", ""), x["bl"])):
            raw = it["status"].strip()
            b, _known = _ws_status_bucket(raw)
            icon = _WS_STATUS_ICON.get(b, "")
            st = raw if raw[:1] in "✅🔄🗑⏳🔒📝" else f"{icon} {raw}".strip()
            lines.append(
                f"| {it.get('short') or '—'} | {it['bl']} | {it.get('subproject') or '—'} "
                f"| {it['name'] or '—'} | {it.get('goal_plain') or '—'} | {st} | {it['stage'] or '—'} | {it['f_id'] or '—'} |")
    return "\n".join(lines), unrecognized


def _render_ws_dag(roster: list[dict], ws_label: str) -> str | None:
    """自 features[].dependencies 派生 Mermaid 依赖 DAG(节点=feature 短名 · 边=dep→feature)。"""
    live = [f for f in roster if f.get("status") != "废弃"]
    if not live:
        return None
    ids = {f["id"] for f in live}
    out = ["```mermaid", "flowchart LR"]
    for f in live:
        sid = _ws_short(f["id"], ws_label)
        bl = f["bl"] or "待回填"
        out.append(f'  {sid}["{sid} · {bl}"]')
    edged = False
    for f in live:
        sid = _ws_short(f["id"], ws_label)
        for d in f["deps"]:
            if d in ids:
                out.append(f"  {_ws_short(d, ws_label)} --> {sid}")
                edged = True
    if not edged:
        out.append("  %% 无声明依赖(features[].dependencies 全空)")
    out.append("```")
    return "\n".join(out)


def _ws_subproject(rm: Path, root: Path) -> str:
    """ROADMAP 路径 → 可读子项目名(多在 {子项目}/docs/ 或 project-specs/{子项目}/ 下)。"""
    sub = rm.parent.name if rm.parent != root else root.name
    if rm.parent.name in {"docs", "project-specs"} and rm.parent.parent != root:
        sub = rm.parent.parent.name
    return sub


def _pick_bl_row(feat: dict, cands: list, reg: dict, root: Path):
    """roster feature → ROADMAP 行(v8.248 · BL 撞号判别)。

    🔴 BL-NNN **各项目独立递增**(conventions §4)—— 同号跨子项目撞车时不能
    「全局首见即胜」(实证:三子项目各有 BL-001 · 勿手改自动块每次刷新都张冠李戴)。
    多候选按归属挑:① target 缩写经 teamwork-space registry 映射 docs_root ·
    候选 ROADMAP 在其树下;② 行「对应 F编号」前缀 == target;③ 目录名 ci == target;
    ④ 单候选 / 全不中兜底首个(维持旧行为 · 不比旧更差)。
    cands 元素 = (sub, row, roadmap_path)。
    """
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    tgt = (feat.get("target") or "").strip()
    if tgt:
        droot = str(reg.get(tgt) or "").strip().rstrip("/")
        if droot:
            for sub, r, rm in cands:
                try:
                    rel = str(rm.parent.relative_to(root)).rstrip("/")
                except ValueError:
                    continue
                if rel == droot or droot.startswith(rel + "/") or rel.startswith(droot + "/"):
                    return (sub, r, rm)
        for sub, r, rm in cands:
            if str(r.get("f_id") or "").startswith(tgt + "-"):
                return (sub, r, rm)
        for sub, r, rm in cands:
            if sub.lower() == tgt.lower():
                return (sub, r, rm)
    return cands[0]


def _find_ws_file(root: Path, ws_label: str):
    """定位 WS 正本 → (最优候选, 全部候选)。

    排序:product-overview/ 优先 → 路径段数少优先 → 字典序。多候选时上层 surface 清单
    (曾因 rglob 无序取首 + .worktree 未排除 · 把进度写进并行 feature worktree 的旧副本)。
    """
    cands = [p for p in root.rglob(f"{ws_label}*.md")
             if _ws_scan_ok(p, root) and "workstream" in str(p).lower()]
    if not cands:
        cands = [p for p in root.rglob(f"{ws_label}*.md") if _ws_scan_ok(p, root)]
    cands.sort(key=lambda p: (0 if "product-overview" in str(p).lower() else 1,
                              len(p.parts), str(p)))
    return (cands[0] if cands else None), cands


def _splice_block(text: str, start_tok: str, end_tok: str, body: str):
    """替换 <!-- START ...-->\\n...\\n<!-- END --> 之间内容 · 无标记返回 None。"""
    pat = re.compile(r"(" + re.escape(start_tok) + r"[^\n]*-->)\n.*?\n(" +
                     re.escape(end_tok) + r")", re.S)
    if not pat.search(text):
        return None
    return pat.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(2), text)


def _resolve_ws_from_feature(feature_dir: Path, root: Path) -> "Optional[str]":
    """v8.180:从 feature 的 F-id 在 ROADMAP「对应F编号」匹配 → 关联WS(ship 自刷用 · 不靠 AI 报 --ws)。

    链路:feature_id 抽 F-token → 扫 ROADMAP 找「对应F编号」含该 token 的行 → 读「关联 WS」·
    无关联WS 则用该行 BL 反查各 WS 名册(features[].bl)· 都不中返 None(best-effort · ship 退回提示)。
    """
    fid = ""
    sj = feature_dir / "state.json"
    state_bl = ""
    if sj.is_file():
        try:
            _st = json.loads(sj.read_text(encoding="utf-8"))
            fid = _st.get("feature_id", "") or ""
            state_bl = _st.get("bl") or ""
        except (OSError, ValueError):
            pass
    if state_bl:  # state.bl 机读绑定优先 · 直接名册反查(不依赖 ROADMAP 手填「对应F编号」)
        for wsf in root.rglob("WS-*.md"):
            if "workstream" not in str(wsf).lower() or not _ws_scan_ok(wsf, root):
                continue
            if any(f.get("bl") == state_bl for f in _parse_ws_features(wsf)):
                n = _ws_nums(wsf.name)
                if n:
                    return "WS-%02d" % min(n)
    fid = fid or feature_dir.name
    m = re.search(r"F-?\d+", fid, re.I)
    if not m:
        return None
    ftoken = m.group(0).replace("-", "").upper()
    roadmaps = [p for p in root.rglob("ROADMAP.md") if _ws_scan_ok(p, root)]
    bl_hit = None
    for rm in roadmaps:
        for r in _parse_roadmap_rows(rm):
            if ftoken in (r.get("f_id", "") or "").replace("-", "").upper():
                ws = _ws_nums(r.get("ws", ""))
                if ws:
                    return "WS-%02d" % min(ws)
                bl_hit = bl_hit or r.get("bl")    # 有 BL 无关联WS → 名册反查退路
    if bl_hit:
        for wsf in root.rglob("WS-*.md"):
            if "workstream" not in str(wsf).lower() or not _ws_scan_ok(wsf, root):
                continue
            if any(f.get("bl") == bl_hit for f in _parse_ws_features(wsf)):
                n = _ws_nums(wsf.name)
                if n:
                    return "WS-%02d" % min(n)
    return None


def cmd_ws_progress(args: argparse.Namespace) -> None:
    """v8.174/177/180:汇总某 WS 下 feature 执行态 → 进度 rollup + 依赖 DAG（派生 · 不手抄）。

    v8.180:--feature 替代 --ws —— 自 feature F-id 解析所属 WS(ship 自刷用 · 不靠 AI 报 WS 编号)。

    v8.177:名册驱动 —— 读 WS frontmatter features[] 当权威 roster(声明的 feature 全列出 · 含
    跨子项目/legacy 的 K0)· 状态自 ROADMAP 按 bl 匹配(放宽解析器吃 legacy 表)· 匹配不到标「未匹配」·
    并自 dependencies 派生 Mermaid DAG。无名册 → 回退 v8.174 纯「关联 WS」扫(向后兼容)。
    """
    root = _git_toplevel(Path.cwd()) or Path.cwd()
    raw = (getattr(args, "ws", None) or "").strip()
    if not raw and getattr(args, "feature", None):   # v8.180:--feature → 自解析 WS
        resolved = _resolve_ws_from_feature(Path(args.feature), root)
        if not resolved:
            emit({"verdict": "WARN", "action": "ws-progress", "resolved_ws": None,
                  "reason": ("--feature 无法解析 WS(F-id 未在任何 ROADMAP「对应F编号」匹配 · "
                             "或该 feature 不属任何 WS)· 跳过刷新 —— 若确属某 WS 用 --ws 显式指定")})
            return
        raw = resolved
    bare = re.fullmatch(r"0*(\d+)", raw)          # 容裸数字 01 / 1（help 承诺）
    targets = _ws_nums(raw) or ({int(bare.group(1))} if bare else set())
    if not targets:
        emit({"verdict": "FAIL", "reason": "需 --ws <编号> 或 --feature <路径>(抽不出 WS 编号)"})
        return
    ws_label = "WS-%02d" % min(targets)

    ws_file, ws_cands = _find_ws_file(root, ws_label)
    roster = [f for f in (_parse_ws_features(ws_file) if ws_file else [])
              if f.get("status") != "废弃"]
    roster_bls = {f["bl"] for f in roster if f["bl"]}

    roadmaps = [p for p in root.rglob("ROADMAP.md") if _ws_scan_ok(p, root)]
    rm_rows: list[tuple[str, dict, Path]] = []
    for rm in roadmaps:
        sub = _ws_subproject(rm, root)
        for r in _parse_roadmap_rows(rm, id_allow=roster_bls):
            rm_rows.append((sub, r, rm))
    # v8.248:BL 各项目独立递增 · 同号收全部候选 · 按 target 归属判别(_pick_bl_row)
    by_bl: dict[str, list[tuple[str, dict, Path]]] = {}
    for sub, r, rm in rm_rows:
        by_bl.setdefault(r["bl"], []).append((sub, r, rm))
    _reg = _parse_workspace_registry(root / "teamwork-space.md")

    items: list[dict] = []
    if roster:                                    # 名册驱动:声明的 feature 全列出
        for f in roster:
            short = _ws_short(f["id"], ws_label)
            hit = _pick_bl_row(f, by_bl.get(f["bl"], []), _reg, root) if f["bl"] else None
            if hit:
                sub, r, _rm = hit
                items.append({**r, "subproject": f["target"] or sub, "short": short,
                              "goal_plain": f.get("goal_plain", "")})
            else:
                items.append({
                    "bl": f["bl"] or "—", "name": f.get("scope", "")[:24],
                    "status": "未匹配 ROADMAP" if f["bl"] else "未写入 ROADMAP",
                    "stage": "", "f_id": "", "ws": ws_label,
                    "subproject": f["target"] or "—", "short": short,
                    "goal_plain": f.get("goal_plain", "")})
        seen = roster_bls
        for sub, r, _rm in rm_rows:                # 名册外但「关联 WS」命中 → 孤儿(surfacing)
            if (targets & _ws_nums(r["ws"])) and r["bl"] not in seen:
                seen = seen | {r["bl"]}
                items.append({**r, "subproject": sub,
                              "short": "⚠️名册外"})
    else:                                          # 回退:无名册 → 纯关联WS 扫(v8.174)
        for sub, r, _rm in rm_rows:
            if targets & _ws_nums(r["ws"]):
                items.append({**r, "subproject": sub, "short": ""})

    block, unrecognized = _render_ws_progress(ws_label, items, len(roadmaps), bool(roster))
    dag = _render_ws_dag(roster, ws_label) if roster else None

    # 可启动集 —— 名册里依赖全部完成态、自身待开始的 feature(治「下一个做什么」人肉对照 DAG)。
    # 判定走 _ws_status_bucket 词表(「已交付」等别名同义)· 不再裸子串匹配。
    ready = []
    if roster:
        stat = {}
        for f in roster:
            hit = _pick_bl_row(f, by_bl.get(f["bl"], []), _reg, root) if f["bl"] else None
            stat[f["id"]] = (hit[1]["status"] if hit else "")
        for f in roster:
            own = stat.get(f["id"], "")
            deps_done = all(_ws_status_bucket(stat.get(d, ""))[0] == "已完成"
                            for d in f["deps"] if d in stat)
            if own and _ws_status_bucket(own)[0] == "待开始" and deps_done:
                ready.append({"feature": _ws_short(f["id"], ws_label), "bl": f["bl"]})
        if ready:
            block += "\n▶ **可启动(依赖已齐)**:" + " · ".join(
                f"{r['feature']}({r['bl']})" for r in ready)

    wrote = None
    dag_written = False
    if args.write:
        if not ws_file:
            emit({"verdict": "WARN", "ws": ws_label, "reason": "找不到 WS 文档 · 仅输出 block",
                  "rows": len(items), "block": block, "dag": dag})
            return
        text = ws_file.read_text(encoding="utf-8", errors="replace")
        spliced = _splice_block(text, _WS_PROG_START, _WS_PROG_END, block)
        if spliced is None:
            emit({"verdict": "WARN", "ws": ws_label, "file": str(ws_file.relative_to(root)),
                  "reason": "WS 文档缺 WS-PROGRESS 标记区 · 仅输出 block(按模板加标记后再 --write)",
                  "rows": len(items), "block": block, "dag": dag})
            return
        text = spliced
        if dag:                                    # DAG 块可选 · 有标记才写
            d2 = _splice_block(text, _WS_DAG_START, _WS_DAG_END, dag)
            if d2 is not None:
                text, dag_written = d2, True
        ws_file.write_text(text, encoding="utf-8")
        wrote = str(ws_file.relative_to(root))

    out = {"verdict": "OK", "action": "ws-progress", "ws": ws_label,
           "roadmaps_scanned": len(roadmaps), "roster": len(roster), "rows": len(items),
           "written_to": wrote, "dag_written": dag_written,
           "ready_to_start": ready, "block": block, "dag": dag}
    if unrecognized:
        out["unrecognized_status"] = unrecognized
    if len(ws_cands) > 1:   # 多候选 surface(正本判定见 _find_ws_file 排序规则)
        out["ws_file_candidates"] = [str(p.relative_to(root)) for p in ws_cands]
    emit(out)


# ─── ws-lint:WS 文档最新模板符合性校验（v8.186）─────────────────────
# 治本(实证 AON WS-012):AI 做 feature-planning 写 WS 时抄项目里旧/混合格式 · 无符合性检查 ·
# 只有用户主动问「按最新模板写的么」才发现。lint 对照 templates/workstream.md 硬性形态。

def _lint_ws_doc(text: str) -> list:
    """校验 WS 文档符合最新 templates/workstream.md 形态 → 缺项列表(空 = 符合)。"""
    missing: list = []
    if "TEAMWORK-MACHINE" not in text:
        if re.match(r"^﻿?---\s*\n", text):
            missing.append("机读块是裸 `---` frontmatter · 最新模板要求 `<!-- TEAMWORK-MACHINE -->` "
                           "注释块(v8.174 · 渲染器不裸露成 YAML 墙)")
        else:
            missing.append("缺 `<!-- TEAMWORK-MACHINE -->` 机读块(v8.174)")
    for key in ("ws_id", "status", "ui_panorama", "ui_panorama_confirmed",
                "承接执行线", "affected_subprojects", "features"):
        if not re.search(rf"(?m)^\s*{re.escape(key)}\s*:", text):
            note = "(v8.185 · 涉 UI 用户确认全景标识)" if key == "ui_panorama_confirmed" else ""
            missing.append(f"frontmatter 缺 `{key}`{note}")
    if _WS_PROG_START not in text or _WS_PROG_END not in text:
        missing.append("缺 `WS-PROGRESS:START/END` 标记区(v8.174 · ws-progress 自刷进度块)")
    if _WS_DAG_START not in text or _WS_DAG_END not in text:
        missing.append("缺 `WS-DAG:START/END` 标记区(v8.177 · ws-progress 派生依赖图)")
    return missing



def cmd_external_ingest(args: argparse.Namespace) -> None:
    """v8.226:把「外部评审结果」摄入为标准第三视角产物(external-cross-review/review-<label>.md)。

    信源三模式(实证:评审时 MR 多未创建 · 会话内为主):
    - session(主路径):用户在本 session 跑 /code-review ultra · findings 已在对话 →
      AI 先把 findings 忠实转录到 --input-file · 本命令归一化落盘(frontmatter + 校验)。
    - paste(兜底):用户从别处粘贴 → 同 session 但 origin 标 manual-paste(降级语义)。
    - pr-comments(MR 窗口期增强):gh/glab API 拉取 · 拉取即机器证据(伪造不了)。
    🔴 分层:本命令只做**转录归一层**(确定性);裁决(质疑→确认→裁决 · 进 findings 台账)永远归 PMO。
    """
    feature_dir = Path(args.feature).resolve()
    out_dir = feature_dir / "external-cross-review"
    out_dir.mkdir(parents=True, exist_ok=True)
    label = (args.label or "ultra").strip()
    mode = args.source
    body, origin, extra = "", mode, {}
    if mode == "pr-comments":
        if not args.mr_url:
            emit({"verdict": "FAIL", "action": "external-ingest",
                  "error": "--from pr-comments 需 --mr-url"}); return
        import subprocess as _sp
        if "github.com" in args.mr_url:
            r = _sp.run(["gh", "pr", "view", args.mr_url, "--comments"],
                        capture_output=True, text=True, timeout=60)
        else:
            r = _sp.run(["glab", "mr", "note", "list", args.mr_url],
                        capture_output=True, text=True, timeout=60)
        if r.returncode != 0 or not r.stdout.strip():
            emit({"verdict": "FAIL", "action": "external-ingest",
                  "error": f"PR comments 拉取失败/为空:{(r.stderr or '')[:120]}",
                  "hint": "确认 MR 存在且 gh/glab 已登录 · 或改用 --from session(评审窗口常无 MR)"}); return
        body = r.stdout
        extra = {"source_url": args.mr_url, "fetch_evidence": "cli-fetch(机器证据)"}
    else:
        if not args.input_file or not Path(args.input_file).is_file():
            emit({"verdict": "FAIL", "action": "external-ingest",
                  "error": "--from session/paste 需 --input-file <AI 已转录的 findings 文件>"}); return
        body = Path(args.input_file).read_text(encoding="utf-8", errors="replace")
        origin = "in-session" if mode == "session" else "manual-paste(降级 · 无机器证据)"
    if len(body.strip()) < 40:
        emit({"verdict": "FAIL", "action": "external-ingest",
              "error": "内容过短(<40 字)· 不像有效评审结果"}); return
    out = out_dir / f"review-{label}.md"
    fm = (f"---\nreview_via: ultra-ingest\norigin: {origin}\nlabel: {label}\n"
          f"heterogeneous: multi-agent-pipeline\ningested_at: \"{now_iso()}\"\n"
          + "".join(f"{k}: {v}\n" for k, v in extra.items()) + "---\n\n")
    out.write_text(fm + body.strip() + "\n", encoding="utf-8")
    emit({"verdict": "OK", "action": "external-ingest", "artifact": str(out),
          "origin": origin, "chars": len(body),
          "next_action_brief": ("🔴 转录已落盘(原料层)· PMO 现在走**裁决管线**:逐条 质疑→确认→裁决"
                                "(confirmed/rejected/deferred 带实证)→ 裁决结果进 REVIEW.md findings 台账 · "
                                "ultra 也会 false positive · 盲采仍是反模式(§12)")})


def cmd_ledger_migrate(args: argparse.Namespace) -> None:
    """PROCESS-LEDGER 旧 schema 迁移(幂等)· 核心单源 _v8_engine.migrate_process_ledger。

    表头/分隔行升级 + 旧数据行末尾补 `—` 到表头宽 ——「旧行是有效前缀不动」的旧设计
    被消费项目实证打破(aon-core 68/135 行 · supersdk 28/46 行停在 10 列 · 按列索引
    解析静默错位)。内容前缀逐字不动 · 只补不裁。
    """
    root = _git_toplevel(Path.cwd()) or Path.cwd()
    led = None
    feat = getattr(args, "feature", None)
    if feat:
        node = Path(feat).resolve()
        for d in [node, *node.parents]:
            cand = d / "project-specs" / "PROCESS-LEDGER.md"
            if cand.is_file():
                led = cand
                break
            if (d / ".git").exists():
                break
    if led is None:
        cand = root / "project-specs" / "PROCESS-LEDGER.md"
        led = cand if cand.is_file() else None
    if led is None:
        emit({"verdict": "SKIP", "action": "ledger-migrate",
              "reason": "未找到 project-specs/PROCESS-LEDGER.md(尚未建台账 → 首行按模板创建即最新)"})
        return
    from _v8_engine import migrate_process_ledger
    res = migrate_process_ledger(led, Path(__file__).resolve().parent.parent)
    try:
        rel = str(led.relative_to(root))
    except ValueError:
        rel = str(led)
    if res["status"] == "skip":
        reason = {"no_canonical_header": "读不到 templates/process-ledger.md canonical 表头",
                  "no_header_row": "台账无 `| Feature |` 表头行(空表 / 非标准)· 首次采写按模板即最新",
                  }.get(res["reason"], res["reason"])
        emit({"verdict": "SKIP", "action": "ledger-migrate", "file": rel, "reason": reason})
        return
    if res["status"] == "error":
        emit({"verdict": "FAIL", "action": "ledger-migrate", "file": rel, "error": res["reason"]})
        return
    emit({"verdict": "OK", "action": "ledger-migrate", "file": rel,
          "migrated": res["changed"], "old_cols": res["old_cols"], "new_cols": res["new_cols"],
          "padded_rows": res["padded_rows"],
          "hint": ("表头/旧行已对齐最新 schema(旧行末尾补 — = 早于该指标 · 内容前缀未动)"
                   if res["changed"] else "表头与全部行已是最新 schema · no-op")})


def cmd_ws_lint(args: argparse.Namespace) -> None:
    """v8.186:校验 WS 文档符合最新模板形态(治 AI 抄项目旧 WS · 无符合性检查)。"""
    root = _git_toplevel(Path.cwd()) or Path.cwd()
    raw = (getattr(args, "ws", None) or "").strip()
    if not raw and getattr(args, "feature", None):
        resolved = _resolve_ws_from_feature(Path(args.feature), root)
        if resolved:
            raw = resolved
    bare = re.fullmatch(r"0*(\d+)", raw) if raw else None
    targets = _ws_nums(raw) or ({int(bare.group(1))} if bare else set())
    if not targets:
        emit({"verdict": "FAIL", "reason": "需 --ws <编号> 或 --feature <路径>(抽不出 WS 编号)"})
        return
    ws_label = "WS-%02d" % min(targets)
    ws_file, _ws_cands = _find_ws_file(root, ws_label)
    if not ws_file:
        emit({"verdict": "FAIL", "ws": ws_label, "reason": f"找不到 {ws_label} 文档"})
        return
    ws_text = ws_file.read_text(encoding="utf-8", errors="replace")
    missing = _lint_ws_doc(ws_text)
    granularity_warnings: list[str] = []
    # v8.197:执行线存在性(愿景层→WS taxonomy 校验)—— WS 承接的 Line 必须在业务架构「执行线列表」
    # 存在 · 否则是幽灵 Line(反查「某线下有哪些 WS」会断)。无业务架构文档 → skip(非所有项目有)。
    # v8.239:调研深度信号 —— features[].current_state 缺失/仍是模板占位 = 拆解未 grounded 实际代码
    _mb = re.search(r"<!--\s*TEAMWORK-MACHINE.*?-->", ws_text, re.S)
    if _mb:
        _blk = _mb.group(0)
        # v8.248:只数 features: 段内的条目 —— risks[] 等列表同用 `- id:` 写法(模板自带)·
        # 全块计数会把 risk 数成 feature(实证:6 feature + 4 risk → 误报「缺失 6/10」)。
        _feat_m = re.search(r"(?ms)^features\s*:[^\n]*\n(.*?)(?=^\S|\Z)", _blk)
        _feat_blk = _feat_m.group(1) if _feat_m else ""
        _n_feat = len(re.findall(r"(?m)^\s*-\s*id\s*:", _feat_blk))
        _cs = re.findall(r"(?m)^\s*current_state\s*:\s*(.+)$", _feat_blk)
        _placeholder = [c for c in _cs if ("<" in c or c.strip().strip('"').strip("'") in ("...", "", "…"))]
        if _n_feat and len(_cs) < _n_feat:
            missing.append(f"features[].current_state 缺失({len(_cs)}/{_n_feat})—— 拆解必须 grounded 实际代码调研(每 BL 记已有/真缺口+来源文件 · 详 feature-planning Step 1)")
        if _placeholder:
            missing.append(f"current_state 含模板占位 {len(_placeholder)} 处(『<...>』/『...』)—— 调研浅信号 · 必由实读代码填并附来源文件")
        # v8.292:粒度反压物化(WARN 非 FAIL —— 拆得对不对是判断题 · 机器只负责把问题摆到台面)
        if _n_feat > 6:
            granularity_warnings.append(
                f"{_n_feat} 个 BL(> 6)—— 🔴 **默认合并 · 拆分是例外**:逐个说得出「为什么这两件"
                "不能一起交付」吗?**不按评审面拆**(代码在不同子项目 / 前后端分属 / 改动面大不好评审"
                "都不是理由 —— 横切出来的件各自不能独立上线)。薄承接件并回宿主件 · 含金量悬殊 = 强合并信号。"
                "详 docs/feature-planning.md Step 5.7 边界判据")
    ws_lines = {re.sub(r"\s+", "", x) for x in re.findall(r"(?m)^\s*-\s*(Line\s*\d+)", ws_text)}
    if ws_lines:
        arch = next(iter(root.glob("product-overview/*业务架构*.md")), None)
        if arch:
            arch_lines = {re.sub(r"\s+", "", x) for x in
                          re.findall(r"Line\s*\d+", arch.read_text(encoding="utf-8", errors="replace"))}
            ghost = sorted(ws_lines - arch_lines)
            if ghost:
                missing.append(f"承接执行线含业务架构不存在的 {ghost}(幽灵 Line · "
                               f"对照 {arch.name} 执行线列表 · 新线先在业务架构登记)")
    emit({
        "verdict": "OK" if not missing else "NONCONFORMANT",
        "action": "ws-lint", "ws": ws_label,
        "file": str(ws_file.relative_to(root)),
        "conformant": not missing, "missing": missing,
        **({"granularity_warnings": granularity_warnings} if granularity_warnings else {}),
        "hint": ("✅ 符合最新 templates/workstream.md"
                 if not missing else
                 "🔴 不符合最新模板 —— **别抄项目里旧 WS** · 照 {SKILL_ROOT}/templates/workstream.md "
                 f"补齐上述缺项 · 再跑 `state.py ws-progress --ws {ws_label} --write` 填进度/DAG 块"),
    })


# ─── test-baseline:预存在失败注册表 + 差分（v8.178）──────────────────
# 治本(audit ×8):brownfield 共享套件预存在失败 · 每 feature 重复 stash-baseline 甄别。
# project-specs/test-baseline.md 登记成项目级单源 · test/dev gate 差分(0 新增 → 红 base 放行)。

def cmd_test_baseline(args: argparse.Namespace) -> None:
    """v8.178:维护/查询 project-specs/test-baseline.md + 当前失败集差分。"""
    from _v8_stage_specs import _read_test_baseline, _find_specs_root  # noqa
    feature = getattr(args, "feature", None)

    if args.action == "list":
        ids = _read_test_baseline(feature)
        emit({"verdict": "OK", "action": "list", "count": len(ids), "baseline": sorted(ids)})
        return

    if args.action == "diff":
        registered = _read_test_baseline(feature)
        current = [c.strip() for c in re.split(r"[,\n]", args.current or "") if c.strip()]
        if not current:
            emit({"verdict": "FAIL", "reason": "--diff 需 --current '<逗号/换行分隔的当前失败 id>'"})
            return
        new = [c for c in current if c not in registered]
        excluded = [c for c in current if c in registered]
        stale = [c for c in sorted(registered) if c not in current]
        emit({"verdict": "OK" if not new else "NEW_FAILURES", "action": "diff",
              "new": new, "excluded": excluded, "stale_registered": stale,
              "hint": ("new=[] → 红 base 可放行(test-complete/dev-complete 同传 --current-failures);"
                       "new 非空 → 回归(修)或新预存在(核实后 --add 登记原因);"
                       "stale_registered = 基线里已不再失败的(可删)")})
        return

    # add
    if not args.test_id or not args.reason:
        emit({"verdict": "FAIL", "reason": "--add 需 --test-id + --reason(预存在失败必须写原因/清账计划)"})
        return
    root = (_find_specs_root(feature) if feature else None) or _git_toplevel(Path.cwd()) or Path.cwd()
    f = root / "project-specs" / "test-baseline.md"
    if not f.is_file():
        f.parent.mkdir(parents=True, exist_ok=True)
        tmpl = Path(__file__).resolve().parent.parent / "templates" / "test-baseline.md"
        f.write_text(tmpl.read_text(encoding="utf-8") if tmpl.is_file()
                     else "# 测试基线失败集\n\n| 失败用例 (id) | 套件/命令 | 基线 commit | 原因（谁的债 · 何时清） | 登记于 |\n|---|---|---|---|---|\n",
                     encoding="utf-8")
    with f.open("a", encoding="utf-8") as fh:
        fh.write(f"| {args.test_id} | {args.suite or '—'} | {args.base_commit or '—'} "
                 f"| {args.reason} | {now_iso()[:10]} |\n")
    emit({"verdict": "OK", "action": "add", "test_id": args.test_id,
          "file": str(f), "baseline_count": len(_read_test_baseline(str(f)))})


# ─── init-feature / recover (v7.3.10+P0-148) ──────────────────────────


DEFAULT_INITIAL_STAGE = {
    "Feature": "goal",
    "Bug": "diagnose",   # v8.107:Bug 先 diagnose(根因细查+修复方案确认)再 dev
    "Micro": "execute",   # v8.250:micro 首 stage = execute(零门禁自由执行)· 去 dev
    "Tiny": "dev",        # v8.342:tiny 无 goal/blueprint · 规格 = dev brief 理解卡
    "Floor": "dev",       # v8.343:floor 同 tiny 入口 · 差别在评审点全 0(dev → ship)
}


def _parse_workspace_registry(ws_path: Path) -> dict:
    """解析 teamwork-space.md 子项目清单表 → {prefix: docs_root}。

    按列名(缩写 / docs_root)定位 · 容忍列序差异 / 多余列。解析不出返回 {}。
    """
    try:
        lines = ws_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    reg: dict = {}
    abbr_i = None
    root_i = None
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            abbr_i = None
            root_i = None
            continue
        cells = [c.strip().strip("`").strip() for c in s.strip("|").split("|")]
        if abbr_i is None:
            if any("缩写" in c for c in cells) and any("docs_root" in c for c in cells):
                for i, c in enumerate(cells):
                    if "缩写" in c:
                        abbr_i = i
                    if "docs_root" in c:
                        root_i = i
            continue
        if cells and all(set(c) <= set("-: ") for c in cells if c):
            continue  # 分隔行 |---|---|
        if abbr_i < len(cells) and root_i < len(cells):
            abbr = cells[abbr_i]
            root = cells[root_i].rstrip("/")
            if abbr and root:
                reg[abbr] = root
    return reg


def _git_toplevel(start: Path):
    """git rev-parse --show-toplevel · 失败返 None。"""
    try:
        r = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _check_artifact_routing(feature_dir: Path, feature_id: str) -> dict:
    """校验 Feature artifact 路径 + ID 前缀 落在 teamwork-space.md 注册的 docs_root 下。

    治本 F049 case:代码在 apps/partner/(属 PTR)· artifact 却建成 SVC-PLATFORM
    前缀 + 落在仓库根 docs/features/ · 错前缀 + 错路径无任何拦截照样 PASS。
    docs_root 是 teamwork-space.md 路由权威(conventions.md §8)。

    返回 {verdict: PASS|FAIL|WARN|SKIP, ...}。
    """
    import re as _re
    if os.environ.get("TEAMWORK_BYPASS_ROUTING_CHECK") == "1":
        return {"verdict": "SKIP", "reason": "TEAMWORK_BYPASS_ROUTING_CHECK=1"}
    top = _git_toplevel(Path.cwd())
    if not top:
        return {"verdict": "SKIP", "reason": "cwd 不在 git 仓库"}
    ws = top / "teamwork-space.md"
    if not ws.exists():
        ws = top / "teamwork_space.md"  # 容错 legacy 下划线名
    if not ws.exists():
        return {"verdict": "SKIP", "reason": "无 teamwork-space.md(单项目仓库)"}
    reg = _parse_workspace_registry(ws)
    if not reg:
        return {"verdict": "SKIP", "reason": "teamwork-space.md 子项目清单解析为空"}
    m = _re.match(r"^(.+?)-[FBM]\d+", feature_id)
    if not m:
        return {"verdict": "SKIP", "reason": f"feature_id {feature_id!r} 抽不出前缀"}
    prefix = m.group(1)
    if prefix not in reg:
        return {
            "verdict": "WARN",
            "prefix": prefix,
            "known_prefixes": sorted(reg),
            "message": (
                f"前缀 {prefix!r} 未在 teamwork-space.md 子项目清单注册 · "
                f"新子项目请先注册 · 或前缀拼错"
            ),
        }
    expected = reg[prefix].rstrip("/")
    try:
        actual = str(feature_dir.resolve().relative_to(top.resolve()).parent)
    except ValueError:
        return {"verdict": "SKIP", "reason": "feature 路径不在仓库内"}
    actual = actual.rstrip("/")
    if actual != expected:
        return {
            "verdict": "FAIL",
            "prefix": prefix,
            "expected_docs_root": expected,
            "actual_path": actual,
        }
    return {"verdict": "PASS", "prefix": prefix, "docs_root": expected}


# ─── prepare-check audit 门禁(v8.14)─────────────────────────────────────
# 治本 PTR-F054 case:AI 跳过 prepare 子流程 直接 init-feature → 用错 prefix /
# 选错 features_root / 漏 ID 冲突预检。已物化的 prepare-check 命令不被调用 =
# 等同没物化。
#
# 设计:
# - prepare-check 每次跑成功 → 追写 jsonl audit(~/.teamwork/prepare_check_audit.jsonl)
# - init-feature 校验:从 --feature-id 抽 prefix → 扫 audit jsonl 近 PREPARE_CHECK_WINDOW_SEC
#   秒内匹配该 prefix 的 record → 命中 PASS / 未命中 BLOCKED
# - 旁路:TEAMWORK_BYPASS_PREPARE_CHECK=1(仅 debug / migration / 极端场景)
# - 测试 override:TEAMWORK_PREPARE_AUDIT_PATH=<path> 覆盖 audit 文件路径
#
# 为什么 60min:Feature prepare → 用户思考拍板 → init-feature 通常 5-30min ·
# 60min 给 buffer · 防"几天前跑过一次就一直绕过"

PREPARE_CHECK_AUDIT_ENV = "TEAMWORK_PREPARE_AUDIT_PATH"
PREPARE_CHECK_BYPASS_ENV = "TEAMWORK_BYPASS_PREPARE_CHECK"
PREPARE_CHECK_WINDOW_SEC = 3600  # 60 min


def _prepare_audit_path() -> Path:
    """audit jsonl 落位 · 用户级跨项目(主工作区 prepare → worktree init-feature 可通)。

    覆盖路径:TEAMWORK_PREPARE_AUDIT_PATH=<path>(测试用)。
    """
    override = os.environ.get(PREPARE_CHECK_AUDIT_ENV)
    if override:
        return Path(override)
    return Path.home() / ".teamwork" / "prepare_check_audit.jsonl"


def _write_prepare_audit(record: dict) -> None:
    """append-only jsonl 写 · 父目录自动创建 · 失败不阻塞 prepare-check 主输出。"""
    try:
        p = _prepare_audit_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        # audit 写失败不致命(jsonl 是兜底审计 · 主功能不依赖它)
        pass


def _parse_iso_utc(s: str):
    """容忍 'Z' 后缀的 ISO 8601 解析 · 失败返 None。"""
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _check_prepare_audit(feature_id: str) -> dict:
    """从 feature_id 抽 prefix · 扫 audit jsonl · 找近 PREPARE_CHECK_WINDOW_SEC 内匹配 record。

    匹配分两级(并行多 feature 场景可辨"prepare 是否为**本** feature 跑过"):
    - exact:record.next_available_id_stem 是本 feature_id 的号段前缀(stem 本身或 stem-)
    - prefix_only:仅项目前缀命中(窗内无精确命中)· 仍放行 · init-feature emit WARN + concerns 留痕

    返回 {verdict: PASS|FAIL|SKIP, match: exact|prefix_only, ...}。SKIP = bypass 环境变量 / 抽不出 prefix。
    """
    if os.environ.get(PREPARE_CHECK_BYPASS_ENV) == "1":
        return {"verdict": "SKIP", "reason": f"{PREPARE_CHECK_BYPASS_ENV}=1"}
    m = re.match(r"^(.+?)-[FBM]\d+", feature_id)
    if not m:
        return {"verdict": "SKIP", "reason": f"feature_id {feature_id!r} 抽不出前缀"}
    prefix = m.group(1)
    audit_path = _prepare_audit_path()
    if not audit_path.exists():
        return {
            "verdict": "FAIL",
            "prefix": prefix,
            "audit_path": str(audit_path),
            "reason": "audit 文件不存在 · 未跑过 prepare-check",
        }
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - PREPARE_CHECK_WINDOW_SEC
    try:
        lines = audit_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return {"verdict": "SKIP", "reason": f"audit 读失败: {e}"}
    prefix_only_hit: Optional[dict] = None  # 窗内最新的 prefix-only 命中
    # 倒序扫(append-only · 最新在末尾)
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("feature_id_prefix") != prefix:
            continue
        ts = _parse_iso_utc(rec.get("timestamp", ""))
        if ts is None:
            continue
        if ts.timestamp() < cutoff:
            if prefix_only_hit is not None:
                break  # 已有窗内命中 · 更老的只会更旧
            # 倒序找到的最新匹配也过期 = 全部过期
            return {
                "verdict": "FAIL",
                "prefix": prefix,
                "audit_path": str(audit_path),
                "latest_match_age_sec": int(now.timestamp() - ts.timestamp()),
                "window_sec": PREPARE_CHECK_WINDOW_SEC,
                "reason": "最近一次匹配 prepare-check 超出 60min 窗口",
            }
        stem = (rec.get("next_available_id_stem") or "").strip()
        if stem and (feature_id == stem or feature_id.startswith(stem + "-")):
            # 精确命中:prepare-check 分配的号段即本 feature 的号段
            # 整条 audit record(含 admission_judgment / consistency / recommended_flow_type)
            # 供 init-feature 跨字段校验(如 audit consistency=MISMATCH vs init --flow-type)
            return {
                "verdict": "PASS",
                "match": "exact",
                "prefix": prefix,
                "matched_stem": stem,
                "match_timestamp": rec.get("timestamp"),
                "age_sec": int(now.timestamp() - ts.timestamp()),
                "audit_record": rec,
            }
        if prefix_only_hit is None:
            prefix_only_hit = {
                "verdict": "PASS",
                "match": "prefix_only",
                "prefix": prefix,
                "matched_stem": stem or None,
                "match_timestamp": rec.get("timestamp"),
                "age_sec": int(now.timestamp() - ts.timestamp()),
                "audit_record": rec,
            }
    if prefix_only_hit is not None:
        return prefix_only_hit
    return {
        "verdict": "FAIL",
        "prefix": prefix,
        "audit_path": str(audit_path),
        "reason": f"audit 中无匹配 prefix={prefix!r} 的 record",
    }


YOLO_BRANCH_PREFIX = "yolo/"


def _is_yolo_branch(branch: str) -> bool:
    """是否是 yolo 隔离分支(v8.349 用户拍板:yolo 必须先合入 `yolo/` 开头的目标分支)。

    🔴 隔离分支不是「多一道墙」—— 它是**待确认项的落脚处**:yolo 期间没人看,
    识别到的风险只能写进文档(实证事故里就是这么丢的);有了 yolo/* 这一段,
    每次自动合入都往 YOLO-PENDING 记一笔,等它合进真 target 时人一次性拍板。
    """
    return bool(branch) and branch.strip().lower().startswith(YOLO_BRANCH_PREFIX)


def _is_main_branch(branch: str, repo_cwd: Optional[str] = None) -> bool:
    """branch 是否是主分支(yolo 硬约束:自动 merge 不得直接进 main)。
    判定:名字 ∈ {main, master} · 或 == 远端默认分支(origin/HEAD 指向)。"""
    if not branch:
        return False
    b = branch.strip().lower()
    if b in ("main", "master"):
        return True
    try:
        r = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=repo_cwd, capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            default = r.stdout.strip().rsplit("/", 1)[-1].lower()  # refs/remotes/origin/main → main
            if default and default == b:
                return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return False


def _check_yolo_preflight(pf: Path) -> tuple[bool, str]:
    """v8.179:校验 YOLO-PREFLIGHT.md 存在 + 已填(核心决策 + 用户确认 · 哨兵已删)。

    yolo 零暂停点 → 意图保真膜 front-load:深入调研 + 核心决策逐条用户确认后才进自主。
    哨兵 `YOLO-PREFLIGHT-UNFILLED` 必须删(强制真填 · 不是建个空模板)。
    """
    if not pf.is_file():
        return False, "YOLO-PREFLIGHT.md 不存在(yolo 不得裸启动 · 先深入调研 + 核心决策用户确认)"
    text = pf.read_text(encoding="utf-8", errors="replace")
    if "YOLO-PREFLIGHT-UNFILLED" in text:
        return False, "YOLO-PREFLIGHT.md 仍含未完成哨兵(深入调研 + 核心决策用户确认后删该哨兵行)"
    if "核心" not in text or ("用户确认" not in text and "用户拍板" not in text):
        return False, "YOLO-PREFLIGHT.md 缺『核心决策』或『用户确认』段(按模板补全)"
    return True, ""


def cmd_init_feature(args: argparse.Namespace) -> None:
    """Create initial state.json · 替代手工 Write。"""
    # Feature Planning / 问题排查 不进状态机 · 拒绝
    if args.flow_type in NON_STATE_MACHINE_FLOWS:
        die(2, json.dumps({
            "verdict": "FAIL",
            "error": f"flow_type='{args.flow_type}' 不进状态机 · init-feature 拒绝",
            "hint": (
                f"{args.flow_type} 流程由 PMO 主对话直接执行 · 不创建 state.json。"
                if args.flow_type == "Feature Planning"
                else "问题排查由 PMO 直接 grep/Read 答 · 不创建 state.json。"
            ),
            "spec": (
                "docs/feature-planning.md"
                if args.flow_type == "Feature Planning"
                else "FLOWS.md § 问题排查"
            ),
        }, ensure_ascii=False, indent=2))

    # v8.65:yolo 可携带 merge_target 分支(--yolo <branch>)· 覆盖 --merge-target / localconfig 默认
    # nargs='?':args.yolo = None(未传)/ True(--yolo 无值)/ str(--yolo <branch>)
    yolo_branch = args.yolo if isinstance(args.yolo, str) and args.yolo.strip() else None
    yolo_enabled = args.yolo is not None
    merge_target = yolo_branch or args.merge_target
    if not merge_target:
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": "缺 merge_target",
            "hint": ("传 --merge-target <branch> · 或 yolo 用 --yolo <branch>"
                     "(该分支即本需求 merge_target · 覆盖 localconfig 默认)"),
        }, ensure_ascii=False, indent=2))

    feature_dir = Path(args.feature)
    state_file = feature_dir / "state.json"

    # v8.14:prepare-check audit 门禁(治本 PTR-F054 case · AI 跳 prepare 直裸跑 init-feature)
    # prepare-check 已物化但被绕过 = 等同没物化 · 这里加下游硬墙
    audit = _check_prepare_audit(args.feature_id)
    if audit["verdict"] == "FAIL":
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (
                f"prepare-check audit 缺失或过期 · 无法证明 prepare 子流程已跑完 "
                f"(prefix={audit.get('prefix')!r})"
            ),
            "audit_detail": audit,
            "hint": (
                "先跑 prepare-check · 再 init-feature:\n"
                f"  python3 {{SKILL_ROOT}}/tools/state.py prepare-check "
                f"--feature-id-prefix {audit.get('prefix')} "
                f"--features-root <绝对路径> --flow-type {args.flow_type}\n"
                "→ prepare-check 写 audit jsonl · init-feature 60min 窗内复跑即放行。\n"
                "若已跑过 prepare-check 仍 FAIL:可能①超 60min 窗 → 重跑一次;"
                "②prefix 拼错 → 对齐 prepare-check 时的 --feature-id-prefix。"
            ),
            "rule": "v8.14 prepare-check audit 门禁 · 治本 PTR-F054 AI 跳 prepare case",
            "bypass": f"调试 / migration · export {PREPARE_CHECK_BYPASS_ENV}=1",
            "spec": "docs/prepare.md § 0",
        }, ensure_ascii=False, indent=2))

    if yolo_enabled and _is_main_branch(merge_target):
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (
                f"yolo 模式禁止 merge_target 是主分支({merge_target!r})—— "
                f"yolo 会**无人 review 自动 merge MR** · 不得直接合进 main/master/远端默认分支"
            ),
            "hint": (
                "yolo 必须合到**非主分支**(如 dev / staging / integration)· 再由人工 gate "
                "该分支 → main 的提升。改 --merge-target <非主分支> 重跑;若确需合 main · "
                "别用 --yolo(改 --auto-mode · 保留 MR merge 人工 stop)。"
            ),
            "rule": "v8.63 yolo 硬约束 · 自动 merge 不进 main(防 AI 错误/幻觉特性直接进 main)",
        }, ensure_ascii=False, indent=2))
    # v8.349(用户拍板:「yolo 必须先合入目标 yolo 分支 · yolo/ 开头的」)——
    # 把 v8.63 的「不得是主分支」收紧成**必须是 yolo/ 前缀的隔离分支**。
    # why:v8.63 只挡了 main,但 yolo 照样能直接自动合进 staging —— 而 staging 通常就是
    # 生产前的最后一站(实证事故:协议 v1.0 强制 header,存量调用方全 400、线上请求归零;
    # 那条 Bug 走的正是 yolo/auto,diagnose 方案确认被自动跳过)。
    # 隔离分支的作用不是多一道墙,是**给「无人值守期间攒下的待确认项」一个落脚处**:
    # 每个 feature 合进 yolo/* 时记一笔,等 yolo/* → 真 target 时一次性拍板(见 YOLO-PENDING)。
    if yolo_enabled and not _is_yolo_branch(merge_target):
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (f"yolo 的 merge_target 必须是 `yolo/` 前缀的隔离分支 · got {merge_target!r}"),
            "hint": (
                "yolo = 无人值守自动 merge · **不得直接合进任何常规集成分支**(staging 也不行 —— "
                "它常是生产前最后一站)。改成:\n"
                f"  --yolo yolo/{(merge_target or 'integration').strip().lstrip('/') or 'integration'}"
                "  (该分支即本需求 merge_target)\n"
                "🔴 两段式:① feature → `yolo/*`(自动 · 每次合入把**待确认项**记进 YOLO-PENDING)"
                "② `yolo/*` → 真 target(**人工** · 一次性确认攒下的全部待确认项)。\n"
                "不想要隔离分支 → 别用 --yolo(改 --auto-mode · 保留 MR merge 人工 stop)。"),
            "rule": "v8.349 yolo 两段式(用户拍板)· 隔离分支承载「无人值守期的待确认项」",
        }, ensure_ascii=False, indent=2))


    # v8.179:yolo 预研门(硬门)—— 正式自主前必产 YOLO-PREFLIGHT.md(深入调研 + 核心决策用户确认)。
    # yolo 零暂停点 → 意图保真膜必 front-load · 防裸启动直接闷头跑偏(无人值守 · 错了没机会中途纠)。
    if yolo_enabled:
        pf_ok, pf_reason = _check_yolo_preflight(feature_dir / "YOLO-PREFLIGHT.md")
        if not pf_ok:
            die(2, json.dumps({
                "verdict": "FAIL",
                "action": "init-feature",
                "error": f"yolo 预研门未过:{pf_reason}",
                "hint": (
                    "yolo 正式自主前必须:① 深入调研真实代码(任务实质 / 范围 / 未知 / 风险)"
                    " ② 提炼核心重要决策 ③ 和用户**逐条确认** → 落 "
                    f"{feature_dir}/YOLO-PREFLIGHT.md(模板 {{SKILL_ROOT}}/templates/yolo-preflight.md)"
                    " · 填完删哨兵行 · 再重跑 init-feature --yolo。\n"
                    "理由:yolo 启动后零暂停点 · 意图 / 关键取舍错了没机会中途纠 → 必须跑前确认。"
                ),
                "rule": "v8.179 yolo 预研门 · front-load 意图保真膜(无人值守 · 跑前确认核心决策)",
                "bypass": "确无核心决策 · 仍须产出 YOLO-PREFLIGHT.md 写明「无核心决策 · 已确认」",
            }, ensure_ascii=False, indent=2))

    # v8.15:admission consistency 校验(治本 F001 GCP gateway case · AI 选错 flow_type)
    # audit 里若 consistency=MISMATCH(AI judgment 推荐 flow_type ≠ init --flow-type)→ WARN
    # 不 BLOCK(R0 兜底:可能合理例外 · 给 AI/用户数据 + 警告 · 决策权留人)
    admission_warning = None
    rec = audit.get("audit_record") or {}
    audit_consistency = rec.get("consistency")
    audit_recommended = rec.get("recommended_flow_type")
    if audit_consistency == "MISMATCH" and audit_recommended:
        admission_warning = (
            f"[WARN] admission MISMATCH:prepare-check 时 AI judgment 推荐 "
            f"flow_type={audit_recommended!r} · 但 init-feature --flow-type={args.flow_type!r} · "
            f"audit at {rec.get('timestamp')} · 若 admission_judgment.ai_rationale "
            f"信号强(如「方向级业务变更」「跨独立 git 仓库」)· 建议取消本次 init · "
            f"用 --flow-type={audit_recommended!r} 重走 prepare-check + Feature Planning 或对应流程"
        )

    # prepare-check 仅 prefix 命中(非本 feature 的精确号段)→ 放行但 WARN 留痕
    # (并行多 feature 场景:同 prefix 的另一 feature 刚跑过 prepare 也会命中 · 显式可见)
    prepare_match_warning = None
    if audit.get("verdict") == "PASS" and audit.get("match") == "prefix_only":
        prepare_match_warning = (
            f"[WARN] prepare-check audit 仅 prefix 命中:窗内最近 record stem="
            f"{audit.get('matched_stem')!r} ≠ 本次 feature_id={args.feature_id!r} · "
            f"并行多 feature 场景请确认 prepare 确为本 feature 跑过 · "
            f"必要时重跑 prepare-check 取本 feature 的 next_available_id_stem"
        )

    # v8.x:artifact 路由物化校验(治本 F049 子项目错位 case)
    # teamwork-space.md docs_root 是路由权威 · 校验 --feature 路径 + ID 前缀一致
    routing = _check_artifact_routing(feature_dir, args.feature_id)
    if routing["verdict"] == "FAIL":
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (
                f"artifact 路径违背 teamwork-space.md 路由权威:前缀 {routing['prefix']} "
                f"注册 docs_root={routing['expected_docs_root']!r} · "
                f"但 --feature 落在 {routing['actual_path']!r}"
            ),
            "hint": (
                "二选一修正:\n"
                f"  ① 路径错 → --feature 改到 {routing['expected_docs_root']}/{feature_dir.name}\n"
                "  ② 前缀错 → 该改动属哪个子项目?用该子项目注册的前缀 + docs_root "
                "(代码在 apps/partner/ → PTR · services/ → SVC-* · 查 teamwork-space.md 子项目清单)"
            ),
            "rule": "conventions.md §8 docs_root 路由权威 · v8.x 物化拦截 · 治本 F049 case",
            "bypass": "确属特例:export TEAMWORK_BYPASS_ROUTING_CHECK=1",
        }, ensure_ascii=False, indent=2))

    # v8.79:撞号硬校验(R0 物化 · 治本 AON 13 组实测撞号 · 分布式 max+1 race 兜底)
    # 目标 {PREFIX}-{字母}{number} 已被**另一**兄弟目录占用 → FAIL(同 clone 内兜;跨 clone 靠 utc 策略)
    _collision = _detect_id_collision(feature_dir, args.feature_id)
    if _collision and not args.force:
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (
                f"artifact 号段撞号:{_collision['number_id']} 已被现存目录 "
                f"{_collision['existing']!r} 占用 · 与本次 {feature_dir.name!r} 同号"
            ),
            "hint": (
                "另一 feature 已占该号段(多 agent/多机并行 race)· 换号重建:\n"
                "  重跑 prepare-check 取新 next_available_id_stem · 改 --feature / --feature-id 后再 init。\n"
                "  (utc 时间戳策略:重跑即得新秒级号 · sequential 策略:取 max+1 避让 existing_ids)"
            ),
            "collision": _collision,
            "rule": "v8.79 撞号硬校验 · 可枚举规则进脚本(R0)· 治本分布式 max+1 race",
            "bypass": "确属同号续作(罕见):--force 跳过撞号校验",
        }, ensure_ascii=False, indent=2))

    if state_file.exists() and not args.force:
        die(2, json.dumps({
            "verdict": "FAIL",
            "error": f"state.json already exists: {state_file}",
            "hint": "Use --force to overwrite (自动 backup .bak.<ts>)",
        }, ensure_ascii=False, indent=2))
    # 注:--force 的 backup rename 延迟到全部校验通过后、写入前那一刻执行 ——
    # 防「先移走旧 state.json → 后续 cwd/worktree 校验 die → 旧状态已被毁」。

    feature_dir.mkdir(parents=True, exist_ok=True)
    # v8.220/222:legacy flow_type 先归一(Micro→Feature+micro)·
    # 查表用内部键(归一后直接查会让 micro 错拿 goal)
    _pub_flow, _preset = normalize_flow(args.flow_type, getattr(args, "preset", None))
    args.flow_type = _pub_flow  # 后续逻辑(角色矩阵/emit)统一走归一值

    # v8.343:Feature 一律建 assembly_plan(链的单源)· --dims 是 custom 装配入口
    _plan = None
    if args.flow_type == "Feature":
        _override = None
        raw = getattr(args, "dims", None)
        if raw:
            try:
                _override = json.loads(raw)
            except json.JSONDecodeError as e:
                die(2, json.dumps({
                    "verdict": "FAIL", "action": "init-feature",
                    "error": f"--dims 不是合法 JSON:{e}",
                    "hint": ('例:--dims \'{"verify_depth":"test",'
                             '"review":{"review":["architect","external"]}}\' · '
                             "只传要拧的维度 · 其余沿用档默认"),
                }, ensure_ascii=False, indent=2))
            if not isinstance(_override, dict):
                die(2, json.dumps({
                    "verdict": "FAIL", "action": "init-feature",
                    "error": f"--dims 必须是 JSON object · got {type(_override).__name__}",
                }, ensure_ascii=False, indent=2))
        _plan = build_assembly_plan(_preset, _override,
                                    set_at=("goal" if _preset in ("lite", "medium", "full")
                                            else "prepare"))
        _bad = validate_dims(_plan["dims"])
        if _bad:
            die(2, json.dumps({
                "verdict": "FAIL", "action": "init-feature",
                "error": "装配维度组合不连贯 · 拒绝创建",
                "violations": _bad,
                "hint": ("维度矩阵与一致性约束见 stages/goal-stage.md § 链装配。"
                         "N/A ≠ 0 路:0 路是在链上不派 · N/A 是该 stage 不在链上。"),
            }, ensure_ascii=False, indent=2))

    initial_stage = args.initial_stage or (
        derive_chain(_plan["dims"])[0] if _plan
        else DEFAULT_INITIAL_STAGE.get(internal_flow_key(args.flow_type, _preset), "goal")
    )

    # 启发式校验：basename 应含 feature_id（防 --feature 传了 slug 而不是完整路径）
    if args.feature_id not in feature_dir.name:
        # 不强阻 · 但 stderr 提示一行警告
        print(
            f"WARNING: --feature basename '{feature_dir.name}' does not contain "
            f"--feature-id '{args.feature_id}' · 确认 --feature 是完整路径（如 "
            f"apps/{{sub_project}}/docs/features/{args.feature_id}）而非仅 feature 名",
            file=sys.stderr,
        )

    state: dict[str, Any] = {
        "feature_id": args.feature_id,
        "bl": getattr(args, "bl", None) or None,  # v8.196:承接的 BL(F↔BL 机读绑定 · 链路最脆一环治本)
        "clarity": getattr(args, "clarity", "normal") or "normal",  # v8.215:明确度 → 评审强度比例化
        "preset": _preset,  # v8.220:Feature 重量档(full/lite/micro)· 链与角色由它决定
        "sub_project": args.sub_project or "",
        "flow_type": args.flow_type,
        "artifact_root": str(feature_dir),  # v7.3.10+P0-149: 单源 · 不再独立 --artifact-root
        # v8.36:host per-feature(治本 SVC-PLATFORM-F054 case · 全局 audit 跨 session 污染)
        # 不传 → None · external-review fallback 读全局 audit(deprecated)+ emit WARN
        "host": args.host or None,
        "host_history": ([{"host": args.host, "at": now_iso(), "source": "init-feature"}]
                          if args.host else []),
        "current_stage": initial_stage,
        "merge_target": merge_target,
        # v8.161:进 dev 那刻由 stage-complete 冻结的 pre-dev HEAD · review-stage external-review
        # 的增量 diff 基线(评本 feature dev 增量 · 非 merge_target...HEAD 累积)。init 占位 None。
        "review_base_commit": None,
        "worktree": {
            "strategy": args.worktree_mode,
            "branch": args.branch,
            "path": args.worktree_path,
            "base_branch": f"origin/{merge_target}",
            "created_at": now_iso(),
        },
        "environment_config": {
            "worktree_mode": args.worktree_mode,
            "branch": args.branch,
            "merge_target": merge_target,
            "base": f"origin/{merge_target}",
            "executed_at": now_iso(),
        },
        # v8.63:yolo implies auto_mode(完全自动是 auto_mode 的超集)· v8.65:yolo_enabled(nargs='?')
        "auto_mode": args.auto_mode or yolo_enabled,
        "yolo": yolo_enabled,
        # 启动期 WARN 留痕:admission MISMATCH / prepare 门禁仅 prefix 命中
        "concerns": [w for w in (admission_warning, prepare_match_warning) if w],
        "review_round": 0,
        "stage_contracts": {},
        "completed_stages": [],
        "created_at": now_iso(),
    }
    # v8.343:计划落库(Feature)· roster 由 plan.dims.review 渲染 —— 单源
    if _plan:
        state["assembly_plan"] = _plan
    # v8.0+P0-9:按 flow_type 填默认 stage_review_roles + adjustments audit list
    try:
        from _v8_engine import build_default_stage_review_roles
        if _plan:
            _chain = set(derive_chain(_plan["dims"]))
            # 流默认 → 计划覆盖 → 链上过滤。计划的 review 只管**随档变化的四个评审点**;
            # test/ui_design/browser_e2e 的 roster 不随档变,沿用流默认(直接整体赋值会抹掉)。
            _roles = {s: list(r) for s, r in
                      build_default_stage_review_roles(args.flow_type, "full").items()
                      if s in _chain}
            for _p, _r in (_plan["dims"].get("review") or {}).items():
                if _p in _chain:
                    _roles[_p] = list(_r)
            # 🔴 链上的评审点即使 0 路也**写键、写空列表**(v8.337「零也显式」的机器版):
            # 不写键 = 修订时想加回来没有落点 · 减税要减在明处、且可逆。
            for _p in REVIEW_POINTS:
                if _p in _chain:
                    _roles.setdefault(_p, [])
            state["stage_review_roles"] = _roles
        else:
            state["stage_review_roles"] = build_default_stage_review_roles(
                args.flow_type, _preset)
        state["stage_review_roles_adjustments"] = []
    except ImportError:
        pass
    # v8.260 fast mode:localconfig `fast_mode: true` → 去掉所有评审环节(默认关)。
    # 快照进 state(mid-feature 改配置不漂移):roster 全清空(roster-aware 门自动放行)·
    # dev 跳 review 直进 test(_dev_transition)· PRD-REVIEW/TECH-REVIEW 不产不查。
    # 🔴 与 yolo 互斥:yolo 无人值守的唯一安全网就是评审 · fast 拆评审 · 不可同用。
    _fast_cfg = _read_fast_mode(feature_dir)
    if _fast_cfg:
        if getattr(args, "yolo", False):
            # v8.262:yolo 忽略 fast(不再互斥报错)—— 无人值守的唯一安全网 = 全量评审 ·
            # fast_mode 静默不生效 · kickoff 记 INFO(用户知情 · 不拦)。
            state.setdefault("concerns", []).append(
                f"{now_iso()} INFO yolo-ignores-fast: localconfig fast_mode=true 被 yolo 忽略"
                "(无人值守安全网=全量评审 · fast 仅有人值守生效)")
        else:
            state["fast_mode"] = True
            # v8.261:留两端 · 各合并单路 —— goal 单路合并冷审(PL+外审关注点合一)·
            # review 单路合并评审(Architect+QA 关注点合一)· blueprint 评审仍去。
            # 「fast」伪角色:收敛协议(verdicts/findings/severity/验证轮)全保留 · 单 agent 兼多帽。
            # v8.305:blueprint 显式写 [] —— 原来靠**键缺失**表达「评审整段去掉」,
            # 而门禁把「缺失」读成「未配置 → 按默认要 external」· 意图必须显式化。
            state["stage_review_roles"] = {"goal": ["fast"], "blueprint": [], "review": ["fast"]}
            state["stage_review_roles_adjustments"] = [{
                "stage": "*", "roles": [], "reason": "fast_mode(localconfig)· goal/review 各留单路合并评审 · 其余评审跳", "adjusted_via": "fast_mode"}]
    # ── v8.0+P0-3:cwd 物化校验(治本 PTR-F033 主 tree 污染 case)──
    # 根因:即使 init-feature 自动建了 worktree · 若 PMO 在主 tree cwd 运行 ·
    # state.json 仍落主 tree · worktree 是空的 · 主 tree 污染依旧。
    # 修复:worktree_mode != off 且 --worktree-path 提供时 · 校验:
    #   - 当前 cwd 必须在 --worktree-path 内
    #   - feature_dir(state.json 落位)必须在 cwd 内(防绝对路径反向落主 tree)
    # 不一致 → FAIL + hint 引导 cd
    cwd_warning = None
    bypass_cwd = os.environ.get("TEAMWORK_BYPASS_CWD_WORKTREE") == "1"
    if not bypass_cwd and args.worktree_mode != "off" and args.worktree_path:
        cwd_real = Path.cwd().resolve()
        wt_real = Path(args.worktree_path).resolve()
        feat_real = Path(args.feature).resolve()
        if wt_real.exists():
            # cwd 必须在 worktree 内
            try:
                cwd_real.relative_to(wt_real)
                cwd_in_wt = True
            except ValueError:
                cwd_in_wt = False
            # feature_dir 必须在 worktree 内(防绝对路径反向落主 tree)
            try:
                feat_real.relative_to(wt_real)
                feat_in_wt = True
            except ValueError:
                feat_in_wt = False

            if not cwd_in_wt or not feat_in_wt:
                die(2, json.dumps({
                    "verdict": "FAIL",
                    "action": "init-feature",
                    "error": "cwd 或 --feature 路径未在 worktree 内 · state.json 会落主 tree(治本 PTR-F033)",
                    "current_cwd": str(cwd_real),
                    "worktree_path": str(wt_real),
                    "feature_path": str(feat_real),
                    "cwd_in_worktree": cwd_in_wt,
                    "feature_in_worktree": feat_in_wt,
                    "hint": (
                        f"先 `cd {wt_real}` · 再用相对路径 `--feature docs/features/...` "
                        f"或确认 --feature 是 worktree 内的绝对路径 · 重跑 init-feature"
                    ),
                    "bypass": "调试场景 export TEAMWORK_BYPASS_CWD_WORKTREE=1",
                }, ensure_ascii=False, indent=2))
        else:
            cwd_warning = (
                f"worktree path {wt_real} 尚不存在 · init-feature 将尝试自动创建 · "
                "建议:先显式 `git worktree add` + `cd` 再跑 init-feature"
            )

    # v8.0+P0-5:worktree 物理存在硬校验(替代 P0-2 自动建)
    # 单一职责:init-feature 只创建 state.json · 不动 git
    # 正路径(triage 拍板):PMO 用户确认后显式 git worktree add → cd → init-feature
    # 漏建 → FAIL(物化拦截 · 不静默兜底)
    if (
        not bypass_cwd
        and args.worktree_mode != "off"
        and args.worktree_path
    ):
        wt_real = Path(args.worktree_path).resolve()
        if not wt_real.exists():
            die(2, json.dumps({
                "verdict": "FAIL",
                "action": "init-feature",
                "error": (
                    f"worktree path {wt_real} 不存在 · "
                    f"init-feature 不再自动创建(v8.0+P0-5 单一职责)"
                ),
                "hint": (
                    f"按 triage emit 的 pause_for_user 指引:\n"
                    f"  1. git worktree add -b {args.branch} {wt_real} origin/{merge_target}\n"
                    f"  2. cd {wt_real}\n"
                    f"  3. 重跑 state.py init-feature"
                ),
                "rule": "SKILL.md § Triage 入口规范 · 入口完成才进状态机",
                "bypass": "调试场景 export TEAMWORK_BYPASS_CWD_WORKTREE=1",
            }, ensure_ascii=False, indent=2))

    # v8.x+P0-N:worktree path 约定校验(治本 PTR-F041 静默错位)
    # 规则(可枚举 · 进脚本):期望 path = main_project_root / worktree_root_path / feature_id
    #   - main_project_root 从 `git worktree list --porcelain` 第一条解析(linked worktree → main)
    #   - worktree_root_path 从 main_project_root/.teamwork_localconfig.json 读 · 默认 ".worktree"
    # 不匹配 → FAIL(治本 AI 抄 SKILL.md 状态行示例 / 自由发挥路径反模式)
    if (
        not bypass_cwd
        and not os.environ.get("TEAMWORK_BYPASS_WORKTREE_PATH_CHECK")
        and args.worktree_mode != "off"
        and args.worktree_path
    ):
        wt_real = Path(args.worktree_path).resolve()
        main_root: Path | None = None
        try:
            result = subprocess.run(
                ["git", "-C", str(wt_real), "worktree", "list", "--porcelain"],
                capture_output=True, text=True, check=True, timeout=10,
            )
            for line in result.stdout.splitlines():
                if line.startswith("worktree "):
                    main_root = Path(line.split(" ", 1)[1]).resolve()
                    break
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            main_root = None

        if main_root is not None:
            localconfig = main_root / ".teamwork_localconfig.json"
            worktree_root_path = ".worktree"
            config_source = "默认(无 .teamwork_localconfig.json)"
            if localconfig.exists():
                try:
                    cfg = json.loads(localconfig.read_text(encoding="utf-8"))
                    worktree_root_path = cfg.get("worktree_root_path", ".worktree")
                    config_source = str(localconfig)
                except (OSError, json.JSONDecodeError):
                    pass
            expected = (main_root / worktree_root_path / args.feature_id).resolve()
            if wt_real != expected:
                die(2, json.dumps({
                    "verdict": "FAIL",
                    "action": "init-feature",
                    "error": "worktree path 不符合 worktree_root_path 约定",
                    "actual": str(wt_real),
                    "expected": str(expected),
                    "main_project_root": str(main_root),
                    "worktree_root_path_config": worktree_root_path,
                    "config_source": config_source,
                    "hint": (
                        f"修复二选一:\n"
                        f"  A. 移到期望路径(推荐):\n"
                        f"     cd {main_root}\n"
                        f"     git worktree remove {wt_real}\n"
                        f"     git worktree add -b {args.branch} {expected} origin/{args.merge_target}\n"
                        f"     cd {expected} && 重跑 state.py init-feature\n"
                        f"  B. 修改配置匹配现状(若有意自定义 worktree 根):\n"
                        f"     编辑 {localconfig}\n"
                        f"     设 worktree_root_path 字段为 wt 父目录相对 main_root 的路径"
                    ),
                    "rule": "conventions.md §9-12 worktree path 规范",
                    "bypass": "应急 · export TEAMWORK_BYPASS_WORKTREE_PATH_CHECK=1",
                }, ensure_ascii=False, indent=2))

    # --force 覆盖:全部可 die 的校验已过 · 写入前才移走旧 state.json(backup 留档)
    if state_file.exists() and args.force:
        ts = now_iso().replace(":", "_")
        backup = state_file.with_suffix(f".json.bak.{ts}")
        state_file.rename(backup)

    atomic_write(state_file, state)

    # v8.0+P0-13:项目级系统维护已挪到 session-bootstrap(session 级 · 不是 Feature 级)
    # init-feature 只管 Feature 级状态机操作

    # v8.291:跨厂商异质彻底退役 —— 第三视角唯一形态 = 错开模型 subagent 冷审(无 opt-in 分支)。
    # yolo 无人值守时给一条 INFO 说明当前形态 + 提醒实跑证据门(prompt doc)。
    yolo_ext_warning = None
    if yolo_enabled:
        yolo_ext_warning = (
            "ℹ️ yolo 第三视角 = **错开模型 subagent 隔离冷审**(≠会话主模型 · 如 fable5 → opus)· "
            "架构师/QA 多角色评审照跑。🔴 不内化律:产物须经 `state.py external-review` 拿配方"
            "(它落 prompt doc = 实跑证据)· 直接手写 external-cross-review 会被 complete 门拦。"
        )
    emit({
        "verdict": "OK",
        "action": "init-feature",
        "feature_id": args.feature_id,
        "flow_type": args.flow_type,
        "current_stage": initial_stage,
        "state_path": str(state_file),
        "checksum_prefix": state[CHECKSUM_FIELD][:24],
        "created_at": state["created_at"],
        "routing_check": routing,
        "next_action_brief": _init_feature_next_brief(
            args, initial_stage, cfg_fast=_fast_cfg, effective_fast=bool(state.get("fast_mode"))),
        # v8.15:admission MISMATCH 时 emit 顶层显警告(AI 一定看到)+ state.concerns 已留痕
        **({"admission_warning": admission_warning} if admission_warning else {}),
        # prepare 门禁仅 prefix 命中(非本 feature 精确号段)· 顶层显警告 + concerns 已留痕
        **({"prepare_match_warning": prepare_match_warning} if prepare_match_warning else {}),
        # v8.179:yolo + 非异质评审醒目警告(降级安全网 · 无人值守须知悉)
        **({"yolo_external_warning": yolo_ext_warning} if yolo_ext_warning else {}),
    })


def _init_feature_next_brief(args, initial_stage: str,
                             cfg_fast: bool = False, effective_fast: bool = False) -> str:
    """init-feature emit 后给 PMO 的 brief(v8.0+P0-5 简化)。

    triage 已确认 worktree · PMO 已显式建 + cd · init-feature 仅创建 state.json。
    所以 brief 直接告知"进下一步" · 不需要再讨论 worktree。

    Bug 流程额外提示(v8.107):先 diagnose(根因细查 + 修复方案 · 用户确认)再 dev ·
    diagnose **产出** BUG 报告的 §根因/§修复方案(不是 dev 前置)· 防 fix 修偏。
    """
    # v8.294(复盘 R3):fast_mode 生效与否**必须可见** —— 静默回退是双输:
    # 用户既没拿到速度、也不知道为什么慢。三态各自说清来源。
    if effective_fast:
        fast_note = "⚡ fast_mode=**on**(来源 localconfig)· goal/review 各留单路合并评审 · blueprint 评审跳"
    elif cfg_fast:
        fast_note = "⚡ fast_mode=**off**(localconfig 为 true 但被 yolo 覆盖 · 无人值守的安全网 = 全量评审)"
    else:
        fast_note = "⚡ fast_mode=**off**(localconfig 未开 · 全量评审)"

    wt_note = ""
    if args.worktree_mode == "off":
        wt_note = "(worktree_mode=off · 在当前 tree 直接工作)"
    else:
        wt_note = f"(worktree_mode={args.worktree_mode} · cwd={Path.cwd()} 已通过 cwd 校验)"

    # v8.107:Bug 流程先 diagnose(根因细查 + 修复方案确认)· diagnose 产出 BUG 报告 · 用户确认后才进 dev
    pre_stage_action = ""
    if args.flow_type == "Bug":
        pre_stage_action = f"""
🔴 **Bug 流程:先 diagnose(根因细查 + 修复方案)· 用户确认后才进 dev**(治本 fix 修偏):
   1. `diagnose-start` → 🔴 **深读相关代码做根因细查**(triage/prepare 时读的代码往往不够细 · 必须深挖到真因)
   2. 写 `{Path(args.feature)}/bugfix/BUG-<bug-id>.md`(模板 `templates/bug-report.md`)·
      §现象 + §根因(深查实证:哪行/哪个调用/为什么)+ §修复方案(怎么改 · 改哪 · 取舍 · 影响面)·
      frontmatter `bug_id/symptom/root_cause/fix_summary`
   3. 🔴 **把 §修复方案 给用户确认**(R5 暂停点)· 用户 ok 后才 `diagnose-complete` → dev
   4. dev 阶段才按**已确认的方案**写 fix 代码 + §回归测试(不在 diagnose 写 fix 码)
"""

    return f"""## init-feature 完成 · 下一步

{wt_note}
{fast_note}

state.json 已落在:`{Path(args.feature).resolve()}/state.json`
{pre_stage_action}
直接进入首 stage(prepare 子流程已在 init-feature 之前完成 · 见 docs/prepare.md):

1. `state.py {initial_stage}-start --feature {args.feature}`
   - emit 本 stage 详细 brief(必读 / 必产物 / 完成方式)

2. AI 按 brief 完成 stage 工作 → `{initial_stage}-complete`

📎 物化兜底:各 stage-start 校验 worktree 物理存在 + cwd 校验
   不一致 → FAIL + hint(治本 PTR-F033)
📎 项目骨架(KNOWLEDGE / TROUBLESHOOTING / GLOSSARY)由 bootstrap.py 在 session 启动时维护 · 不在 init-feature 后做。
"""


def cmd_reset_prev(args: argparse.Namespace) -> None:
    """v8.0+P0-6:状态机回退一步(治本 raw-write 滥用)。

    安全语义化命令 · 替代 raw-write 修改 current_stage 的场景:
    - 状态机内回退(completed_stages[-1] 回到 current_stage)
    - 清除已转移到的 stage 的 contract(防脏数据)
    - last_completed 的 gate 重置(允许重跑 complete)
    - 自动追 concerns WARN

    硬门禁:
    - Ship 后(ship.phase=pushed · 远程已动)不可回 · 状态不可逆
    - completed_stages 为空 → 无可回退
    """
    # 正常走 checksum 校验:state.json 被外改时 die + 提示先 recover(认证 + audit)再回退
    path = state_path(args.feature)
    state = load_state(args.feature)

    before = json.loads(json.dumps(state))

    # 硬门禁 1:Ship 后不可回
    ship_phase = (state.get("ship") or {}).get("phase")
    if ship_phase == "pushed":
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "reset-prev",
            "error": f"Ship 后不可回退 · ship.phase={ship_phase!r} · 远程已动 · 状态不可逆",
            "hint": (
                "若需要修复:reset-prev 不可用 —— MR 未合并 → "
                "`jump-to-stage --to dev --reason '...'`(MR 窗口期修复口 · 留痕);"
                "已合并 → 开 Bug 流(diagnose 起);整件放弃 → ship-phase --action close-unmerged"
            ),
        }, ensure_ascii=False, indent=2))

    # 硬门禁 2:completed_stages 为空
    completed = state.get("completed_stages") or []
    if not completed:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "reset-prev",
            "error": "completed_stages 为空 · 无可回退的 stage",
            "current_stage": state.get("current_stage"),
            "hint": "若需调整 current_stage 初值 · 用 init-feature --force 或 raw-write",
        }, ensure_ascii=False, indent=2))

    last_completed = completed[-1]
    current = state.get("current_stage")

    # 硬门禁 3:current_stage 与 last_completed 相等(异常/无意义)
    # 典型 case:旧版 review NEEDS_REVISION bug 错误地把 review 加 completed_stages ·
    # 已被 v8.x review-complete 回退路径检测修复 · 此处兜底剩余异常
    if last_completed == current:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "reset-prev",
            "error": (
                f"current_stage={current!r} 与 last_completed 相等 · "
                "状态自洽 · reset-prev 无效"
            ),
            "hint": (
                "排查:state.json 是否被外部修改 / review-complete NEEDS_REVISION 应自动转 dev "
                "(v8.x 已修)· 若状态确需手工调整 · 用 raw-write 显式改 current_stage(留 concerns WARN)"
            ),
        }, ensure_ascii=False, indent=2))

    # 1. current_stage 改回 last_completed
    state["current_stage"] = last_completed

    # 2. completed_stages 移除 last_completed
    state["completed_stages"] = completed[:-1]

    # 3. 清除"已转移到的 stage" 的 contract(防脏数据)
    if current and current != last_completed:
        contracts = state.get("stage_contracts") or {}
        contracts.pop(current, None)

    # 4. last_completed 的 gate 重置 · 允许重跑 complete
    contracts = state.setdefault("stage_contracts", {})
    c = contracts.setdefault(last_completed, {})
    c["input_satisfied"] = False
    c["process_satisfied"] = False
    c["output_satisfied"] = False
    c.pop("completed_at", None)
    c.pop("duration_minutes", None)
    # started_at 保留(stage 开始时间不变)

    # 5. legal_next_stages 重算
    flow_graph = resolve_flow_graph(state.get("flow_type") or "", state.get("preset") or "full")
    state["legal_next_stages"] = flow_graph.get(last_completed, [])

    # 6. 自动 concerns WARN(audit 透明)
    state.setdefault("concerns", []).append(
        f"{now_iso()} WARN reset-prev: {current!r} → {last_completed!r} · "
        f"reason: {args.reason}"
    )

    state["updated_at"] = now_iso()
    state["updated_by"] = "reset-prev"
    atomic_write(path, state)

    emit({
        "verdict": "OK",
        "action": "reset-prev",
        "from_stage": current,
        "to_stage": last_completed,
        "reason": args.reason,
        "legal_next_stages": state["legal_next_stages"],
        "completed_stages_after": state["completed_stages"],
        "next_action_brief": (
            f"## reset-prev 完成\n\n"
            f"已回退:{current!r} → {last_completed!r}\n"
            f"contract 重置:{last_completed} 三 gate 全 false · 可重跑 complete。\n\n"
            f"下一步:跑 `state.py {last_completed}-complete --feature {args.feature} ...` 重新推进。\n\n"
            f"⚠️ 已自动追 concerns WARN(audit 透明)。"
        ),
    })


def _load_localconfig(start):
    """localconfig 解析(单源 = _v8_engine.load_localconfig · 跨 worktree 边界)· 失败返 None。"""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _v8_engine import load_localconfig  # type: ignore
    except ImportError:
        return None
    return load_localconfig(start)


def _read_id_strategy(start: Path) -> str:
    """读 localconfig `id_strategy`(v8.79)。

    - 默认 = `utc-yymmddhhmmss`(v8.79 起 · 治本分布式 `max+1` 撞号 · 详 docs/conventions.md §1)
    - opt-out = `sequential`(旧顺序号 `max+1` · 单 clone 项目可保留好念的短序号)
    """
    DEFAULT = "utc-yymmddhhmmss"
    VALID = {"sequential", "utc-yymmddhhmmss"}
    cfg = _load_localconfig(start)
    if not isinstance(cfg, dict):
        return DEFAULT
    strat = cfg.get("id_strategy")
    return strat if strat in VALID else DEFAULT


def _read_fast_mode(start) -> bool:
    """读 localconfig `fast_mode`(默认 **False** · 显式 true 才开)。

    fast mode = 评审收敛为两端单路(goal 合并冷审 + review 合并评审 · blueprint 评审去)·
    保留:测试硬门 · 用户暂停点 · worktree 纪律。🔴 yolo 忽略 fast(v8.262)。

    🔴 v8.294:改走跨 worktree 边界的解析器 —— 原实现遇 worktree 的 `.git` 文件即停,
    而 localconfig 不入 git 只在主工作树,导致 fast_mode 自 v8.260 起在默认 worktree
    模式下**从未生效过**(case 实证:配置 true · state.json 无该键 · 按全量 roster 跑)。
    """
    cfg = _load_localconfig(start)
    return isinstance(cfg, dict) and cfg.get("fast_mode") is True


def _detect_id_collision(feature_dir: Path, feature_id: str) -> "dict | None":
    """撞号硬校验(v8.79 · R0 物化 · 治本 AON 13 组实测撞号)。

    扫 `feature_dir` 的兄弟目录 · 若有**另一**目录共享同 `{PREFIX}-{字母}{number}`
    号段(同名 = 自身 · re-init/force · 不算撞)→ 返回撞号详情 · 否则 None。
    注:仅兜**同 clone** race;跨 clone(各自看不到对方在途目录)的撞号此处兜不住 —— 合并时才现 ·
    故 `utc-yymmddhhmmss` 才是跨 clone 的根治。两层互补 · 详 docs/conventions.md §1。
    """
    import re as _re
    m = _re.match(r"^(.+?-[FBM]\d+)", feature_id)
    if not m:
        return None
    number_id = m.group(1)  # e.g. PTR-F045 / SVC-PLATFORM-F260601143012
    root = feature_dir.parent
    if not root.exists():
        return None
    self_name = feature_dir.name
    # number_id 后必接非数字或结尾(防 PTR-F045 误匹配 PTR-F0451-*)
    pat = _re.compile(rf"^{_re.escape(number_id)}(?:\D|$)")
    for child in root.iterdir():
        if child.is_dir() and child.name != self_name and pat.match(child.name):
            return {"number_id": number_id, "existing": child.name}
    return None


def cmd_prepare_check(args: argparse.Namespace) -> None:
    """v8.13:prepare 子流程 ID 冲突预检 · 推荐 next_available_id。

    按 --flow-type 定 artifact ID 字母(Feature=F · Bug=B · Micro=M ·
    详 docs/conventions.md §1)· 扫 --features-root 下该字母的已有 artifact 目录 ·
    抓 --feature-id-prefix 匹配的 ID · 返回 existing_ids + next_available_id。

    治本 case:① PMO 启动 Feature 不知 F040 已被 Planning 占用 → 临时改号多确认一轮;
    ② Bug 流程错推 PREFIX-F(应 PREFIX-B)· flow_type 原本没参与 ID 字母。
    """
    import re

    root = Path(args.features_root or "docs/features").resolve()
    if not root.exists():
        emit({
            "verdict": "FAIL",
            "command": "prepare-check",
            "error": f"features_root 不存在: {root}",
            "hint": "用 --features-root <绝对路径> 指定 · 默认 docs/features",
        })
        return

    prefix = args.feature_id_prefix
    if not prefix:
        emit({
            "verdict": "FAIL",
            "command": "prepare-check",
            "error": "--feature-id-prefix 必填(如 PTR / INFRA / SVC-PLATFORM)",
        })
        return

    # flow_type → artifact ID 字母(详 docs/conventions.md §1)
    # Feature=F · Bug=B · Micro=M · 缺省 F(--flow-type 漏传时向后兼容)
    # v8.220:ID 字母收敛 F/B(Micro 的 M 退役 · legacy 归一后即 Feature)
    _pub_ft, _ = normalize_flow(args.flow_type or "Feature")
    id_letter = "B" if _pub_ft == "Bug" else "F"

    # 扫匹配 <PREFIX>-<字母><NNN>* 目录(字母由 flow_type 定)
    pattern = re.compile(rf"^{re.escape(prefix)}-{id_letter}(\d+)")
    existing: list[tuple[int, str]] = []  # (number, full_id)
    for child in root.iterdir():
        if not child.is_dir():
            continue
        m = pattern.match(child.name)
        if m:
            existing.append((int(m.group(1)), child.name))

    existing.sort()
    existing_ids = [name for _, name in existing]
    used_numbers = {n for n, _ in existing}

    # v8.79:号段分配按 id_strategy(默认 utc 时间戳 · opt-out sequential · 详 docs/conventions.md §1)
    id_strategy = _read_id_strategy(root)
    if id_strategy == "sequential":
        # 顺序号 max+1(连续递增 · 不填空洞)· ⚠️ 分布式 race 隐患 · 靠 init-feature 撞号硬校验兜
        next_num = (max(used_numbers) + 1) if used_numbers else 1
        next_id_stem = f"{prefix}-{id_letter}{next_num:03d}"
    else:  # utc-yymmddhhmmss(默认 v8.79)· UTC0 秒级时间戳 · 跨机分布式免协调
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
        next_num = int(ts)
        next_id_stem = f"{prefix}-{id_letter}{ts}"

    payload = {
        "verdict": "OK",
        "command": "prepare-check",
        "features_root": str(root),
        "feature_id_prefix": prefix,
        "id_letter": id_letter,
        # v8.221:对外词汇 = Feature/Bug + preset(配置面板照抄:flow=Feature · preset=micro)
        "flow_type_public": normalize_flow(args.flow_type or "Feature")[0] if args.flow_type else None,
        "preset": normalize_flow(args.flow_type or "Feature")[1] if args.flow_type else None,
        "config_line_hint": ("⚙️ 配置行词汇(v8.220):flow=<Feature[·micro] / Bug> · clarity=<explicit|normal|ambiguous>"
                             " · bl=<BL-NNN|无> · branch 前缀统一 feature/(Bug=fix/)· ID 统一 F/B(M 已退役 · lite 已退役)"),
        "existing_ids": existing_ids,
        "existing_count": len(existing_ids),
        "id_strategy": id_strategy,
        "next_available_number": next_num,
        "next_available_id_stem": next_id_stem,
        "hint": (
            f"prepare 暂停点 artifact ID 默认填 {next_id_stem}-<Kebab-Case-名称> · "
            f"用户可改 · 但应避开 existing_ids 中已占编号"
            + (" · 🕐 id_strategy=utc-yymmddhhmmss(UTC 秒级时间戳 · 已生成勿手算 · 重跑得新号)"
               if id_strategy != "sequential"
               else " · id_strategy=sequential(顺序号 max+1)")
            + ("" if args.flow_type
               else " · ⚠️ 未传 --flow-type · ID 字母默认 F · Bug/Micro 务必补 --flow-type")
        ),
    }

    # v8.x:--flow-type 可选 · 返回 stage_chain_preview(stage × 评审角色)
    # 让 PMO 在 prepare 暂停点直接渲染「📋 各 stage 评审角色」子表 · 不凭手工查 spec
    if args.flow_type:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from _v8_engine import build_stage_chain_preview, FLOW_STAGE_CHAIN
            # v8.221:legacy 名归一 → 链键(Micro 是 Feature 的 preset)
            # v8.342:--preset 参与解析 —— 定了 tiny 却预览出 11-stage 全链,
            # 等于把「已经减掉的税」又摆回用户面前(配置立了没接线的老毛病)。
            # 🔴 先归一再查表:原实现 `flow_type if flow_type in FLOW_STAGE_CHAIN` 会在
            # flow_type="Feature" 时直接短路,preset 永远读不到 —— 定了 tiny 也预览出全链。
            _pub, _pre = normalize_flow(args.flow_type, getattr(args, "preset", None))
            _chain_key = internal_flow_key(_pub, _pre)
        except ImportError as e:
            payload["stage_chain_preview_error"] = str(e)
        else:
            if _chain_key not in FLOW_STAGE_CHAIN:
                payload["stage_chain_preview_error"] = (
                    f"flow_type '{args.flow_type}' 不支持 stage chain 预览 · "
                    f"支持: {sorted(FLOW_STAGE_CHAIN)}(Feature Planning / 问题排查 不进状态机 · 无 chain)"
                )
            else:
                payload["flow_type"] = args.flow_type
                payload["stage_chain_preview"] = build_stage_chain_preview(_chain_key)

    # v8.15:admission 校验(治本 F001 GCP gateway case · AI 不读 prepare.md §2.1/§2.2)
    # 设计:工具不扫关键词 regex(伪枚举 · 死板 · 误判)· 而是强制 AI 必传判断结果(judgment)
    # R0 哲学拆分:
    # - 可枚举:judgment 字段必填(工具 BLOCK if missing) + consistency 校验
    # - 不可枚举:judgment 内容(AI 自由判断 · audit 留痕)
    admission = _validate_admission_judgment(args)
    if admission["verdict"] == "FAIL":
        emit({
            "verdict": "FAIL",
            "command": "prepare-check",
            "error": admission["error"],
            "hint": admission["hint"],
            "spec": "docs/prepare.md § 2.1(复杂度升级判据)+ § 2.2(Micro 准入)",
        })
        return
    # 注入 payload(consistency / admission_judgment / user_intent / warning if MISMATCH)
    payload.update(admission["payload_extras"])

    # v8.27:reviewer 思考清单(治本 F-Bv2-8 case · PMO 直接抄 stage_chain_preview 默认 reviewers)
    # 4 个核心问题 · 软提示 AI 在 emit prepare 暂停点时基于此给思考后的 reviewer 预估
    # 不强制 JSON 必传(Option A · 用户拍板)· 不像 v8.15 admission_judgment 物化
    payload["reviewer_thinking_checklist"] = REVIEWER_THINKING_CHECKLIST
    # v8.215:分诊证据先行(智能分诊 v1)——「看过再判」:30 秒侦察后填证据 · 空着不给判。
    # clarity 解耦「大」和「不确定」:改动面大→Feature 骨架;不确定性低→评审走轻档。
    payload["triage_evidence"] = {
        "🔴": "PMO 侦察(grep 候选改动面 / 查 KNOWLEDGE / 新依赖)后逐项填 · 凭证据判 clarity · 不猜",
        "estimated_files": "<侦察后填数量级 · 如 ~12>",
        "cross_repo": "<true/false>",
        "new_deps": "<新依赖清单 或 无>",
        "has_ui": "<true/false>",
        "mechanical": "<true/false · 机械映射类(外化/重命名/迁移/升级)且无新业务行为>",
        "clarity": "<explicit/normal/ambiguous · 判定标准:用户给出明确方案 或 mechanical=true → explicit;"
                   "一句话含方向词/多方案可选 → ambiguous;其余 normal>",
        "consumption": "🔴 本证据在 prepare 只消费一件事:判 clarity(意图明确度)—— "
                       "**评审面与环节装配不在 prepare 做**(装配后移:goal 调研后按实测复杂度定 · "
                       "role_value_criteria 届时用 · 单源 goal-stage § 链装配)· "
                       "clarity 传 `init-feature --clarity` 仅记录进 state(台账/年检校准 · 不触发硬编码行为)",
    }
    # v8.216:角色价值判据(给 AI 的判断框架 · 非规则)—— 逐角色问「这个视角对本 feature 能拦住什么」
    payload["role_value_criteria"] = {
        "pl": "需求有价值前提/范围可质疑吗?(用户明说要做的机械改动 → 无 · 新能力/改行为 → 有)",
        "qa": "有边界条件/AC 可测性风险吗?(纯文案/配置 → 弱 · 有状态/并发/输入面 → 强)· goal/blueprint/review 默认并入外审覆盖方向(可验证/可测试/测试真实性)· 判强才加回独立冷审(v8.243/244)",
        "architect": "有架构决策/跨模块影响吗?(单文件机械改 → 弱 · 新依赖/改契约/跨层 → 强)· goal 默认并入外审覆盖方向「可实现」(blueprint/review 主审席位保留)· 判强才加回 goal 独立冷审(v8.243)",
        "external": "goal/blueprint/review 默认在(覆盖方向制 v8.243/244:必覆盖方向 + AI 自主方向)· 判据改为:要不要升异质(≥3 模块触发 · 核心链路)或加维度",
        "🔴": "每角色给一行理由(有值留 · 无值去)· review stage 从严(拦真主力 · 建议 ≥2 视角 · <2 需强理由)",
    }
    payload["reviewer_thinking_hint"] = (
        "🔴 装配后移(用户拍板):此 4 问与 role_value_criteria 的**消费时点在 goal 调研后**"
        "(单源 goal-stage § 链装配)—— prepare 不设评审角色 · 不装链;"
        "goal 自身评审面调研后 AI 自定(change-review-roles 留痕不问用户)· "
        "下游装配随 PRD 终确认导读展示(默认执行 · 用户不要求改就生效)。"
        "⚠️ 加减须有**本 Feature 特定理由** · 不是套路化删角色 —— 尤其 **pl 默认保留**"
        "(产品方向视角)·『无 ROADMAP』**不是**去 pl 的理由(ROADMAP=规划层 · 与 PRD 产品方向"
        "评审无关)· 仅纯内部/技术重构无产品面才去 pl。"
        "case 实证(F-Bv2-8 · 2026-05-25):PMO 第一次直接抄默认 · 经用户提示后二次思考才识别 "
        "ui_design 跳过(后端先行)/ blueprint 强 external(跨 5 module 触发点)等调整。"
    )

    # host-aware 输出风格 hint(codex-cli terminal 渲染 markdown 表格易破 · 推荐 box-drawing)
    # prepare-check 无 --feature(state.json 尚不存在)· host 无从读 → 按 unknown 给保守风格
    # (host 单源 = state.json.host · 全局 host_audit.json 已退役)
    payload["output_style_hint"] = _build_output_style_hint(None)

    # v8.14 + v8.15:写 prepare_check_audit jsonl(init-feature 门禁读这个)
    # 治本 PTR-F054:prepare-check 物化但 AI 不调用 → 下游门禁兜底
    # v8.15:audit 加 admission_judgment / consistency · 治本 F001(选错 flow_type)
    audit_record = {
        "timestamp": now_iso(),
        "feature_id_prefix": prefix,
        "features_root": str(root),
        "flow_type": args.flow_type or "",
        "id_letter": id_letter,
        "next_available_id_stem": next_id_stem,
        "existing_count": len(existing_ids),
        "user_intent": args.user_intent or "",
        "admission_judgment": admission["judgment"],  # parsed JSON or None
        "consistency": admission["consistency"],     # OK / MISMATCH / FAIL(v8.34 删 SKIPPED)
        "recommended_flow_type": admission["recommended_flow_type"],
    }
    _write_prepare_audit(audit_record)
    payload["audit_recorded"] = True

    emit(payload)


# v8.27:reviewer 思考清单(prepare-check 输出 · 治本 F-Bv2-8 PMO 直接抄默认 case)
# 用户决策:Option A(checklist 提示 · 不物化 JSON 必传)· 核心 4 问(不过载)
REVIEWER_THINKING_CHECKLIST = [
    {
        "question": ("本 Feature 有无产品方向影响?(业务目标 / 用户可见行为 / 商业模式 / "
                     "跨项目一致性 / 变更级联 Level≥2 —— 任一即『有』)"),
        "if_yes": ("goal **保留 pl**(默认 · 常态)· PL 审产品方向对齐 —— "
                   "telos:防『做了一堆 Feature 但偏离产品方向』"),
        "if_no": ("仅『纯内部 / 技术重构 · 零产品面 · 零跨项目 · 变更级联 Level-1 局部』"
                  "才去 pl(少数例外)· ⚠️ **别拿『无 ROADMAP』当借口去 pl** —— "
                  "ROADMAP 是规划层产物 · 与 PL 的 PRD 评审价值(产品方向)无关 · "
                  "二者不是一回事"),
    },
    {
        "question": "本 Feature 是否含 UI 改动?",
        "if_no": "ui_design 跳过(--needs-ui=false)· 节省 designer 一轮 + browser_e2e 跳过",
        "if_yes": "ui_design 启用 · reviewers [designer, pm]",
    },
    {
        "question": "本 Feature 跨 ≥3 个 module 触发点 / 调用方?(如跨多 stage / 多 service)",
        "if_yes": "blueprint / review 强调 external(第三视角查漏 · 默认错开模型冷审〔v8.268〕· 异质 opt-in · F-Bv2-8 实证有效)",
        "if_no": "blueprint / review external 默认即可",
    },
    {
        "question": "本 Feature 是否数据模型重构?(删/改老字段 · 表结构变 · 索引变)",
        "if_yes": "blueprint 强 architect + (若项目配置)加 dba 评审",
        "if_no": "blueprint architect 默认即可",
    },
]


# v8.44.4:host-aware 输出风格 hint(治本 case 2026-05-28 codex-cli 渲染 markdown 表格失败)
# - claude-code:rich markdown 渲染 OK · 表格 / 加粗 / emoji 都好
# - codex-cli / gemini-cli / unknown:terminal renderer 对复杂 markdown 表格容易破
#   推荐 box-drawing(┌─┬─┐│├─┤└─┘)绘制表格 / 纯文本列表 · 避免 raw 字符显示
HOST_OUTPUT_STYLE_PROFILES = {
    "claude-code": {
        "style_id": "markdown_ok",
        "description": "Rich markdown 渲染 OK · 表格 / 加粗 / emoji / code block 都好",
        "table_format": "markdown",  # | col | col | + |---|---|
        "list_format": "markdown",
        "emphasis": "markdown",      # **粗** / *斜* / `code`
        "emoji_safe": True,
    },
    "codex-cli": {
        "style_id": "box_drawing_or_plain",
        "description": ("Terminal renderer 对复杂 markdown 表格容易破(raw 字符显示)· "
                        "推荐 box-drawing(┌─┬─┐│├─┤└─┘)绘制表格 / 纯文本 key: value 列表"),
        "table_format": "box_drawing",  # ┌─┬─┐│├─┤└─┘
        "list_format": "plain",         # "- " / "1. " · 不嵌套粗体
        "emphasis": "plain",            # 不用 ** 加粗 · 改用 "🔴 " 前缀 / 大写 / 缩进
        "emoji_safe": True,             # emoji 可用(case 实证)
    },
    "gemini-cli": {
        "style_id": "box_drawing_or_plain",  # 保守同 codex-cli
        "description": "未实测 · 保守用 box-drawing(同 codex-cli profile)",
        "table_format": "box_drawing",
        "list_format": "plain",
        "emphasis": "plain",
        "emoji_safe": True,
    },
    "unknown": {
        "style_id": "box_drawing_or_plain",  # 默认保守
        "description": "host 未知 · 保守用 box-drawing(最大兼容)",
        "table_format": "box_drawing",
        "list_format": "plain",
        "emphasis": "plain",
        "emoji_safe": True,
    },
}


def _build_output_style_hint(host: Optional[str]) -> dict:
    """v8.44.4:按 host 返回输出风格 hint dict · PMO emit 暂停点时按此风格。

    返:
      {host, style_id, description, table_format, list_format, emphasis, emoji_safe, rationale}

    PMO 看 hint 决定:
    - codex-cli host → 表格用 box-drawing · 不用 markdown · 避免 raw 字符显示
    - claude-code host → markdown 表格 OK · 用 markdown 更紧凑
    """
    h = host or "unknown"
    profile = HOST_OUTPUT_STYLE_PROFILES.get(h, HOST_OUTPUT_STYLE_PROFILES["unknown"])
    return {
        "host": h,
        "style_id": profile["style_id"],
        "description": profile["description"],
        "table_format": profile["table_format"],
        "list_format": profile["list_format"],
        "emphasis": profile["emphasis"],
        "emoji_safe": profile["emoji_safe"],
        "rationale": (
            "treat host 渲染能力为客观信号 · prepare-check 物化检测 + emit hint · "
            "PMO 按 hint 选默认表达方式 · 避免每次被用户提示后才改"
            "(治本 case 2026-05-28 codex-cli markdown 表格失败)"
        ),
    }


# v8.46 C:Feature Planning 物化入口(治本未物化漏洞 · 用户洞察 2026-05-28)
# 根因:Feature Planning 不进状态机 · 无 state.py 兜底 · PRODUCT-OVERVIEW-INTEGRATION.md / feature-planning.md
# 纯靠 AI 自觉读 → AI 没读就不按规范(不维护规划状态表 / 草稿态误影响下游)。
# planning-check 不进状态机(不写 state.json)· 纯 emit checklist + 必读规范 · 物化「你必须想这件事」。
PLANNING_CHECKLIST = [
    {"item": "🔴 拆 BL/WS 前调研实际代码现状:每个候选 BL 核验「已做什么 / 真缺口在哪」· 反映真实完成度(不把已完成列 todo · 不把有脚手架的当 greenfield)· decisive 前提(数据是否真入库 / 能力是否真生效)核验实际代码 · 不轻信 Explore/sub-agent 摘要 · 🔴 需 live 数据(查 DB/log)先读 project-specs/TROUBLESHOOTING.md 拿连法,别凭 .env/启动脚本瞎试",
     "spec": "feature-planning.md §2 Step 1"},
    {"item": "🔴 拆分视角 = 业务交付,不是子项目:**代码跨多个子项目 ≠ 拆多个 feature**(target 只是 ROADMAP 归属 · 实现可跨 · 前缀取业务交付宿主〔详 prepare.md §1.5.3〕)· 拆解讨论稿每条候选 BL 必答**大白话目标**(`goal_plain` · 这条单独上线后谁能干什么/得到什么 —— 写不出 = 横切件并回宿主 · ws-progress 总览表直出此列)",
     "spec": "feature-planning.md §2 Step 5.7 + templates/workstream.md"},
    {"item": "范围判定:工作区级(改 teamwork-space.md + 多 PROJECT.md)vs 子项目级(单 PROJECT.md + ROADMAP.md + sitemap.md)",
     "spec": "feature-planning.md §2 Step 2"},
    {"item": "🎨 全景UI初步规划(本轮涉 UI 时 · 🔴 拆 WS 之前出):在 {子项目}/docs/design/preview-project/ 出/扩 design system + 本轮关键页(初步 · 系统+代表页 · 非每页 · 防瀑布 · 跑 preview.sh 看)+ 同步 sitemap.md(IA 地图 · 只写层级/导航不写视觉)· 完成产生 git diff = 拆 WS 的输入 · 🔴 **出完必给用户可访问预览 URL(跑 preview.sh 抓 PREVIEW_URL)+ emit R5 等用户确认全景 · 用户没确认过 = 不算规划完成**(auto/yolo 自动确认 · 留痕=下游 WS frontmatter ui_panorama_confirmed 标 auto · 🔴 规划不进状态机 add-concern 不可用);非 UI 轮跳过(下游 WS 标 全景初规:N-A)",
     "spec": "feature-planning.md §2 Step 5"},
    {"item": "核心产出 WS(product-overview/workstream/WS-NN.md · 1..N 个 · 输入=全景diff+业务目标 · 承接 1+ 执行线 · 拆一组 feature · 🔴 每 WS 记 全景初规状态(✅/N-A)+ 🔴 ui_panorama_confirmed(涉 UI 用户确认全景的 ISO · 必填才能规划完成)+ 覆盖的全景页清单 + 执行顺序与并行建议(波次:同波可并行/各自 worktree · 跨波串行 + 同改面/跨子项目方向额外串行))· 0-1 时含业务架构与产品规划.md(愿景+执行线列表)· 🔴 照 templates/workstream.md 起草**别抄项目旧 WS** · 写完跑 `state.py ws-lint --ws WS-NN` 校验最新模板(TEAMWORK-MACHINE 块+WS-PROGRESS/WS-DAG 标记)· 🔴 不出 feature 实现代码(R6 · 全景 preview-project 是设计代码例外)· 不进 stage 链 · 🔴 v8.239 **拆 WS 前两道深度门**:①调研深度契约(每候选 BL 的 current_state 必出自实读代码 · 附来源文件 · ws-lint 抓占位)②**拆解讨论暂停点(R5 必经)**:拆解草案(候选 BL+边界理由+粒度自检+波次)先给用户讨论收敛(合并/砍/改边界)才落 WS —— WS 必须是「代码现状 × 用户深度讨论」的产物 · 不是 AI 一把拆完;粒度反压:BL>6 或有「无独立交付价值 / 按评审面横切」的 BL → 草案必须给「为什么不合并」;🔴 v8.240 边界判据:主判据=交付内聚 · feature 可跨子项目(target 只是 ROADMAP 归属 · 子项目边界不是拆分理由)· 薄承接件默认并入宿主(独立须硬理由:外部gate/交付节奏/blast radius/管辖边界 · 含金量悬殊=强合并信号)· 落盘后合并/砍件不重排 id(被并件留 `→ 已并入 Sx`)",
     "spec": "feature-planning.md §2 Step 6 + templates/workstream.md"},
    {"item": "WS 拆出的 feature 写入 ROADMAP(BL-NNN · 关联 WS)· feature 全写入 = WS ✅ 规划完成 · 每个 BL 后续用户拍板走 prepare 启动 Feature",
     "spec": "conventions.md §4 + prepare.md §5"},
    {"item": "🔴 规划收尾必 emit R5 暂停点问用户**如何收尾**(WS+ROADMAP+全景是 Step 0 worktree 内未提交改动)· 🔴 头两项一步到位(治本:别让用户手动『你直接合并然后收尾』):**1. 确认·合入 MR+收尾**(commit+push+开 MR+**自动合并**+清 worktree+净化主分支一步到位)· **2. 确认·合入收尾+启动首个 BL**(同 1 · 收尾完 prepare 首波 ready BL〔execution_waves W1〕)· **3. 建 MR 我自己平台合**(await-merge 轮询 / 平台合后收尾)· **4. 先不提交** · 🔴 **自动合并硬门(选1/2)= merge_target 非主分支**(main/master → 回退选 3 · 同 yolo 风险模型)· 平台拒(审批/CI)→ 回退选 3 · 🔴 启动首个 BL(选2)前提 = finalize 完成后+用户显式选+feature target=集成分支(守 v8.188『别叠 feature 在未合并 planning 分支』)· 不走 ship 状态机",
     "spec": "feature-planning.md §2 Step 9"},
]


def cmd_planning_check(args: argparse.Namespace) -> None:
    """v8.46:Feature Planning 物化入口 · emit 规划 checklist + 必读规范(不进状态机)。

    治本 Feature Planning 未物化漏洞:规划路径无 stage 兜底 · PRODUCT-OVERVIEW-INTEGRATION /
    feature-planning 纯靠 AI 自觉读。本命令物化"你必须想这件事"(像 prepare-check)·
    检测 product-overview/ 存在 → emit 规划状态机 + 必读 · 不存在 → 仍 emit 基础 checklist。
    """
    # project_root:--project-root 显式 · 否则 find_project_root(cwd)
    project_root = None
    if getattr(args, "project_root", None):
        project_root = Path(args.project_root).expanduser().resolve()
    else:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from bootstrap import find_project_root
            project_root = find_project_root(Path.cwd())
        except Exception:
            project_root = Path.cwd()

    po_dir = project_root / "product-overview"
    po_exists = po_dir.is_dir()

    # v8.48:PRODUCT-OVERVIEW-INTEGRATION.md 是产品规划权威 · 总 must_read
    #   (无 po 时学怎么冷启动初创 · 有 po 时学状态管理 + 与 teamwork-space 派生关系)
    must_read = ["PRODUCT-OVERVIEW-INTEGRATION.md", "docs/feature-planning.md"]

    payload = {
        "verdict": "OK",
        "command": "planning-check",
        "project_root": str(project_root),
        "product_overview_exists": po_exists,
        "must_read": must_read,
        "entry_criteria": {
            "keyword": "规划 / 拆 roadmap / 路线图 / 全景 / 商业模式调整 / 做电商 / 做 SaaS",
            "complexity_force_upgrade": (
                "关键词命中 Feature/Micro 时 · 命中任一强制升 Feature Planning:"
                "跨独立 git 仓库(≥2 · 同 repo 多部署单元不计入)/ 数据模型重构 / 老需求架构性废弃 / 影响 ≥2 BL / 方向级业务变更"
            ),
        },
        "planning_checklist": PLANNING_CHECKLIST,
        "planning_order": (
            "🔴 权威链路(详 SKILL.md § teamwork 业务流程架构):业务架构与产品规划(愿景+执行线列表)"
            "→ ✅确认派生 teamwork-space.md →(涉 UI)全景UI初步规划(preview-project + sitemap · 拆 WS 前)"
            "→ WS(workstream/ · 1..N · 承接 1+ 执行线 · 拆一组 feature · 每 WS 记 全景初规状态)"
            "→ feature 写入 ROADMAP(BL · 关联 WS · 全写入=WS✅规划完成)→ 用户拍板 BL → prepare+init-feature → F。"
            "teamwork-space.md **不是** Feature Planning 产出 · 由 product-overview「✅ 已确认」内容派生"
        ),
        "worktree_setup": (
            "🔴 进入 feature-planning 前先建**临时 worktree**(隔离规划产物 · 同 feature worktree 策略 —— "
            "防 WS/ROADMAP/product-overview + 全景 preview-project 代码落主工作区污染主分支、撞并行 feature 基线):\n"
            "  git fetch origin\n"
            "  git worktree add -b planning/<短名> <repo-root>/.worktree/planning-<短名> origin/<merge-target>\n"
            "  cd <worktree-path>   # 🔴 规划产物全写 worktree 内路径(同 worktree 纪律)\n"
            "  → 规划完成 → ⏸️暂停问「如何收尾」(5 选项 · 头两项一步到位):1.合入 MR+收尾(自动合并+清 worktree+净化) 2.收尾+启动首个 BL 3.建 MR 我自己平台合 4.先不提交 · "
            "🔴 自动合并硬门 = merge_target 非主分支(main/master → 回退手动)· 🔴 启动首个 BL(选2)必 finalize 完成后(别叠 feature 在未合并 planning 分支)· "
            "finalize = cd 回主工作区 → git worktree remove → `state.py main-sync --merge-target <mt> --strategy <commit-push|stash-pull|skip>`(🔴 --strategy 必传 · =ship-finalize · 详 Step 9)\n"
            "  (trivial 单文档微调 · 用户可决定免 worktree)"
        ),
        "key_constraints": [
            "🔴 不进状态机:init-feature --flow-type 'Feature Planning' 会被 reject",
            "🔴 在**临时 worktree 内**做(见 worktree_setup)· 不写主工作区 · 规划产物随 MR 原子合入",
            "🔴 不出 feature 实现代码(R6 红线)· 产出 = 项目级文档 + 全景 preview-project(设计代码 · 故更需 worktree 隔离)",
            "BL-NNN 在规划期分配 · 不是 Feature ID(无 PRD/TC/TECH)",
        ],
        "next_hint": (
            f"🔴 先按 worktree_setup 建临时 worktree + cd 进去 · 再读 {' + '.join(must_read)} · "
            f"按 checklist 在主对话执行 Feature Planning(不进状态机 · PMO 直接做 · 但在 worktree 内)· "
            f"完成后拆出的 BL 用户拍板再走 prepare 启动 Feature"
        ),
    }

    if po_exists:
        # 项目有 product-overview/ → emit 规划状态机(治本"草稿态误影响下游")
        payload["planning_state_machine"] = {
            "states": ["📝 草稿", "🔄 讨论中", "⏸️ 待确认", "✅ 已确认"],
            "downstream_rule": (
                "🔴 仅「✅ 已确认」内容才影响 teamwork-space.md / 下游执行 · "
                "草稿/讨论中/待确认 都不更新 teamwork-space.md"
            ),
            "required_tables": [
                "每份 product-overview 文档头部:规划状态表(文档状态 / 最近更新 / 待决议题)",
                "文档末尾:规划议题追踪表(编号 / 议题 / 状态 / 结论 / 影响章节 / 日期)",
            ],
        }
        payload["product_overview_hint"] = (
            f"本项目有 product-overview/({po_dir})· 规划必维护规划状态表 + 议题追踪 · "
            f"详 PRODUCT-OVERVIEW-INTEGRATION.md(加载规则 + 状态管理 + 与 teamwork-space 关系)"
        )
    else:
        # v8.48:无 product-overview → 产品规划优先(不再说"可直接拆 ROADMAP" · 那把上游当 optional)
        payload["product_overview_hint"] = (
            f"本项目无 product-overview/ · 🔴 冷启动权威顺序 = 产品规划优先:先建 product-overview"
            f"(PL 引导模式 · 产品定位/业务架构/执行手册 · 见 PRODUCT-OVERVIEW-INTEGRATION.md 建议章节 + 裁剪规则)"
            f"→ ✅确认派生 teamwork-space.md → 再拆 ROADMAP。单 Feature 极简项目用户可拍板跳过 · 直接拆 ROADMAP"
        )

    emit(payload)


def _validate_admission_judgment(args) -> dict:
    """v8.15:校验 --user-intent + --admission-judgment(治本 F001 case)。
    v8.34:删 SKIPPED 兼容路径 · 全局强制必传(治本 SVC-CORE-M001 case · AI 钻 SKIPPED 空子不思考)。

    返回 {verdict, error?, hint?, payload_extras, judgment, consistency, recommended_flow_type}。
    consistency: OK(judgment 推荐 == --flow-type) / MISMATCH(不一致 · WARN) / FAIL(BLOCK)

    R0 哲学:工具不解析 user_intent 语义 · 仅校验 admission_judgment JSON 4 字段必填。
    AI 必须真读 prepare.md §2.1/§2.2 才能写出合理 judgment(伪造 ai_rationale 会在 retro
    被复盘到 · 心理成本高)。

    v8.34 删 SKIPPED 兼容路径 ROI:
    - 风险:破坏旧脚本 / debug / migration 路径 · 老 case 调 prepare-check 不传两参 → BLOCK
    - 收益:case 实证(SVC-CORE-M001 Micro 2026-05-26)PMO 不传 admission_judgment 跳过思考 ·
      v8.15 物化「你必须想这件事」被 SKIPPED 兜底架空 · 必须删
    """
    has_intent = bool(args.user_intent)
    has_judgment = bool(args.admission_judgment)

    # v8.34:两者都不传 = BLOCK(治本 SVC-CORE-M001 · 删 v8.15 SKIPPED 兼容口子)
    # 旧调试/migration 路径仍可走 TEAMWORK_BYPASS_PREPARE_CHECK=1(SKILL.md § 暂停点协议)
    if not has_intent and not has_judgment:
        return {
            "verdict": "FAIL",
            "error": (
                "--user-intent + --admission-judgment 必传(v8.34 全局强制 · "
                "删 v8.15 SKIPPED 兼容口子 · 治本 SVC-CORE-M001 AI 跳过思考 case)"
            ),
            "hint": (
                "用法:state.py prepare-check ... "
                "--user-intent '<用户原话>' "
                "--admission-judgment '{"
                "\"sections_reviewed\":[\"§2.1\",\"§2.2\"],"
                "\"matched_signals\":[{\"section\":\"§2.1\",\"signal\":\"...\",\"evidence\":\"...\"}],"
                "\"recommended_flow_type\":\"Feature/Feature Planning/Bug/Micro\","
                "\"ai_rationale\":\"为什么这么判\"}'  "
                "· AI 必读 prepare.md §2.1/§2.2 才能写出 matched_signals + ai_rationale "
                "· 调试 bypass:TEAMWORK_BYPASS_PREPARE_CHECK=1"
            ),
            "payload_extras": {},
            "judgment": None,
            "consistency": "FAIL",
            "recommended_flow_type": None,
        }

    # 部分传 = 不一致 · BLOCK
    if has_intent != has_judgment:
        missing = "--admission-judgment" if has_intent else "--user-intent"
        return {
            "verdict": "FAIL",
            "error": f"--user-intent + --admission-judgment 必同传 · 缺 {missing}",
            "hint": (
                "两者一起才有意义:user-intent 是用户原话(留痕)· admission-judgment "
                "是 AI 读 prepare.md §2.1/§2.2 后的判断(matched_signals + recommended_flow_type)"
            ),
            "payload_extras": {},
            "judgment": None,
            "consistency": "FAIL",
            "recommended_flow_type": None,
        }

    # 都传了 · 校验 admission_judgment JSON schema
    try:
        judgment = json.loads(args.admission_judgment)
    except json.JSONDecodeError as e:
        return {
            "verdict": "FAIL",
            "error": f"--admission-judgment 不是合法 JSON: {e}",
            "hint": (
                "示例:--admission-judgment '{\"sections_reviewed\":[\"§2.1\",\"§2.2\"],"
                "\"matched_signals\":[{\"section\":\"§2.1\",\"signal\":\"方向级业务变更\","
                "\"evidence\":\"想做一个服务\"}],\"recommended_flow_type\":\"Feature Planning\","
                "\"ai_rationale\":\"...\"}'"
            ),
            "payload_extras": {},
            "judgment": None,
            "consistency": "FAIL",
            "recommended_flow_type": None,
        }

    # 校验 4 必填字段
    required_fields = [
        "sections_reviewed",       # list · ["§2.1", "§2.2"]
        "matched_signals",         # list · [{section, signal, evidence}]
        "recommended_flow_type",   # str · Feature / Feature Planning / Bug / Micro
        "ai_rationale",            # str · 自由文本 · AI 解释为什么这么判
    ]
    missing_fields = [f for f in required_fields if f not in judgment]
    if missing_fields:
        return {
            "verdict": "FAIL",
            "error": f"--admission-judgment 缺必填字段: {missing_fields}",
            "hint": (
                f"4 字段全需要(R0 物化:'你必须想这件事')· "
                f"sections_reviewed[](读了 prepare.md 哪些段)· "
                f"matched_signals[](命中信号 · 含 evidence)· "
                f"recommended_flow_type(你推荐什么 flow_type · 含 'Feature Planning')· "
                f"ai_rationale(为什么这么判 · 给用户/retro 复盘看)"
            ),
            "payload_extras": {},
            "judgment": judgment,
            "consistency": "FAIL",
            "recommended_flow_type": None,
        }

    # 校验 recommended_flow_type 是合法值
    legal_recommended = {
        "Feature", "Feature Planning", "Bug", "Micro", "问题排查",
    }
    rec = judgment.get("recommended_flow_type")
    if rec not in legal_recommended:
        return {
            "verdict": "FAIL",
            "error": f"admission_judgment.recommended_flow_type={rec!r} 非法",
            "hint": f"合法值: {sorted(legal_recommended)}",
            "payload_extras": {},
            "judgment": judgment,
            "consistency": "FAIL",
            "recommended_flow_type": rec,
        }

    # 校验 matched_signals 是 list of dict(基本 schema)· 内容由 AI 自由判
    sigs = judgment.get("matched_signals", [])
    if not isinstance(sigs, list):
        return {
            "verdict": "FAIL",
            "error": "admission_judgment.matched_signals 必须是 list",
            "hint": "格式:[{section: '§2.1', signal: '...', evidence: '...'}, ...]",
            "payload_extras": {},
            "judgment": judgment,
            "consistency": "FAIL",
            "recommended_flow_type": rec,
        }

    # consistency 校验:recommended_flow_type vs --flow-type
    extras: dict = {
        "user_intent": args.user_intent,
        "admission_judgment": judgment,
        "recommended_flow_type": rec,
    }
    if not args.flow_type:
        # --flow-type 未传 · 无法 consistency 校验 · 当 OK(向后兼容)· 留 audit
        extras["admission_consistency"] = "OK"
        extras["admission_consistency_note"] = (
            "未传 --flow-type · 无法 consistency 校验 · 推荐: " + rec
        )
        return {
            "verdict": "OK",
            "payload_extras": extras,
            "judgment": judgment,
            "consistency": "OK",
            "recommended_flow_type": rec,
        }

    if rec == args.flow_type:
        extras["admission_consistency"] = "OK"
        return {
            "verdict": "OK",
            "payload_extras": extras,
            "judgment": judgment,
            "consistency": "OK",
            "recommended_flow_type": rec,
        }

    # MISMATCH:WARN(不 BLOCK · R0 兜底)
    extras["admission_consistency"] = "MISMATCH"
    extras["admission_consistency_warning"] = (
        f"⚠️ admission_judgment.recommended_flow_type={rec!r} 与 --flow-type={args.flow_type!r} 不一致 · "
        f"AI 读 §2.1/§2.2 后判 {rec} · 但你选 {args.flow_type} · "
        f"在 prepare 暂停点必加 §2.1/§2.2 三选项让用户拍板(不要默认选 {args.flow_type} 跳过判据) · "
        f"audit 已留痕 · retro 可复盘"
    )
    return {
        "verdict": "OK",  # 不 BLOCK · 仅 WARN(R0:可能有合理例外)
        "payload_extras": extras,
        "judgment": judgment,
        "consistency": "MISMATCH",
        "recommended_flow_type": rec,
    }


def cmd_ci_commands(args: argparse.Namespace) -> None:
    """v8.348:扫出本仓 CI **真正会跑的门禁命令**,供 test stage 逐条对照。

    治的是「本地测试与 MR CI 不同构」——实证 case(aon-main DEV-F260830125314):
    TEST-REPORT 只记 `cargo check`(验编译),CI 跑 `cargo clippy -- -D warnings`,
    一条 lint 漏到 CI 才炸。而那个 AI **试过** grep,只是猜错了路径
    (真配置在 include 进来的 `infra/ci/api-gateway.yml`)→ 空结果被当成「没有 CI」。
    🔴 本命令**不要求本地跑全集**(有些 job 要 infra / 太慢)· 它只保证「你看见过」。
    """
    root = Path(getattr(args, "root", None) or ".").resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _v8_engine import scan_ci_commands
    found = scan_ci_commands(root)
    total = sum(len(v) for v in found.values())
    emit({
        "verdict": "OK", "command": "ci-commands", "root": str(root),
        "config_files": len(found), "gate_commands": total,
        "commands": {f: [{"line": ln, "cmd": c} for ln, c in cs] for f, cs in found.items()},
        "next_action": (
            "逐条标注 **本地已跑 / 跑不了(为什么)/ 本次不适用**,写进 TEST-REPORT §CI 对照。"
            "🔴 跑不了的也要写 —— 那就是「已知会在 CI 才发现」的清单(零也显式)。"
            if found else
            "未扫到 CI 配置(仓库可能没有 CI · 或布局非常规)—— TEST-REPORT §CI 对照写「无 CI 配置」。"),
        "note": "文本扫描 script/run 块里的门禁类命令(编译/测试/静态检查)· 不解析 job 图 · 部署类不收",
    })


def cmd_revise_plan(args: argparse.Namespace) -> None:
    """v8.343 显式修订点:按新证据改装配计划(**加减同价 · 各记一行证据**)。

    用户拍板:「渐进式的流程更合理 …… 或者至少可以修改」。取的是「计划 + 显式修订点」形态 ——
    计划仍在装配时一次给全(用户看得见整体形状 · 抗棘轮),但每个 stage 边界都是修订口:
    出现装配时不知道的事实 → 改;没出现 → 照计划走。

    三类不可修订(硬边界 · 见 goal-stage § 修订点):
      ① 用户主权点:已停等确认过的(PRD 终确认)· ship 本身 · 用户点名要过的评审点
      ② 硬不变式:模型错开 / PRD·TECH 高档(不进矩阵 · 既有机器门守)
      ③ 不可回溯放松:已产生的证据不能事后放松(dev 交了测试证据 → 不许改 evidence_gate=关)
    修订只影响**未走的部分**;已走的 stage 不重判。
    """
    state = load_state(args.feature)
    state_file = state_path(args.feature)

    plan = state.get("assembly_plan")
    if not plan:
        die(2, json.dumps({
            "verdict": "FAIL", "command": "revise-plan",
            "error": "本 feature 无 assembly_plan(存量 state 或 Bug 流)",
            "hint": ("Bug 流不走维度装配;存量 Feature 可用 change-review-roles 调评审面 · "
                     "环节偏离走 jump-to-stage --reason。"),
        }, ensure_ascii=False, indent=2))

    try:
        new_val = json.loads(args.to)
    except json.JSONDecodeError:
        new_val = args.to          # 标量维度允许裸传(spec_depth=prd / verify_depth=test)

    dims = plan.get("dims") or {}
    dim = args.dim
    # D4 的点式寻址:review.blueprint / review.pm_acceptance
    if dim.startswith("review."):
        point = dim.split(".", 1)[1]
        if point not in REVIEW_POINTS:
            die(2, json.dumps({
                "verdict": "FAIL", "command": "revise-plan",
                "error": f"评审点 {point!r} 非法", "legal": list(REVIEW_POINTS),
            }, ensure_ascii=False, indent=2))
        if isinstance(new_val, str):
            new_val = [r.strip() for r in new_val.split(",") if r.strip()]
        before = list((dims.get("review") or {}).get(point, []))
        candidate = merge_dims(dims, {"review": {point: new_val}})
    else:
        if dim not in ("spec_depth", "evidence_gate", "verify_depth", "ui"):
            die(2, json.dumps({
                "verdict": "FAIL", "command": "revise-plan",
                "error": f"维度 {dim!r} 非法",
                "legal": ["spec_depth", "evidence_gate", "verify_depth", "ui",
                          "review.<goal|blueprint|review|pm_acceptance>"],
            }, ensure_ascii=False, indent=2))
        before = dims.get(dim)
        candidate = merge_dims(dims, {dim: new_val})

    if before == new_val:
        emit({"verdict": "NOOP", "command": "revise-plan", "dim": dim,
              "current": before, "hint": "新值 == 现值 · 不写不 audit"})
        return

    # 🔴 顺序要紧:**不可回溯守卫先判**。放在一致性校验之后的话,降维天然带出的不连贯
    # 会先报「组合不连贯」——把人支去修 roster,而真正的答案是「这段你已经走过了」。
    # (守卫写了却走不到 = 本框架反复复发的「规则立了没接线」)
    done = set(state.get("completed_stages") or [])
    if dim == "evidence_gate" and new_val is False and "dev" in done:
        die(2, json.dumps({
            "verdict": "FAIL", "command": "revise-plan",
            "error": "dev 已完成并交付测试证据 · 不许回溯把 evidence_gate 改成关",
            "rule": "修订只影响未走的部分 · 已产生的证据不可回溯放松",
        }, ensure_ascii=False, indent=2))
    walked = [s for s in derive_chain(dims) if s in done]
    dropped = [s for s in walked if s not in derive_chain(candidate)]
    if dropped:
        die(2, json.dumps({
            "verdict": "FAIL", "command": "revise-plan",
            "error": f"该修订会把**已走过**的 stage 移出链:{dropped}",
            "hint": "修订只影响未走的部分 · 想重走某 stage 用 jump-to-stage --reason",
            "rule": "计划可改 · 历史不可改",
        }, ensure_ascii=False, indent=2))

    # 降维会让某些评审点**不再在链上**(如 spec_depth prd_tech→prd 之后 blueprint 冷审)。
    # 在**修订**处这是改维度的后果、不是误判 → 自动剪枝并在 emit 里报出来;
    # 在 **init** 处同样的配置是「AI 以为这个 stage 会跑」的误判 → validate_dims 照旧拒。
    _on = set(derive_chain(candidate))
    pruned = [p for p in (candidate.get("review") or {})
              if p in REVIEW_POINTS and p not in _on and (candidate["review"][p])]
    for p in pruned:
        candidate["review"].pop(p, None)

    bad = validate_dims(candidate)
    if bad:
        die(2, json.dumps({
            "verdict": "FAIL", "command": "revise-plan",
            "error": "修订后维度组合不连贯 · 拒绝", "violations": bad,
        }, ensure_ascii=False, indent=2))

    before_chain = derive_chain(dims)
    plan["dims"] = candidate
    after_chain = derive_chain(candidate)
    plan.setdefault("revisions", []).append({
        "at_stage": state.get("current_stage"),
        "dim": dim,
        "from": before,
        "to": new_val,
        # 🔴 evidence 是「装配时不知道的**事实**」· 不是「我觉得该加/该减」——
        # 加与减同价:两个方向都要这一行,轻的偏置留在档默认里,不留在举证难度里。
        "evidence": args.evidence,
        "at": now_iso(),
    })

    # roster 跟着计划走(链上评审点零也显式)
    roles = state.setdefault("stage_review_roles", {})
    on_chain = set(after_chain)
    for p, r in (candidate.get("review") or {}).items():
        if p in on_chain:
            roles[p] = list(r)
    for p in REVIEW_POINTS:
        if p in on_chain:
            roles.setdefault(p, [])

    atomic_write(state_file, state)
    emit({
        "verdict": "OK",
        "command": "revise-plan",
        "dim": dim, "before": before, "after": new_val,
        "evidence": args.evidence,
        "chain_before": before_chain,
        "chain_after": after_chain,
        "revisions_total": len(plan["revisions"]),
        "direction": ("加" if len(after_chain) > len(before_chain)
                      else "减" if len(after_chain) < len(before_chain) else "平"),
        "pruned_review_points": pruned,     # 降维带出的孤儿评审点(剪了要说 · 不静默)
        "hint": "修订已回显 · 不停等 · 按新计划继续(用户想调回一句即可)",
    })


def cmd_change_review_roles(args: argparse.Namespace) -> None:
    """v8.x:调整 stage_review_roles · 治本 raw-write 滥用(可枚举进脚本 · R0 哲学)。

    校验:
    - state.json 存在
    - stage 必在 LEGAL_STAGES
    - stage 必在 state.stage_review_roles(只能改已配置 stage · dev/ship 等无 review 配置 reject)
    - roles 必属 REVIEW_ROLE_ENUM(非空 · 至少 1 个)
    - reason 必填(audit)

    写入:
    - state.stage_review_roles[stage] = roles
    - state.stage_review_roles_adjustments append 一条 audit
    - 复用 stage-complete --next-stage-roles 的 audit 结构 · adjusted_via 字段区分来源

    NOOP:新值 == 现值 → 不写不 audit · 输出 verdict=NOOP。
    """
    state = load_state(args.feature)
    state_file = state_path(args.feature)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _v8_engine import REVIEW_ROLE_ENUM

    if args.stage not in LEGAL_STAGES:
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": f"--stage '{args.stage}' 不在 LEGAL_STAGES",
            "legal_stages": sorted(LEGAL_STAGES),
        }, ensure_ascii=False, indent=2))

    review_roles = state.setdefault("stage_review_roles", {})
    # v8.305:不再要求「stage 已在 dict 里」—— 那条让 fast_mode 下的用户**无法自救**
    # (fast 把 blueprint 从 dict 去掉 · 而门禁要 external · 想显式设空都被拒 → 只剩 bypass)。
    # 现在只校验 stage 是否**有评审语义**(engine 的 STAGES_WITH_REVIEW_ROLES_HINT 单源)。
    try:
        from _v8_engine import STAGES_WITH_REVIEW_ROLES_HINT as _REVIEWABLE
    except ImportError:
        _REVIEWABLE = set(review_roles.keys())
    if args.stage not in _REVIEWABLE:
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": f"stage '{args.stage}' 没有评审语义(无 reviewer 席位可调)",
            "hint": f"可调 stages: {sorted(_REVIEWABLE)}",
        }, ensure_ascii=False, indent=2))

    # v8.305:**允许显式清空**(`--roles ''` / `--roles none`)—— 「本 stage 不评审」是合法配置,
    # 原来把它当参数错误拒掉,等于只能加不能减。
    _raw = (args.roles or "").strip().lower()
    if _raw in ("", "none", "[]", "-"):
        roles_list = []
    else:
        roles_list = [r.strip() for r in args.roles.split(",") if r.strip()]
        if not roles_list:
            roles_list = []

    invalid = [r for r in roles_list if r not in REVIEW_ROLE_ENUM]
    if invalid:
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": f"--roles 含非法角色: {invalid}",
            "hint": f"REVIEW_ROLE_ENUM = {sorted(REVIEW_ROLE_ENUM)}",
        }, ensure_ascii=False, indent=2))

    # v8.305:允许 stage 尚未在 dict 里(放宽守卫后必须跟着改)—— 缺失视作空 roster
    before = list(review_roles.get(args.stage, []))

    # v8.66:yolo 去 external 评审 = 拆无人值守唯一安全网 → 默认禁止(非必要不得去)
    # 治本 case(WS-002 yolo):AI 把 yolo 当"简化/提速" · change-review-roles 去 goal/blueprint
    # external 美其名"集中到 review stage" —— 无人值守下这是拆掉唯一跨模型把关 · 反了。
    if (state.get("yolo") and "external" in before and "external" not in roles_list
            and not getattr(args, "accept_external_removal", False)):
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": (
                f"yolo 模式禁止从 {args.stage} 去掉 external 异质模型评审 —— "
                f"无人值守下 external 是**唯一安全网** · 非必要不得去"
            ),
            "hint": (
                "🔴 yolo 不是简化/提速 · 是无人值守下**更严**的自动把关:\n"
                "  ① 优先:别去 external · 让 external 评审照常跑(CLI 真不可用先重试 / 修环境)\n"
                "  ② 仅当 external CLI 客观不可用(未装 / 网络死 · 已重试失败)才加 "
                "--accept-external-removal --reason '<具体技术原因 + 重试失败证据>'\n"
                "  🔴 不得以「集中到 review 代码 stage」「效率」「价值低」为由去 external "
                "(= 擅自简化 · 违 yolo 加重审核原则)"
            ),
            "rule": "v8.66 yolo 加重审核 · 非必要不得去 external(SKILL.md § yolo)",
        }, ensure_ascii=False, indent=2))

    # v8.305:stage 键**本就不存在** + 目标为空 → 不是 NOOP,是**把「不评审」显式物化**
    # (原来靠键缺失表达意图 · 而缺失读不出「有意」还是「忘了」· 同本版 fast_mode 的修法)
    _materialize_empty = (args.stage not in review_roles and not roles_list)
    if before == roles_list and not _materialize_empty:
        emit({
            "verdict": "NOOP",
            "command": "change-review-roles",
            "stage": args.stage,
            "current_roles": roles_list,
            "hint": "新值 == 现值 · 不写不 audit",
        })
        return

    review_roles[args.stage] = roles_list
    audit_entry = {
        "stage": args.stage,
        "before": before,
        "after": roles_list,
        "reason": args.reason,
        "adjusted_at": now_iso(),
        "adjusted_via": "change-review-roles",
    }
    state.setdefault("stage_review_roles_adjustments", []).append(audit_entry)

    # v8.66:yolo 去 external(已 --accept-external-removal 放行)→ concern WARN 留痕(retro 复盘拆安全网)
    if state.get("yolo") and "external" in before and "external" not in roles_list:
        state.setdefault("concerns", []).append(
            f"{now_iso()} WARN yolo 去 external@{args.stage}(无人值守拆唯一跨模型安全网)· "
            f"reason: {args.reason}"
        )

    atomic_write(state_file, state)

    emit({
        "verdict": "OK",
        "command": "change-review-roles",
        "stage": args.stage,
        "before": before,
        "after": roles_list,
        "reason": args.reason,
        "next_action_hint": (
            f"已更新 state.stage_review_roles.{args.stage} · "
            f"后续 {args.stage}-complete 校验 reviewers 必含 {sorted(roles_list)}"
        ),
    })


# ─── external 第三视角冷审(v8.291 起唯一形态 = 错开模型 subagent · 本模块只出配方不 exec)──

# 可跑外审的 stage(v8.293:原 EXTERNAL_STAGE_TO_PROFILE 三层 dict 折叠 —— codex-agents/
# 已删、三个 stage 的 claude profile 本就全是同一个 reviewer.md · 嵌套只剩形式)
EXTERNAL_REVIEW_STAGES = ("goal", "blueprint", "review")
EXTERNAL_REVIEWER_PROFILE = "reviewer.md"  # claude-agents/ 下唯一模板

def _find_prior_external_review(feature_dir: Path, stage: str):
    """v8.191:找上一轮 external 结果文件 + 它评过的 commit → (path, target_commit) · 无 → None。"""
    d = feature_dir / "external-cross-review"
    if not d.is_dir():
        return None
    best = None
    for f in d.glob(f"{stage}-*.md"):
        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:2000]
        except OSError:
            continue
        m = re.search(r"^target_commit:\s*(\S+)", head, re.M)
        if m and (best is None or f.stat().st_mtime > best[0]):
            best = (f.stat().st_mtime, f, m.group(1))
    return (best[1], best[2]) if best else None


STAGE_REVIEW_FILES = {
    "goal":      ["PRD.md"],
    "blueprint": ["TC.md", "TECH.md"],
    "review":    [],  # review 模式靠 git diff · 不 inline 文件
}

# stage → reviewer target type(reviewer.md {target} 占位符)
STAGE_TO_REVIEW_TARGET = {
    "goal":      "prd",
    "blueprint": "blueprint",
    "review":    "code",
}

# v8.43:防 argv ARG_MAX 超限 · 单文件最大 inline 字节数
EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE = 60 * 1024  # 60KB


def _gather_review_files_for_claude(stage: str, feature_dir: Path) -> tuple[str, list[dict]]:
    """v8.43:把 stage 待评审文件内容 inline 成单 str(填充 reviewer.md {file_list} 占位符)。

    返 (inline_block, files_meta):
      - inline_block:" ### PRD.md\\n```\\n<content>\\n```\\n\\n### TC.md\\n..."
      - files_meta:[{name, exists, bytes, truncated?}] · 供 emit audit

    设计:
    - 超 60KB 单文件 truncate + emit metadata 告诉 reviewer 截断了
    - 缺失文件 emit 警告但不 BLOCK(reviewer 自己决定如何处理)
    - review stage 不 inline 文件(走 git diff 模式 · 由 codex 路径处理 · claude 路径目前不支持)
    """
    targets = STAGE_REVIEW_FILES.get(stage, [])
    if not targets:
        return ("(本 stage 不 inline 文件 · 由 reviewer 按外部 context 判断)", [])
    blocks: list[str] = []
    meta: list[dict] = []
    for fname in targets:
        fpath = feature_dir / fname
        info: dict = {"name": fname, "exists": fpath.exists()}
        if not fpath.exists():
            blocks.append(f"### {fname}\n_(文件不存在 · reviewer 视情况处理)_\n")
            info["bytes"] = 0
            meta.append(info)
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            blocks.append(f"### {fname}\n_(读取失败:{e})_\n")
            info["bytes"] = 0
            info["read_error"] = str(e)
            meta.append(info)
            continue
        info["bytes"] = len(content.encode("utf-8"))
        if info["bytes"] > EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE:
            # 按 byte 截断 + 标记 truncated(reviewer 看到提示自行判断完整性)
            truncated = content.encode("utf-8")[
                :EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE
            ].decode("utf-8", errors="ignore")
            content = (truncated + f"\n\n... [v8.43 truncated · 原文 {info['bytes']} bytes "
                                    f"超 {EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE} bytes 阈值] ...")
            info["truncated"] = True
        blocks.append(f"### {fname}\n```\n{content}\n```\n")
        meta.append(info)
    return ("\n".join(blocks), meta)


def _new_prompt_doc_path(feature_dir: Path, stage: str, model: str,
                         ts: Optional[str] = None) -> Path:
    """v8.136:每轮唯一 prompt-doc 路径(治 v8.44 固定名跨轮隐式复用 → stale review)。

    `<feature_dir>/external-review-prompts/<stage>-<model>-<UTC紧凑时间戳>.md`
    审计 = 输入(本轮实际跑的 prompt 即本文件)· 旧轮留档不复用 · 随 feature 归档。
    case PTR-F260611065743:round 1 的审计副本(固定名)被 round 2 当 prompt 优先读 →
    评审 stale PRD;手工删 doc 后 round 3 又写回 → round 4 必复发。唯一命名根治。
    """
    if ts is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return feature_dir / "external-review-prompts" / f"{stage}-{model}-{ts}.md"


def _extract_prompt_body(template_text: str) -> str:
    """v8.136:从 claude-agents/reviewer.md 模板只取「## Prompt 主体」fenced block 内文本。

    治 v8.43 fallback 拿**整文件**做占位符替换的双嵌 bug:模板尾部「占位符说明」表含
    `{file_list}` 示例格 · 全局 replace 把完整 PRD 再灌进表格单元格 → prompt 含模板元说明 +
    对照表 + 双份 PRD(~400 行垃圾 · 加重长 prompt 卡)。找不到标记 → 原样返回(兼容自定义模板)。
    """
    i = template_text.find("## Prompt 主体")
    if i == -1:
        return template_text
    fence = template_text.find("```", i)
    if fence == -1:
        return template_text
    start = template_text.find("\n", fence)
    if start == -1:
        return template_text
    start += 1
    end = template_text.find("\n```", start)
    if end == -1:
        return template_text
    return template_text[start:end]



def cmd_set_mode(args: argparse.Namespace) -> None:
    """v8.69:语义化设 auto_mode / yolo(替代 raw-write · 物化 + audit)。

    治本 case(SVC-PLATFORM-F060 · Codex agent 提):改 auto_mode 只能 raw-write ·
    audit 里出现 raw-write 不理想。本命令把开关 + yolo 非主分支 gate + audit 收进脚本。

    flag:
      --auto-mode / --no-auto-mode    开/关 auto_mode(互斥)
      --yolo [<branch>] / --no-yolo    开/关 yolo(互斥)· yolo implies auto_mode ·
                                       <branch> = 专属 merge_target(覆盖 · 非主分支 gate)
      --reason 必填(audit)
    """
    state = load_state(args.feature)
    state_file = state_path(args.feature)

    if args.auto_mode and args.no_auto_mode:
        die(2, json.dumps({"verdict": "FAIL", "command": "set-mode",
                           "error": "--auto-mode 与 --no-auto-mode 互斥"},
                          ensure_ascii=False, indent=2))
    if args.yolo is not None and args.no_yolo:
        die(2, json.dumps({"verdict": "FAIL", "command": "set-mode",
                           "error": "--yolo 与 --no-yolo 互斥"},
                          ensure_ascii=False, indent=2))
    if not (args.auto_mode or args.no_auto_mode
            or args.yolo is not None or args.no_yolo):
        die(2, json.dumps({
            "verdict": "FAIL", "command": "set-mode",
            "error": "未指定任何变更",
            "hint": "至少一个:--auto-mode / --no-auto-mode / --yolo [<branch>] / --no-yolo",
        }, ensure_ascii=False, indent=2))

    before = {"auto_mode": bool(state.get("auto_mode")),
              "yolo": bool(state.get("yolo")),
              "merge_target": state.get("merge_target")}
    new_auto, new_yolo, new_mt = (before["auto_mode"], before["yolo"],
                                  before["merge_target"])

    # yolo
    yolo_branch = (args.yolo if isinstance(args.yolo, str) and args.yolo.strip()
                   else None)
    if args.yolo is not None:  # 开 yolo
        new_yolo = True
        new_auto = True  # yolo implies auto_mode
        if yolo_branch:
            new_mt = yolo_branch
        if _is_main_branch(new_mt):
            die(2, json.dumps({
                "verdict": "FAIL", "command": "set-mode",
                "error": f"yolo merge_target 必须非主分支(当前 {new_mt!r})—— "
                         f"yolo 无人 review 自动 merge · 不得直接进 main/master/默认分支",
                "hint": "用 --yolo <非主分支>(如 dev/staging)· 或先改 merge_target",
                "rule": "v8.63/69 yolo 硬约束 · 自动 merge 不进 main",
            }, ensure_ascii=False, indent=2))
        # v8.349:中途切 yolo 与 init-feature 同约束 —— 否则「先普通启动、再 set-mode 切 yolo」
        # 就是绕过两段式的现成口子(同一个门必须守住所有入口)
        if not _is_yolo_branch(new_mt):
            die(2, json.dumps({
                "verdict": "FAIL", "command": "set-mode",
                "error": f"yolo 的 merge_target 必须是 `yolo/` 前缀的隔离分支 · got {new_mt!r}",
                "hint": (f"--yolo yolo/{(new_mt or 'integration').strip().lstrip('/') or 'integration'}"
                         " · 两段式:feature → yolo/*(自动 · 记待确认项)→ 真 target(人工确认)"),
                "rule": "v8.349 yolo 两段式(用户拍板)· 所有入口同约束",
            }, ensure_ascii=False, indent=2))
    elif args.no_yolo:
        new_yolo = False

    # auto_mode(yolo=True 强制 auto=True)
    if args.auto_mode:
        new_auto = True
    if args.no_auto_mode:
        if new_yolo:
            die(2, json.dumps({
                "verdict": "FAIL", "command": "set-mode",
                "error": "yolo 开启时不能关 auto_mode(yolo implies auto_mode)",
                "hint": "先 --no-yolo · 再 --no-auto-mode",
            }, ensure_ascii=False, indent=2))
        new_auto = False

    after = {"auto_mode": new_auto, "yolo": new_yolo, "merge_target": new_mt}
    if after == before:
        emit({"verdict": "NOOP", "command": "set-mode",
              "current": before, "hint": "新值 == 现值 · 不写不 audit"})
        return

    state["auto_mode"] = new_auto
    state["yolo"] = new_yolo
    if new_mt != before["merge_target"]:
        state["merge_target"] = new_mt
        state.setdefault("worktree", {})["base_branch"] = f"origin/{new_mt}"
        ec = state.setdefault("environment_config", {})
        ec["merge_target"] = new_mt
        ec["base"] = f"origin/{new_mt}"

    state.setdefault("mode_changes", []).append({
        "at": now_iso(), "before": before, "after": after,
        "reason": args.reason, "via": "set-mode",
    })
    # yolo 开启 = 高风险 · 额外 concern WARN(audit 显著)
    if new_yolo and not before["yolo"]:
        state.setdefault("concerns", []).append(
            f"{now_iso()} WARN yolo 开启 via set-mode · merge_target={new_mt} · "
            f"reason: {args.reason}")

    atomic_write(state_file, state)
    emit({
        "verdict": "OK", "command": "set-mode",
        "before": before, "after": after, "reason": args.reason,
        "next_action_hint": (
            "yolo 开启 · 严格按流程 · 不得简化/内化(详 SKILL.md § yolo)"
            if new_yolo and not before["yolo"]
            else "auto_mode/yolo 已更新 · audit 写入 state.mode_changes"),
    })



def _is_ancestor(ancestor: str, commit: str, cwd: str) -> bool:
    """`git merge-base --is-ancestor`:ancestor 是 commit 的祖先(或相等)→ True。

    v8.161:external-review 用它校验 review_base_commit 是否真在 review 目标 commit 的
    历史里 —— 是才用作增量 diff base · 否则兜底 merge_target。任何 git 失败(无 ref /
    非 repo / git 缺失)→ False(安全:回退到 merge_target 既有行为 · 绝不因锚点失效而 BLOCK)。
    """
    try:
        r = subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, commit],
                           capture_output=True, text=True, cwd=cwd)
        return r.returncode == 0
    except (FileNotFoundError, OSError):
        return False


def _resolve_external_base(state: dict, stage: str, commit: str,
                           feature_dir: Path) -> tuple[str, str]:
    """第三视角冷审的 diff 基线(v8.291 保留 v8.161 不变式 · 从原内联逻辑抽出)。

    - **仅 review stage** 用 `state.review_base_commit`(pre-dev HEAD · 增量评审锚)· goal/blueprint 忽略它;
    - 且它必须是 `commit` 的**祖先** —— 否则(分支重开 / rebase / 锚过期)回退 `merge_target`,
      避免给出一个算不出 diff 的假基线。
    """
    def _is_ancestor(a: str, b: str) -> bool:
        if not (a and b):
            return False
        r = subprocess.run(["git", "-C", str(feature_dir), "merge-base", "--is-ancestor", a, b],
                           capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    anchor = state.get("review_base_commit") or ""
    if stage == "review" and anchor and _is_ancestor(anchor, commit):
        return anchor, "review_base_commit"
    return (state.get("merge_target") or ""), "merge_target"


def cmd_external_review(args: argparse.Namespace) -> None:
    """v8.291:第三视角冷审 = **错开模型 subagent**(唯一形态 · 跨厂商 CLI 异质已彻底退役)。

    退役理由(用户拍板):跨厂商 CLI(codex / gemini)冷启动 + 安全审查慢路径 + 登录/网络故障面,
    实测严重拖慢流程(台账见 codex 挂死 98m / "Additional safety checks" 慢路径);而**同厂商模型错开**
    (会话 fable5 → 外审 opus)已能拿到独立采样的主要收益 —— 上下文隔离(冷审)+ 权重错开,零 CLI 成本。

    本命令不再 exec 任何子进程,只做三件事:① 组装评审 prompt(含待评审文件 inline)② 落 prompt 文档
    ③ emit subagent 配方(**model 必须 ≠ 会话主模型**)。产出由主对话写入 external-cross-review/。
    """
    feature_dir = Path(args.feature).resolve()
    state = load_state(args.feature)
    feature_id = state.get("feature_id") or feature_dir.name
    skill_root = Path(__file__).resolve().parent.parent

    if args.stage not in EXTERNAL_REVIEW_STAGES:
        emit({"verdict": "FAIL", "command": "external-review",
              "error": f"stage={args.stage!r} 无对应评审 profile",
              "known_stages": sorted(EXTERNAL_REVIEW_STAGES)})
        sys.exit(1)

    # commit / base:显式参数 > state 的 stage auto_commit > HEAD
    commit = args.commit or (state.get("stage_contracts", {})
                             .get(args.stage, {}).get("auto_commit"))
    if not commit:
        r = subprocess.run(["git", "-C", str(feature_dir), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        commit = r.stdout.strip() if r.returncode == 0 else ""
    if args.base:
        base, base_source = args.base, "explicit"
    else:
        base, base_source = _resolve_external_base(state, args.stage, commit, feature_dir)

    verify_fixes = bool(getattr(args, "verify_fixes", False))
    prior = _find_prior_external_review(feature_dir, args.stage) if verify_fixes else None
    if verify_fixes and not prior:
        emit({"verdict": "FAIL", "command": "external-review",
              "error": "--verify-fixes 找不到上一轮 external 结果"
                       "(external-cross-review/*.md 含 target_commit)",
              "hint": "先跑一次全量外审 · 或去掉 --verify-fixes"})
        sys.exit(1)

    # 评审 prompt(host-agnostic 模板 + 待评审文件 inline)
    try:
        tpl = _extract_prompt_body((skill_root / "claude-agents" / EXTERNAL_REVIEWER_PROFILE).read_text(encoding="utf-8"))
    except OSError:
        tpl = "You are an independent reviewer. Review the following and output a markdown review."
    file_list_block, _meta = _gather_review_files_for_claude(args.stage, feature_dir)
    sub_prompt = (tpl.replace("{stage}", args.stage)
                     .replace("{target}", STAGE_TO_REVIEW_TARGET.get(args.stage, args.stage))
                     .replace("{feature_name}", feature_id)
                     .replace("{file_list}", file_list_block))
    if verify_fixes and prior:
        sub_prompt += (f"\n\n---\n🔴 增量重验轮:上一轮评审见 {prior[0].name}(评的是 {prior[1]})· "
                       f"本轮只做两件事:① 逐条裁决上轮 open finding(fixed/not-fixed · 带依据)"
                       f"② 只回归审查 {prior[1]}..{commit} 的修复 diff 引入的新问题。禁全量重扫。\n")

    suffix = "fixverify" if verify_fixes else "review"
    prompt_doc = _new_prompt_doc_path(feature_dir, args.stage, f"subagent-{suffix}")
    try:
        prompt_doc.parent.mkdir(parents=True, exist_ok=True)
        prompt_doc.write_text(sub_prompt, encoding="utf-8")
    except OSError:
        pass

    target_file = f"external-cross-review/{args.stage}-<model>{'-fixverify' if verify_fixes else ''}.md"
    emit({
        "verdict": "SUBAGENT_RECIPE",
        "command": "external-review",
        "stage": args.stage,
        "target_commit": commit,
        "target_base": base,
        "base": base,          # 兼容键(v8.161 测试与旧消费方)
        "base_source": base_source,
        "prompt_doc": str(prompt_doc),
        "target_file_pattern": str(feature_dir / target_file),
        "next_action": (
            "🎭 **第三视角冷审 = 错开模型 subagent**(v8.291 · 跨厂商 CLI 异质已退役 · 本命令不 exec 子进程):\n"
            f"  1. 起 Agent subagent(isolated context)· 🔴 **model 参数必须 ≠ 会话主模型**"
            "· 🔴 **必须有文件读取能力**(要读真实代码/上游 WS —— 本配方只 inline 部分文件:"
            "goal→PRD · blueprint→TC/TECH · review→无)· "
            "零工具 reviewer profile 会返 `files_read: []` 并阻塞整个 stage(v8.304)"
            "(如 fable5 会话 → `model: opus`)· prompt = 读 " + str(prompt_doc) + " 的内容"
            "(评审指令 + 待评审文件已 inline · **不喂主对话起草心路**)\n"
            "  2. 把 subagent 产出写到 `external-cross-review/" + args.stage + "-<实际模型>"
            + ("-fixverify" if verify_fixes else "") + ".md` · frontmatter 必含:\n"
            "       review_model: <subagent 实际用的模型 · 照实写>\n"
            "       review_via: subagent\n"
            "       files_read: [<实际读过的文件 · 空 = 能力缺失 · 门禁判 CAPABILITY_BLOCKED>]\n"
            f"       target_commit: {commit}\n"
            "       coverage: [<本次实际覆盖的方向>]\n"
            "  3. `" + args.stage + "-complete` 门禁校验:产物非空 + `review_via: subagent` + coverage 申报。\n"
            "  🔴 **禁主对话自评**(热审 = 同上下文 = 无独立性)· **禁伪造/冒充**(照实写实际模型)。"
        ),
        "spec": "standards/external-model-usage.md(裁决纪律 §二)· 模型错开不变式见 SKILL 🎚️",
    })


# ─── v8.24-v8.41 · update-skill → v8.42 已抽到独立 tools/update.py ────────
# 历史:v8.24 加 cmd_update_skill in state.py(git pull) · v8.41 重写 tarball download
# v8.42(用户拍板 2026-05-27 · "更新文件本身是否有必要单独一个 python"):
# - 抽到独立 tools/update.py(职责分离 · 与 bootstrap.py pattern 对齐)
# - 治本"元工具混运行时"+ chicken-and-egg(state.py 坏掉 · update.py 仍能救命)
# - 用法:python3 SKILL_ROOT/tools/update.py [--channel <branch>] [--accept-overwrite]


def cmd_audit_raw_writes(args: argparse.Namespace) -> None:
    """v8.12:跨 Feature 汇总所有 raw-write 历史 · 帮助识别状态机缺口。

    扫 --features-root 下所有 state.json · 抓 concerns 中 raw-write 条目 · 聚合统计。
    """
    import re

    root = Path(args.features_root or "docs/features").resolve()
    if not root.exists():
        die(1, json.dumps({
            "verdict": "FAIL",
            "command": "audit-raw-writes",
            "error": f"features_root 不存在: {root}",
            "hint": "用 --features-root <绝对路径> 指定 · 默认 docs/features",
        }, ensure_ascii=False, indent=2))

    by_feature: dict[str, dict] = {}
    by_field: dict[str, int] = {}
    total = 0
    saved = os.environ.get(CHECKSUM_BYPASS_ENV)
    os.environ[CHECKSUM_BYPASS_ENV] = "1"
    try:
        for state_json in root.rglob("state.json"):
            try:
                state = json.loads(state_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            feature_name = state_json.parent.name
            concerns = state.get("concerns") or []
            rw = [c for c in concerns if isinstance(c, str) and "raw-write" in c]
            if not rw:
                continue
            by_feature[feature_name] = {
                "count": len(rw),
                "occurrences": rw,
            }
            total += len(rw)
            # 粗 extract 字段(reason 中"current_stage" 等)
            for c in rw:
                # raw-write 自身写的:"raw-write 跳过校验 · 改动 N 字段 · 理由:..."
                # 不含字段名 · 但 reason 可能含 · 简单抓 typical fields
                for field_hint in (
                    "current_stage", "legal_next_stages", "completed_stages",
                    "stage_contracts", "ship", "evidence", "rounds",
                ):
                    if field_hint in c:
                        by_field[field_hint] = by_field.get(field_hint, 0) + 1
    finally:
        if saved is None:
            del os.environ[CHECKSUM_BYPASS_ENV]
        else:
            os.environ[CHECKSUM_BYPASS_ENV] = saved

    # frequency hint
    freq_alert = []
    for field, cnt in sorted(by_field.items(), key=lambda x: -x[1]):
        if cnt >= 2:
            freq_alert.append(
                f"{field}: {cnt} 次 · 频次 ≥2 → 提示状态机有专用命令缺口"
            )

    emit({
        "verdict": "OK",
        "command": "audit-raw-writes",
        "features_root": str(root),
        "total_raw_writes": total,
        "feature_count": len(by_feature),
        "by_feature": by_feature,
        "by_field_frequency": dict(sorted(by_field.items(), key=lambda x: -x[1])),
        "frequency_alert": freq_alert,
        "hint": (
            "v8.x 后任何 raw-write 都应视作状态机缺口信号 · 复查每条 reason → 治本:\n"
            "  - current_stage → state.py jump-to-stage(v8.11+)\n"
            "  - stage_contracts.X.evidence → 检查 stage-complete 是否漏持久化(v8.8 治本通用)\n"
            "  - legal_next_stages → 一般是 jump-to-stage 后副产物\n"
            "  - 其他 → 报 bug 或确认是否真异常"
        ),
    })


def cmd_jump_to_stage(args: argparse.Namespace) -> None:
    """v8.11:跳到任意合法 stage · 替代 raw-write current_stage 滥用。

    典型 case:pm_acceptance rejected_with_feedback · 用户选回 goal 改 PRD / 回 ui_design 改 UI。

    校验:
    - --to 必须在 LEGAL_STAGES
    - --to 必须在当前 flow_type 的 FLOW 表(防跳到该 flow 不存在的 stage)
    - --to != current_stage(防 no-op)
    - ship 后(ship.phase=pushed · 远程已动)不可跳 · 状态不可逆

    动作:
    - current_stage = --to
    - legal_next_stages = flow_graph[--to]
    - --to 的 contract gates 重置(允许重做)+ restarted_at / restarted_from / restarted_reason
    - 加 concerns WARN(audit)
    - completed_stages 不动(保留历史)
    """
    # 正常走 checksum 校验:state.json 被外改时 die + 提示先 recover(认证 + audit)再跳转
    path = state_path(args.feature)
    state = load_state(args.feature)

    target = args.to
    current = state.get("current_stage")

    # 1. enum 校验
    if target not in LEGAL_STAGES:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"--to={target!r} 不在 LEGAL_STAGES",
            "legal_stages": sorted(LEGAL_STAGES),
        }, ensure_ascii=False, indent=2))

    # 2. 当前 flow_type 必须含 target stage
    flow_type = state.get("flow_type")
    flow_graph = resolve_flow_graph(flow_type, getattr(args, "preset", None) or "full")
    if not flow_graph:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"flow_type={flow_type!r} 无 FLOW 表(不进状态机的流程不支持 jump)",
        }, ensure_ascii=False, indent=2))
    if target not in flow_graph:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"--to={target!r} 不在 flow_type={flow_type!r} 的 FLOW 表",
            "valid_stages_for_flow": sorted(flow_graph.keys()),
        }, ensure_ascii=False, indent=2))

    # 3. ship 后不可跳 —— 唯一例外(用户拍板):MR 窗口期(pushed · 平台未合并)
    # 发现问题 → 同 feature 回 dev 修复(不开 Bug 流)· 修完 push 重跑更新同一 MR。
    ship_phase = (state.get("ship") or {}).get("phase")
    if ship_phase == "pushed":
        reason = (getattr(args, "reason", None) or "").strip()
        if target == "dev" and reason:
            ship = state.setdefault("ship", {})
            ship.setdefault("reopened_fixes", []).append(
                {"at": now_iso(), "reason": reason})
            state.setdefault("concerns", []).append(
                f"{now_iso()} WARN mr-window-reopen: pushed → dev · reason: {reason} · "
                "修完 dev/test 证据门照跑 → ship-phase --action push 重跑(rerecord)更新同一 MR")
        elif target == "dev":
            die(1, json.dumps({
                "verdict": "FAIL",
                "action": "jump-to-stage",
                "error": "MR 窗口期回 dev 修复必须带 --reason(一句:修什么 · audit 留痕)",
                "hint": "state.py jump-to-stage --to dev --reason 'MR 修复:<blocker 一句>'",
            }, ensure_ascii=False, indent=2))
        else:
            die(1, json.dumps({
                "verdict": "FAIL",
                "action": "jump-to-stage",
                "error": f"Ship 后不可跳到 {target!r} · ship.phase={ship_phase!r}",
                "hint": (
                    "MR 未合并要修代码 → `jump-to-stage --to dev --reason '...'`(唯一放行口 · "
                    "留痕 · 修完 push 重跑更新同一 MR);已合并后的问题 → 开 Bug 流(diagnose 起);"
                    "整件放弃 → ship-phase --action close-unmerged"
                ),
            }, ensure_ascii=False, indent=2))

    # 4. target == current(no-op)
    if target == current:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"--to={target!r} 与 current_stage 相同 · no-op",
        }, ensure_ascii=False, indent=2))

    # 5. 改 current_stage + legal_next_stages
    state["current_stage"] = target
    state["legal_next_stages"] = flow_graph.get(target, [])

    # 6. 重置 target stage contract gates(允许重做 + audit 留痕)
    contracts = state.setdefault("stage_contracts", {})
    target_contract = contracts.setdefault(target, {})
    target_contract["input_satisfied"] = False
    target_contract["process_satisfied"] = False
    target_contract["output_satisfied"] = False
    target_contract.pop("completed_at", None)
    target_contract.pop("duration_minutes", None)
    target_contract["restarted_at"] = now_iso()
    target_contract["restarted_from_stage"] = current
    target_contract["restarted_reason"] = args.reason

    # 7. 加 concerns WARN
    state.setdefault("concerns", []).append(
        f"{now_iso()} WARN jump-to-stage: {current!r} → {target!r} · reason: {args.reason}"
    )

    # 8. completed_stages 不动(保留历史 · 不像 reset-prev 去尾)
    state["updated_at"] = now_iso()
    state["updated_by"] = "jump-to-stage"
    atomic_write(path, state)

    emit({
        "verdict": "OK",
        "action": "jump-to-stage",
        "from_stage": current,
        "to_stage": target,
        "reason": args.reason,
        "legal_next_stages": state["legal_next_stages"],
        "completed_stages": state.get("completed_stages", []),
        "next_action_brief": (
            f"## jump-to-stage 完成\n\n"
            f"已跳:{current!r} → {target!r}\n"
            f"contract 重置:{target} 三 gate 全 false · 可跑 {target}-start 重做。\n\n"
            f"下一步:`state.py {target}-start --feature {args.feature}`\n\n"
            f"⚠️ 已自动追 concerns WARN(audit 透明)· completed_stages 不变。"
        ),
    })


def cmd_recover(args: argparse.Namespace) -> None:
    """Re-checksum after manual edit · adds concern WARN · 留 audit trail."""
    saved = os.environ.get(CHECKSUM_BYPASS_ENV)
    os.environ[CHECKSUM_BYPASS_ENV] = "1"
    try:
        path = state_path(args.feature)
        state = json.loads(path.read_text(encoding="utf-8"))
    finally:
        if saved is None:
            del os.environ[CHECKSUM_BYPASS_ENV]
        else:
            os.environ[CHECKSUM_BYPASS_ENV] = saved

    old_cs = state.get(CHECKSUM_FIELD)
    # concerns 统一字符串格式 "<ISO> <SEVERITY> <msg>"(与 add-concern / reset-prev 等一致 · 防混型)
    state.setdefault("concerns", []).append(
        f"{now_iso()} WARN state.json checksum recovered after manual edit · reason: {args.reason}"
    )
    atomic_write(path, state)
    emit({
        "verdict": "OK",
        "action": "recover",
        "feature": args.feature,
        "old_checksum_prefix": old_cs[:24] if old_cs else None,
        "new_checksum_prefix": state[CHECKSUM_FIELD][:24],
        "reason": args.reason,
        "concerns_appended": True,
    })


class JsonErrorArgumentParser(argparse.ArgumentParser):
    """argparse 参数错误也 emit JSON(治本 AI `state.py xxx | json.load` 管道遇参数错误炸 Traceback)。

    argparse 默认 error() 打 usage 到 stderr(非 JSON)· state.py 其它输出都是 JSON ·
    此子类让参数错误也结构化 · 保证 state.py 全部输出可被 json.load。
    add_subparsers 默认 parser_class = type(主 parser) · 所有子命令自动继承。
    """

    def error(self, message: str):  # noqa: D102
        payload = {
            "verdict": "FAIL",
            "error": f"参数错误: {message}",
            "command": self.prog,
            "usage": self.format_usage().strip(),
            "hint": "补全缺失 / 修正参数后重试 · 各参数说明见 `<command> --help`",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(2)


def _add_feature_arg(parser: argparse.ArgumentParser, *, help_text: str | None = None) -> None:
    """统一注册 --feature · 缺省时从 TEAMWORK_FEATURE 环境变量读取（v7.3.10+P0-130 ergonomics）。"""
    env = os.environ.get("TEAMWORK_FEATURE")
    parser.add_argument(
        "--feature",
        required=(env is None),
        default=env,
        help=help_text or ("artifact_root（含 state.json 的目录）"
                           + (f" · 默认从 $TEAMWORK_FEATURE={env}" if env else "")),
    )

def build_parser() -> argparse.ArgumentParser:
    p = JsonErrorArgumentParser(prog="state.py", description="Teamwork state.json tool (P1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("snapshot", aliases=["status"],
                        help="返回精简关注字段（cite-friendly · 看当前 stage/下一步 · 别名 status · compact 恢复用）")
    _add_feature_arg(sp)
    sp.add_argument("--tier", choices=["core", "stage", "full"], default="core")
    sp.add_argument("--cite", help="额外关注字段，逗号分隔的 dotted path")
    sp.set_defaults(func=cmd_snapshot)

    vp = sub.add_parser("validate", help="schema + 状态机 + evidence-binding 全量校验")
    _add_feature_arg(vp)
    vp.set_defaults(func=cmd_validate)

    rp = sub.add_parser(
        "raw-read",
        help="🚪 逃生舱：读全 state.json 或指定 dotted path（仅 debug/migration）",
    )
    _add_feature_arg(rp)
    rp.add_argument("--field", help="可选 · dotted path · 缺省返回全 JSON")
    rp.set_defaults(func=cmd_raw_read)

    rw = sub.add_parser(
        "raw-write",
        help="🚪 逃生舱：跳过 schema/状态机校验直写 · 自动追加 concerns WARN（必带 --reason）",
    )
    _add_feature_arg(rw)
    rw.add_argument("--set", action="append", required=True,
                    help="key=val · val 优先按 JSON 解析 · 可多次")
    rw.add_argument("--reason", required=True, help="必填 · 写入 concerns WARN")
    rw.set_defaults(func=cmd_raw_write)

    # v8.0:enter-stage / satisfy-gate / complete-stage / ship-* / pm-decision /
    # bug-frontmatter / micro-validate 全部已物理删除(v8 用各 stage -start/-complete +
    # ship-phase --action 替代)。🔴 add-concern v8.172 **重新实现**(文档多处引用 ·
    # 治 doc/impl 漂移 · 见 cmd_add_concern)。
    # 上述 cmd_* 函数中 bug_frontmatter / micro_validate 保留为内部 utility · cmd_pm_decision
    # **已物理删除** —— v7 fossil 写 contract.decision(v8 用 evidence.decision)· 留着是 landmine。

    # P5 (v7.3.10+P0-148): init-feature + recover
    ifp = sub.add_parser(
        "init-feature",
        help="创建 Feature state.json · 替代手工 Write（v7.3.10+P0-148）",
    )
    ifp.add_argument("--feature", required=True,
                     help="🔴 目标 feature 目录的**完整路径**（绝对或相对 CWD）· "
                          "如 apps/admin/docs/features/ADMIN-F013-x · "
                          "**不是仅 feature 名**（v7.3.10+P0-149 修复 PTR-F032 实战 bug）· "
                          "state.json 落此处 · 同时作为 state.artifact_root 字段值")
    ifp.add_argument("--clarity", default="normal",
                     choices=["explicit", "normal", "ambiguous"],
                     help="[v8.216] 需求明确度(prepare 侦察后判 · 仅记录:台账/年检校准)· 评审配置不由它硬编码 · 由 AI 按 role_value_criteria 配 stage_review_roles")
    ifp.add_argument("--bl", default=None,
                     help="[v8.196] 本 F 承接的 BL 编号(如 BL-003)· 写入 state.json.bl · "
                          "ship 翻牌/ws-progress 解析所属 WS 优先读它(不再单靠 ROADMAP 手填「对应F编号」)")
    ifp.add_argument("--feature-id", required=True,
                     help="如 ADMIN-F013-tax-billing · 应是 --feature basename")
    ifp.add_argument("--flow-type", required=True,
                     choices=["Feature", "Bug", "Micro",
                              "Feature Planning", "问题排查"],
                     help="[v8.220] 对外收缩为 Feature/Bug · Micro 为 legacy 别名(自动映射 Feature+preset)· Planning/排查照旧 reject")
    ifp.add_argument("--preset", default=None,
                     choices=["full", "medium", "lite", "tiny", "floor", "micro"],
                     help="[v8.343] 起手**档名**(= 命名的默认维度元组)· 默认 full。"
                          "档只是起手点,权威是维度 —— 要拧用 --dims。入场问句(判风险的**种类**,"
                          "不判改动大小):micro=无行为面(测试无从写起)· floor=有行为面但测试能完全证明"
                          "(dev→ship · 验收在 MR diff)· tiny=值得一双眼看 diff · lite=有规格风险要 PRD、"
                          "但方案空间小不写 TECH · medium=值得写 TECH、但没到要两路并行冷审"
                          "(goal/blueprint 各单路)· full=两路并行冷审的边际收益压得过开销。")
    ifp.add_argument("--dims", default=None,
                     help="[v8.343] 🎛️ **custom 装配**(JSON · 只传要拧的维度 · 其余沿用档默认)。"
                          "四维:spec_depth(none|prd|prd_tech)· evidence_gate(bool)· "
                          "verify_depth(self|test|test_e2e)· review({评审点: [角色…]})· 另有开关 ui(bool)。"
                          "例:--preset medium --dims '{\"review\":{\"blueprint\":[\"architect\",\"dba\"]}}'。"
                          "🔴 组合连贯性机器校验(不连贯直接拒)· 模型错开与 PRD/TECH 高档是硬不变式、不进矩阵。")
    ifp.add_argument("--sub-project", help="如 admin / api-server")
    # v7.3.10+P0-149: 删 --artifact-root 冗余参数 · --feature 单源（既是落盘目录又是 artifact_root 字段值）
    ifp.add_argument("--initial-stage",
                     help="缺省按 (flow_type, preset) 决定（Feature→goal / Bug→diagnose / "
                          "micro→execute / tiny→dev）")
    ifp.add_argument("--merge-target", required=False,
                     help="如 staging / dev · yolo 可改用 --yolo <branch> 指定(二选一)")
    ifp.add_argument("--branch", required=True, help="如 feat/admin-f013-x")
    ifp.add_argument("--worktree-mode", choices=["auto", "manual", "off"],
                     default="off")
    ifp.add_argument("--worktree-path",
                     help="worktree 绝对路径 · worktree-mode != off 时建议提供")
    ifp.add_argument("--auto-mode", action="store_true", help="启用 AUTO_MODE")
    ifp.add_argument("--yolo", nargs="?", const=True, default=None, metavar="BRANCH",
                     help="[v8.63/65] 完全自动(YOLO)· implies --auto-mode + 自动 approve "
                          "pm_acceptance + 自动 merge MR(gh/glab)+ 自动 ship-finalize · 零 stop · "
                          "可选 <BRANCH> = 本需求专属 merge_target(指定则覆盖 --merge-target / "
                          "localconfig 默认 · 不指定则用 --merge-target)· 🔴 该分支必须非 "
                          "main/master/默认(防无人 review 直接进 main)")
    ifp.add_argument("--force", action="store_true",
                     help="覆盖现有 state.json（自动 backup .bak.<ts>）")
    # host 是 per-feature 属性 · 单源 state.json.host(全局 host_audit.json 已退役)
    ifp.add_argument("--host",
                     choices=["claude-code", "codex-cli", "gemini-cli"],
                     help="主对话宿主 · 写到 state.json.host(per-feature 单源 · external-review "
                          "等下游读它定异质模型)· 可选 · 不传则后续 <stage>-start --host 补写 · "
                          "都没有时 external-review 会 FAIL 要求显式传")
    ifp.set_defaults(func=cmd_init_feature)

    rcv = sub.add_parser(
        "recover",
        help="重新认证 checksum（state.json 被外部修改后）· 追加 concerns WARN（v7.3.10+P0-148）",
    )
    _add_feature_arg(rcv)
    rcv.add_argument("--reason", required=True,
                     help="必填 · 解释为什么手动改了 state.json · 入 audit")
    rcv.set_defaults(func=cmd_recover)

    acp = sub.add_parser("add-concern",
                         help="[v8] append 一条 concern 到 state.concerns(审计锚 · auto/skip+WARN 留痕)")
    acp.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    acp.add_argument("--severity", required=True, choices=["WARN", "ERROR", "INFO"],
                     help="concern 级别(文档惯例 WARN)")
    acp.add_argument("--message", required=True,
                     help="concern 内容(如 'auto skip: DB schema change tables/fields: ...')")
    acp.set_defaults(func=cmd_add_concern)

    # v8.174:ws-progress WS 进度 rollup(派生 · 自各 ROADMAP「状态」列 · 职责单一禁手抄)
    wpp = sub.add_parser(
        "ws-progress",
        help="[v8.174/177] 名册驱动汇总某 WS 的 feature 执行态(含跨子项目/legacy)→ 进度块 + 依赖 DAG(--write 写回 WS-PROGRESS/WS-DAG 标记区)")
    wpp.add_argument("--ws", help="WS 编号(WS-01 / 01 / WS-1 均可)· 与 --feature 二选一")
    wpp.add_argument("--feature", help="[v8.180] feature 路径 · 自其 F-id 在 ROADMAP「对应F编号」解析所属 WS(ship 自刷用 · 不必报 WS 编号)")
    wpp.add_argument("--write", action="store_true",
                     help="写回 WS 文档的 <!-- WS-PROGRESS:START/END --> 标记区(缺标记则仅输出)")
    wpp.set_defaults(func=cmd_ws_progress)

    # v8.192:pause-mark 计时排毒(stage 内 R5 暂停等待与工作分离)
    pmk = sub.add_parser("pause-mark",
                         help="[v8.192] 标记 stage 内暂停开始(emit R5 暂停点时跑)· 下一流程命令自动闭合 · 等待计入 await_minutes")
    pmk.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    pmk.add_argument("--label", help="暂停点标签(如 'PRD 确认')")
    pmk.set_defaults(func=cmd_pause_mark)

    # v8.281:评审后记录「起草可预防性」(非门禁 · ship 聚合进台账 · 年检分析起草考虑点缺不缺)
    rpv = sub.add_parser(
        "review-preventability",
        help="[v8.281] 评审收敛后记录起草可预防性(findings 里多少起草时本可预防 + 缺哪条考虑点)· 非门禁 · ship 聚合进台账「🛡️ 起草可预防性」列")
    rpv.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    rpv.add_argument("--stage", required=True, choices=["goal", "blueprint", "review"],
                     help="哪次评审(goal PRD 冷审 / blueprint TECH 评审 / review 代码评审)")
    rpv.add_argument("--preventable", type=int, default=0, help="findings 里起草时本可预防的条数(本应被 PL六问/TECH自查/复发清单覆盖)")
    rpv.add_argument("--total", type=int, default=0, help="本次确认 findings 总数")
    rpv.add_argument("--missing", default="",
                     help="缺的起草考虑点(分号分隔 · 如 '并发时序;迁移前历史数据预检')· 全 emergent 留空")
    rpv.add_argument("--note", default="", help="一句话补充(可选)")
    rpv.set_defaults(func=cmd_review_preventability)

    # v8.295:stage-cost 耗时归因(stage 收敛后记 · 非门禁 · ship 聚合进台账「⏱️ 耗时归因」)
    scp = sub.add_parser(
        "stage-cost",
        help="[v8.295] 记录本 stage 耗时归因(总轮次 / 其中协调开销轮次 / 最大的一笔是什么)· 非门禁")
    scp.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    scp.add_argument("--stage", required=True,
                     choices=["goal", "ui_design", "blueprint", "dev", "review", "test", "browser_e2e"],
                     help="哪个 stage(只在有多轮往返成本的 stage 记)")
    scp.add_argument("--rounds", type=int, default=0,
                     help="本 stage 的 agent/评审往返总轮次")
    scp.add_argument("--overhead-rounds", type=int, default=0,
                     help="其中**纯协调开销**的轮次(无设计/实现价值:文档对齐 / 跨档同步 / 格式修 / 门禁重试 / 返工重写)")
    scp.add_argument("--kinds", default="",
                     help="开销类型(分号分隔 · 如 '双档同步;门禁重试')· 无开销留空")
    scp.add_argument("--note", default="", help="一句话:最大的一笔开销是什么(可选但强烈建议)")
    scp.set_defaults(func=cmd_stage_cost)

    # v8.186:ws-lint WS 文档最新模板符合性校验(治 AI 抄项目旧 WS · 无检查)
    wlp = sub.add_parser(
        "ws-lint",
        help="[v8.186] 校验 WS 文档符合最新 templates/workstream.md 形态(TEAMWORK-MACHINE 块 + WS-PROGRESS/WS-DAG 标记 + 必备 frontmatter)")
    wlp.add_argument("--ws", help="WS 编号(WS-01 / 01 均可)· 与 --feature 二选一")
    wlp.add_argument("--feature", help="feature 路径 · 自 F-id 解析所属 WS")
    wlp.set_defaults(func=cmd_ws_lint)

    # v8.210:ledger-migrate PROCESS-LEDGER 旧 schema 升级表头(幂等 · 只换表头 · 只在末尾加列纪律)
    lmp = sub.add_parser(
        "ledger-migrate",
        help="[v8.210] PROCESS-LEDGER 旧 schema → 升级表头(幂等 · 旧数据行是有效前缀不动)· §16 append 前跑")
    lmp.add_argument("--feature", help="feature 路径(自其向上找 project-specs/PROCESS-LEDGER.md)· 省略则用 git 根")
    lmp.set_defaults(func=cmd_ledger_migrate)

    # v8.226:external-ingest 外部评审摄入(ultra review 等 · 转录归一层 · 裁决归 PMO)
    eip = sub.add_parser("external-ingest",
        help="[v8.226] 摄入外部评审(如 /code-review ultra)为 external-cross-review 产物 · --from session(主)/paste(兜底)/pr-comments(MR 窗口)")
    eip.add_argument("--feature", required=True)
    eip.add_argument("--from", dest="source", required=True, choices=["session", "paste", "pr-comments"])
    eip.add_argument("--input-file", help="session/paste:AI 已转录的 findings 文件路径")
    eip.add_argument("--mr-url", help="pr-comments:MR/PR URL")
    eip.add_argument("--label", default="ultra", help="来源标记(产物名 review-<label>.md)")
    eip.set_defaults(func=cmd_external_ingest)

    # v8.178:test-baseline 预存在失败注册表 + 差分(红 base 0 新增放行 · 治反复 stash-baseline)
    tbp = sub.add_parser(
        "test-baseline",
        help="[v8.178] 维护/查询预存在失败注册表(project-specs/test-baseline.md)+ 差分 · 红 base 0 新增可放行")
    tbp.add_argument("--feature", default=None,
                     help="feature 路径(定位 project-specs/ · 缺则用 cwd 的 git 根)")
    grp = tbp.add_mutually_exclusive_group(required=True)
    grp.add_argument("--add", dest="action", action="store_const", const="add",
                     help="登记一个预存在失败(需 --test-id + --reason)")
    grp.add_argument("--list", dest="action", action="store_const", const="list",
                     help="列出已登记的预存在失败")
    grp.add_argument("--diff", dest="action", action="store_const", const="diff",
                     help="当前失败集对照基线算新增(需 --current)")
    tbp.add_argument("--test-id", help="--add:失败用例 id(与 --current-failures 同格式)")
    tbp.add_argument("--suite", help="--add:套件/命令(如 'cargo test --lib')")
    tbp.add_argument("--reason", help="--add:为何红 · 谁的债 · 何时清(必填)")
    tbp.add_argument("--base-commit", help="--add:基线 commit(可选)")
    tbp.add_argument("--current", help="--diff:逗号/换行分隔的当前失败用例 id")
    tbp.set_defaults(func=cmd_test_baseline)

    # v8.0+P0-6:reset-prev 状态机回退一步(替代 raw-write 滥用)
    rp = sub.add_parser(
        "reset-prev",
        help="[v8] 状态机回退一步 · 治本 raw-write 滥用(Ship 后不可回 · 自动 concerns WARN)",
    )
    _add_feature_arg(rp)
    rp.add_argument("--reason", required=True,
                    help="必填 · 回退原因 · 自动追 concerns WARN")
    rp.set_defaults(func=cmd_reset_prev)

    # v8.11:jump-to-stage 跳任意合法 stage(替代 raw-write current_stage)
    jp = sub.add_parser(
        "jump-to-stage",
        help="[v8] 跳到任意合法 stage · 治本 raw-write 滥用 · 自动 audit(典型 case:pm_acceptance rejected 跳 goal/ui_design)",
    )
    _add_feature_arg(jp)
    jp.add_argument("--to", required=True,
                    help="目标 stage(必须在 LEGAL_STAGES + 当前 flow_type FLOW 表)")
    jp.add_argument("--reason", required=True,
                    help="必填 · 跳转原因 · 自动追 concerns WARN")
    jp.set_defaults(func=cmd_jump_to_stage)

    # v8.12:audit-raw-writes 跨 Feature 汇总 raw-write 历史(治本 raw-write 缺口识别)
    arw = sub.add_parser(
        "audit-raw-writes",
        help="[v8] 跨 Feature 汇总 raw-write 历史 · 识别状态机缺口(频次 ≥2 = 应有专用命令)",
    )
    arw.add_argument("--features-root", default=None,
                     help="features 根目录 · 默认 docs/features(从 cwd 算)")
    arw.set_defaults(func=cmd_audit_raw_writes)

    # v8.13:prepare-check ID 冲突预检(prepare 子流程 §1.5.4 调)
    # v8.15:加 --user-intent + --admission-judgment(物化 AI 必读 §2.1/§2.2 · 治本 F001 GCP gateway case)
    pc = sub.add_parser(
        "prepare-check",
        help="[v8] prepare 子流程 ID 冲突预检 + admission 校验 · 输出 next_available_id + consistency",
    )
    pc.add_argument("--features-root", default=None,
                    help="features 根目录 · 默认 docs/features(从 cwd 算)")
    pc.add_argument("--feature-id-prefix", required=True,
                    help="项目缩写(如 PTR / INFRA / SVC-PLATFORM)· 详 docs/conventions.md § 7")
    pc.add_argument("--flow-type", default=None,
                    choices=["Feature", "Bug", "Micro"],
                    help=("决定 artifact ID 字母(F/B/M · 详 conventions.md §1)+ "
                          "返回 stage_chain_preview · Bug/Micro 必传(漏传退回 F)"))
    pc.add_argument("--preset", default=None, choices=["full", "tiny", "micro"],
                    help=("[v8.342] Feature 重量档 · 决定 stage_chain_preview 预览哪条链 · "
                          "默认 full。定了 tiny 就传 tiny —— 否则暂停点会把 11-stage 全链"
                          "摆给用户看,已经减掉的流程税又长回去了。"
                          "🔴 lite 不在此列(它是 goal 调研后的装配形态 · prepare 预览按 full 出)"))
    # v8.15:admission(AI judgment 模式 · 不用 regex 关键词)
    pc.add_argument("--user-intent", default=None,
                    help=("[v8.15] 用户原话(原文 · 不要 paraphrase)· "
                          "工具不解析 · 仅留痕到 audit jsonl · 供 retro 复盘"))
    pc.add_argument("--admission-judgment", default=None,
                    help=("[v8.15] AI 读 prepare.md §2.1/§2.2 后的判断(JSON · 必含 "
                          "sections_reviewed[] · matched_signals[] · recommended_flow_type · "
                          "ai_rationale 4 字段)· 强制 AI 真读 §2.1/§2.2 而非凭概览 · "
                          "工具校验 recommended_flow_type vs --flow-type · MISMATCH → WARN(不 BLOCK)"))
    pc.set_defaults(func=cmd_prepare_check)

    # v8.46 C:planning-check · Feature Planning 物化入口(治本规划路径未物化漏洞)
    plc = sub.add_parser(
        "planning-check",
        help=("[v8.46] Feature Planning 物化入口 · emit 规划 checklist + 必读规范 + "
              "(若有 product-overview)规划状态机 · 不进状态机 · 治本规划路径靠 AI 自觉读 spec"),
    )
    plc.add_argument("--project-root", default=None,
                     help="项目根(检测 product-overview/)· 默认从 cwd 找 git 根")
    plc.set_defaults(func=cmd_planning_check)

    # v8.x:change-review-roles · 治本 raw-write 滥用(可枚举进脚本 · R0 哲学)
    crr = sub.add_parser(
        "change-review-roles",
        help="[v8] 调整某 stage 的 review_roles · 自动写 audit · 替代 raw-write",
    )
    crr.add_argument("--feature", required=True,
                     help="Feature/Bug 目录(含 state.json)")
    crr.add_argument("--stage", required=True,
                     help="目标 stage(必在 state.stage_review_roles 已配置之列)")
    crr.add_argument("--roles", required=True,
                     help="逗号分隔的角色列表(如 'qa,architect,external') · 必属 REVIEW_ROLE_ENUM")
    crr.add_argument("--reason", required=True,
                     help="调整理由(必填 · 写 stage_review_roles_adjustments audit)")
    crr.add_argument("--accept-external-removal", action="store_true",
                     help="[v8.66] yolo 模式去 external 评审的显式逃生口 · 仅限 external CLI "
                          "客观不可用(未装/网络死·已重试失败)· 不得为效率/集中到 review stage 用 · "
                          "用了写 concern WARN 留痕")
    crr.set_defaults(func=cmd_change_review_roles)

    # v8.343:revise-plan · 显式修订点(计划 + 修订留痕 · 用户拍板「至少可以修改」)
    rvp = sub.add_parser(
        "revise-plan",
        help="[v8.343] 按新证据改装配计划(维度)· 加减同价各记一行证据 · 回显不停等",
    )
    rvp.add_argument("--feature", required=True, help="Feature 目录(含 state.json)")
    rvp.add_argument("--dim", required=True,
                     help="要拧的维度:spec_depth / evidence_gate / verify_depth / ui / "
                          "review.<goal|blueprint|review|pm_acceptance>")
    rvp.add_argument("--to", required=True,
                     help="新值(标量裸传或 JSON)· 评审点可传逗号分隔角色('architect,external' · "
                          "空串 = 减到 0 路)")
    rvp.add_argument("--evidence", required=True,
                     help="🔴 **装配时不知道的那个事实**(不是「我觉得该加/该减」)· "
                          "加与减同价 —— 两个方向都要这一行,轻的偏置留在档默认里、不留在举证难度里")
    rvp.set_defaults(func=cmd_revise_plan)

    # v8.348:CI 门禁对照(test stage 用 · 治本地测试与 MR CI 不同构)
    cic = sub.add_parser("ci-commands",
                         help="[v8.348] 扫本仓 CI 真正会跑的门禁命令 · 供 test 逐条对照(不要求本地跑全集)")
    cic.add_argument("--root", default=".", help="仓库根(默认当前目录 · worktree 内传 worktree 根)")
    cic.set_defaults(func=cmd_ci_commands)

    # v8.69:set-mode · 语义化设 auto_mode / yolo(替代 raw-write · 物化 + audit)
    sm = sub.add_parser(
        "set-mode",
        help="[v8.69] 设 auto_mode / yolo · 写 mode_changes audit · 替代 raw-write",
    )
    sm.add_argument("--feature", required=True, help="Feature 目录(含 state.json)")
    sm.add_argument("--reason", required=True, help="变更理由(必填 · 写 mode_changes audit)")
    sm.add_argument("--auto-mode", action="store_true", help="开启 auto_mode")
    sm.add_argument("--no-auto-mode", action="store_true", help="关闭 auto_mode")
    sm.add_argument("--yolo", nargs="?", const=True, default=None, metavar="BRANCH",
                    help="开启 yolo(implies auto_mode)· 可选 <BRANCH> = 专属 merge_target"
                         "(覆盖 · 必非 main/master/默认)")
    sm.add_argument("--no-yolo", action="store_true", help="关闭 yolo")
    sm.set_defaults(func=cmd_set_mode)

    # v8.20:external-review · 异质模型评审一条命令调起(治本 SVC-CORE-F034 case)
    er = sub.add_parser(
        "external-review",
        help="[v8.291] 第三视角冷审配方(错开模型 subagent · 不 exec 子进程 · 跨厂商 CLI 异质已退役)")
    er.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    er.add_argument("--stage", required=True, choices=sorted(EXTERNAL_REVIEW_STAGES),
                    help="评审 stage(决定 prompt profile 与待评审文件集)")
    er.add_argument("--commit", default=None, help="被评审 commit(缺省取 stage auto_commit → HEAD)")
    er.add_argument("--base", default=None, help="diff 基线(缺省取 state.review_base_commit)")
    er.add_argument("--verify-fixes", action="store_true",
                    help="增量重验(仅 review):只验上一轮 findings 的修复 diff · 不全量重扫")
    er.set_defaults(func=cmd_external_review)

    # v8.24-v8.41:update-skill · 自更新 → v8.42 抽到独立 tools/update.py
    # 用法:python3 SKILL_ROOT/tools/update.py [--channel <branch>] [--accept-overwrite]
    # 不再在 state.py 注册 subparser(治本"元工具混运行时"+ chicken-and-egg)

    # ─── v8.0 stage 命令注册(Code-driven Orchestration) ─────────────
    # 设计文档:v8.0 设计稿已清理(git 历史可溯)
    # 命令 schema 现行权威:state.py --help + _v8_stage_specs.py
    #   (v8.0 命令 schema 快照已清理 · git 历史可溯)
    # 引擎模块:
    # - _v8_engine.py   通用 stage start/complete + bypass 协议
    # - _v8_stage_specs.py  12 stage 完整契约
    # - _v8_ship.py     ship-phase 子动作(替代 v7 ship-*)
    #
    # 注:v8.0+P0-12 删除 _v8_init.py(triage + prepare 命令)·
    #     入口分诊是 PMO 行为(按 SKILL.md § Triage 入口规范 规范做)· 不在 state.py 范围。
    try:
        from _v8_engine import register_v8_subparsers
        from _v8_stage_specs import STAGE_SPECS as V8_STAGE_SPECS
        from _v8_ship import register_v8_ship_subparser

        register_v8_subparsers(sub, V8_STAGE_SPECS, FLOW_BY_TYPE)
        register_v8_ship_subparser(sub)
    except ImportError as _e:
        # v8 模块不可用 · 不影响 v7 命令 · 不打印警告(silent execution)
        pass

    # v8.0+P0-13:session-bootstrap 是独立脚本 tools/bootstrap.py · 不在 state.py 域

    return p


def _maybe_heal_version_drift() -> None:
    """v8.322:版本漂移入口自愈(best-effort · 绝不拦正事)· 详 _v8_engine.heal_version_drift。

    输出走 stderr(stdout 是命令 JSON 契约 · 不许混入)。
    """
    try:
        from _v8_engine import heal_version_drift
        res = heal_version_drift(Path.cwd(), Path(__file__).resolve().parent.parent)
        if res:
            a = res.get("actions", {})
            led = a.get("ledger") if isinstance(a.get("ledger"), dict) else {}
            pad = led.get("padded_rows")
            print(
                f"⚠️ version-drift-healed {res['from']} → {res['to']}"
                f"(root={res['root']} · ledger={led.get('status', a.get('ledger'))}"
                + (f" padded_rows={pad}" if pad else "")
                + f" · gitignore={a.get('gitignore')})"
                " —— 幂等轻迁移已就地完成 · chmod/hooks/升级检测仍归 session bootstrap",
                file=sys.stderr,
            )
    except Exception:  # noqa: BLE001 — 自愈绝不拦正事
        pass


def main() -> None:
    args = build_parser().parse_args()
    _maybe_heal_version_drift()
    args.func(args)


if __name__ == "__main__":
    main()
