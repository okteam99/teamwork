#!/usr/bin/env python3
"""
state-patch.py — teamwork v7.3.10+P0-52

增量更新 Feature/Bug 的 state.json，避免 Edit 全文带来的 token 成本。

为什么需要：
    Edit 工具更新 state.json 时要发送 old_string + new_string 上下文，
    一个 Feature 生命周期 PMO 更新 state.json 约 15-20 次（triage / Plan
    入口 / 各 Stage 完成 / 评审循环 / Ship 双段 / 等），累积主对话
    token 成本 ~7,500 tokens / Feature。本脚本只发送变更字段，节省 ~40%。

支持的操作：
    --set KEY=VALUE             设置 scalar 字段
    --append KEY=VALUE          list 字段追加（去重）
    --merge-object KEY=JSON     对象字段 merge
    --set-note KEY=VALUE        设置 _KEY_note 字段（自动加 _ 前缀）
    --unset KEY                 删除字段
    --validate                  写入前 schema 校验
    --dry-run                   仅显示更新后内容，不写入

类型推断（--set / --append 的 VALUE 自动识别）：
    true/false → bool
    null → None
    数字 → int 或 float
    [/{ 开头 → JSON literal（支持 array / object）
    其他 → string

典型调用示例：

    # 1. Stage 转换（Goal-Plan → Blueprint）
    python state-patch.py /path/to/state.json \\
      --set 'current_stage=blueprint' \\
      --append 'completed_stages=goal_plan'

    # 2. PRD 评审完成（写入 verdict）
    python state-patch.py state.json \\
      --merge-object 'goal_plan_substeps_config={"plan_done": true, "review_round": 2}'

    # 3. Ship 第二段 finalize
    python state-patch.py state.json \\
      --set 'current_stage=completed' \\
      --append 'completed_stages=ship_phase2_finalize' \\
      --set 'shipped=true' \\
      --set 'shipped_at=2026-04-29T19:30:00Z' \\
      --set 'merge_commit=07c93d63' \\
      --set-note 'merge_evidence=git fetch + git branch -r --contains 验证通过'

    # 4. Bug 简化流程（fix 完成）
    python state-patch.py state.json \\
      --set 'current_stage=ship_phase1_awaiting_merge' \\
      --append 'completed_stages=bug_fix_dev'

    # 5. 评审循环超 3 轮 → 用户决策升级
    python state-patch.py state.json \\
      --set 'goal_plan_substeps_config.review_round_overflow=true' \\
      --set 'goal_plan_substeps_config.review_round_overflow_decision=force-converge' \\
      --set 'goal_plan_substeps_config.review_round_overflow_decision_at=2026-04-29T15:00:00Z' \\
      --set 'goal_plan_substeps_config.review_round_overflow_decision_reason=PL 拍板继续推进'

注意：
    - --set 不支持 dotted path（嵌套字段），用 --merge-object 代替
    - --append 默认去重（已存在该值则跳过）
    - 原子写：先写临时文件 → fsync → mv，防中断损坏
    - schema 校验仅检测顶层字段名是否在 templates/feature-state.json 里，不验证类型/值

退出码：
    0  成功
    1  参数错误 / state.json 不存在 / JSON 解析失败
    2  schema 校验有 WARN（仍写入，但 stderr 给出警告）

更多：
    详见 SKILL.md / roles/pmo.md state.json 更新规范段。
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def parse_value(v):
    """智能类型推断"""
    if v == "true":
        return True
    if v == "false":
        return False
    if v == "null":
        return None
    # 整数
    try:
        if v.lstrip("-").isdigit():
            return int(v)
    except (ValueError, AttributeError):
        pass
    # 浮点
    try:
        return float(v) if any(c in v for c in ".eE") else int(v)
    except (ValueError, TypeError):
        pass
    # JSON literal（array / object / string）
    if v and v[0] in "[{\"":
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            pass
    return v


def parse_kv(arg):
    """解析 KEY=VALUE 形式"""
    if "=" not in arg:
        raise ValueError(
            f"--set/--append/etc 参数格式错误（应为 KEY=VALUE）：{arg}"
        )
    k, v = arg.split("=", 1)
    return k.strip(), parse_value(v)


def apply_set(state, key, value):
    state[key] = value


def apply_append(state, key, value):
    if key not in state:
        state[key] = []
    if not isinstance(state[key], list):
        raise TypeError(
            f"--append 字段 '{key}' 不是 list 类型（当前：{type(state[key]).__name__}）"
        )
    if value not in state[key]:
        state[key].append(value)


def apply_merge_object(state, key, value):
    if not isinstance(value, dict):
        raise TypeError(
            f"--merge-object 值必须是 JSON object（当前：{type(value).__name__}）。"
            f" 应该形如 --merge-object 'foo={{\"key\": \"value\"}}'"
        )
    if key not in state:
        state[key] = {}
    if not isinstance(state[key], dict):
        raise TypeError(
            f"--merge-object 字段 '{key}' 不是 object 类型（当前：{type(state[key]).__name__}）"
        )
    state[key].update(value)


def apply_set_note(state, key, value):
    note_key = f"_{key}_note" if not key.startswith("_") else key
    state[note_key] = value


def apply_unset(state, key):
    state.pop(key, None)


def validate_schema(state, schema_path):
    """简单 schema 校验：检查顶层字段名是否在模板里"""
    if not schema_path or not schema_path.exists():
        return True, [], "schema 文件不存在，跳过校验"
    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        return False, [], f"schema 文件 JSON 解析失败：{e}"
    schema_keys = set(schema.keys())
    state_keys = set(state.keys())
    unknown = sorted(state_keys - schema_keys)
    return len(unknown) == 0, unknown, ""


def main():
    parser = argparse.ArgumentParser(
        description="增量更新 state.json，避免 Edit 全文 token 成本（teamwork v7.3.10+P0-52）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="详见脚本顶部 docstring 调用示例 + roles/pmo.md state.json 更新规范",
    )
    parser.add_argument("state_file", help="state.json 文件路径")
    parser.add_argument(
        "--set",
        action="append",
        dest="set_ops",
        default=[],
        metavar="KEY=VALUE",
        help="设置 scalar 字段（支持 true/false/null/数字/string/JSON literal）",
    )
    parser.add_argument(
        "--append",
        action="append",
        dest="append_ops",
        default=[],
        metavar="KEY=VALUE",
        help="list 字段追加（去重）",
    )
    parser.add_argument(
        "--merge-object",
        action="append",
        dest="merge_ops",
        default=[],
        metavar="KEY=JSON",
        help="对象字段 merge（VALUE 必须是 JSON object literal）",
    )
    parser.add_argument(
        "--set-note",
        action="append",
        dest="note_ops",
        default=[],
        metavar="KEY=VALUE",
        help="设置 _KEY_note 字段（自动加 _ 前缀，已带前缀则不加）",
    )
    parser.add_argument(
        "--unset",
        action="append",
        dest="unset_ops",
        default=[],
        metavar="KEY",
        help="删除字段",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="写入前 schema 校验（基于 templates/feature-state.json 顶层字段名）",
    )
    parser.add_argument(
        "--schema",
        metavar="PATH",
        help="自定义 schema 文件路径（默认推导 templates/feature-state.json）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示更新后内容，不写入",
    )
    args = parser.parse_args()

    state_path = Path(args.state_file)
    if not state_path.exists():
        print(f"ERROR: state.json 文件不存在：{state_path}", file=sys.stderr)
        sys.exit(1)

    # 读
    try:
        with open(state_path) as f:
            state = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: state.json JSON 解析失败：{e}", file=sys.stderr)
        sys.exit(1)

    # 应用操作（按顺序：unset → set → append → merge → set-note）
    try:
        for op in args.unset_ops:
            apply_unset(state, op)
        for op in args.set_ops:
            k, v = parse_kv(op)
            apply_set(state, k, v)
        for op in args.append_ops:
            k, v = parse_kv(op)
            apply_append(state, k, v)
        for op in args.merge_ops:
            k, v = parse_kv(op)
            apply_merge_object(state, k, v)
        for op in args.note_ops:
            k, v = parse_kv(op)
            apply_set_note(state, k, v)
    except (ValueError, TypeError) as e:
        print(f"ERROR: 操作失败 → {e}", file=sys.stderr)
        sys.exit(1)

    # 校验
    warn_exit = False
    if args.validate:
        if args.schema:
            schema_path = Path(args.schema)
        else:
            # 默认推导：state.json 路径回溯到 teamwork skill 根目录
            schema_path = (
                state_path.resolve().parent.parent.parent.parent
                / "skills"
                / "teamwork"
                / "templates"
                / "feature-state.json"
            )
            # fallback：尝试相对路径
            if not schema_path.exists():
                here = Path(__file__).parent
                schema_path = here / "feature-state.json"
        ok, unknown, err = validate_schema(state, schema_path)
        if err:
            print(f"WARN: schema 校验失败 → {err}", file=sys.stderr)
            warn_exit = True
        elif not ok:
            print(
                f"WARN: 检测到 schema 之外的顶层字段：{unknown}",
                file=sys.stderr,
            )
            print(
                "（可能是 PMO 自创字段或老字段残留，检查是否合理；本次仍写入）",
                file=sys.stderr,
            )
            warn_exit = True

    # 写
    new_content = json.dumps(state, ensure_ascii=False, indent=2) + "\n"

    if args.dry_run:
        print("=== DRY RUN（未写入）===")
        print(new_content)
        return

    # 原子写
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=state_path.parent, prefix=".state-", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w") as f:
            f.write(new_content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, state_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # 简短报告
    ops_summary = []
    if args.set_ops:
        ops_summary.append(f"set:{len(args.set_ops)}")
    if args.append_ops:
        ops_summary.append(f"append:{len(args.append_ops)}")
    if args.merge_ops:
        ops_summary.append(f"merge:{len(args.merge_ops)}")
    if args.note_ops:
        ops_summary.append(f"note:{len(args.note_ops)}")
    if args.unset_ops:
        ops_summary.append(f"unset:{len(args.unset_ops)}")
    print(f"OK: {state_path} 已更新（{', '.join(ops_summary)}）")
    if warn_exit:
        sys.exit(2)


if __name__ == "__main__":
    main()
