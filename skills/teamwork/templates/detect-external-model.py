#!/usr/bin/env python3
"""
detect-external-model.py — 外部模型探测脚本（v7.3.10+P0-24）

用法：
    python3 {SKILL_ROOT}/templates/detect-external-model.py [--cwd <project_root>]

功能：
    1. 探测主对话宿主（基于 .claude/ / .codex/ / .agents/ 等目录标记）
    2. 探测候选外部 CLI 是否在 PATH（codex / claude）
    3. 应用同源约束（外部模型 ≠ 主对话同源）
    4. 输出结构化 JSON 到 stdout，PMO 解析渲染

设计原则（关键）：
    - 不查 API key env var（OAuth / config file / env var 多种存在方式，env var 探测会误报）
    - 失败检测延后到运行时：dispatch 时调用 CLI 失败 → state.concerns WARN → 降级单视角 review
    - 此脚本只回答"CLI 装了吗 + 是否同源"两个确定性问题

依赖：仅 Python 3.6+ 标准库（os / shutil / json / argparse）

退出码：
    0 - 正常输出（无论是否有候选）
    1 - 内部错误

🔴 本脚本是 Teamwork v7.3.10+P0-24 外部模型规范的探测入口。
   PMO 在 Feature 流程的初步分析阶段调用此脚本，渲染为「🌐 外部模型探测」段。
"""

import argparse
import json
import os
import shutil
import sys


# 候选外部模型清单
# 未来加 Gemini 等模型只需在这里加一行；不需要修改 PMO 逻辑
CANDIDATES = [
    {
        "id": "codex",
        "cli": "codex",
        "auth_hint": "需 codex 已 OAuth 登录（codex login）或 OPENAI_API_KEY 已设",
        "homologous_host": "codex-cli",
    },
    {
        "id": "claude",
        "cli": "claude",
        "auth_hint": "需 claude 已 OAuth 登录（claude login）或 ANTHROPIC_API_KEY 已设",
        "homologous_host": "claude-code",
    },
]


def detect_host(cwd):
    """
    探测主对话宿主。

    规则（与 stages/init-stage.md 宿主检测保持一致）：
        - 存在 .claude/ 目录 → claude-code
        - 存在 .codex/ 或 .agents/ → codex-cli
        - 其他 → unknown
    """
    if os.path.isdir(os.path.join(cwd, ".claude")):
        return "claude-code"
    if os.path.isdir(os.path.join(cwd, ".codex")):
        return "codex-cli"
    if os.path.isdir(os.path.join(cwd, ".agents")):
        return "codex-cli"
    return "unknown"


def detect_cli(cli_name):
    """检查 CLI 是否在 PATH 中。"""
    return shutil.which(cli_name) is not None


def main():
    parser = argparse.ArgumentParser(
        description="Detect external model availability for Teamwork external cross-review."
    )
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Project root for host detection (defaults to current working directory).",
    )
    args = parser.parse_args()

    cwd = os.path.abspath(args.cwd)
    host = detect_host(cwd)

    candidates_pool = []
    available_external = []

    for c in CANDIDATES:
        cli_installed = detect_cli(c["cli"])
        is_homologous = c["homologous_host"] == host

        if not cli_installed:
            usable = False
            reason = "CLI 未安装（未在 PATH 中找到）"
        elif is_homologous:
            usable = False
            reason = "与主对话同源（独立性弱，不可作外部模型）"
        else:
            usable = True
            reason = None

        entry = {
            "id": c["id"],
            "cli": c["cli"],
            "cli_installed": cli_installed,
            "is_homologous_to_host": is_homologous,
            "usable_as_external": usable,
            "reason_unavailable": reason,
            "auth_hint": c["auth_hint"] if usable else None,
        }
        candidates_pool.append(entry)
        if usable:
            available_external.append(c["id"])

    # 推荐策略：候选清单中第一个可用的（CANDIDATES 的顺序即偏好顺序）
    recommendation = available_external[0] if available_external else None

    output = {
        "host_main_model": host,
        "candidates_pool": candidates_pool,
        "available_external": available_external,
        "recommendation": recommendation,
        "schema_version": "1.0",
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"detect-external-model.py 内部错误: {e}\n")
        sys.exit(1)
