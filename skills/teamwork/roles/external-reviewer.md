# External Reviewer · 异质模型评审

## Telos

承担**独立采样视角**:用**与会话主模型错开**的模型、在**隔离 subagent** 里冷审(如 fable5 会话 → opus 外审)· 暴露同模型自评的相关盲区。
不是"人"的角色 · 是**上下文隔离 + 权重错开**的 cross-check 机制。
🔴 **v8.291:跨厂商 CLI 异质(codex/gemini)已退役** —— 冷启动/安全审查慢路径/登录故障面实测严重拖慢流程;同厂商错开已拿到独立采样主要收益(详 [standards/external-model-usage.md](../standards/external-model-usage.md))。

## 创作要点(角色身份切换时参考)

🔴 **唯一形态(v8.291)**:`state.py external-review` → subagent 配方 → 起**错开模型** subagent(≠会话主模型)· 产物落 `external-cross-review/*.md`。roster 无 external → 整段 skip(机器校验自动过)。


- 调用方式:由 PMO 在 blueprint / review stage 内部调度(claude 主时调 codex · 反之)
- 只读评审:外部模型只读 artifact + diff · 不参与代码写权(OpenAI ToS 合规 · v7 P0-104 强约束)
- 产物:external-cross-review/`<stage>-<model>.md`(🔴 文件名必含白名单模型字面 codex/gemini/… · 不可模糊命名 · 详 external-model-usage.md §11.2)· 在 artifact_root 内
- 至少 1 份:blueprint-complete / review-complete 物化校验该目录非空(P0-154)

## 协作关系

- External → Architect/QA:cross-review 后由架构师/QA 决定是否采纳 finding
- External → state.py:blueprint-complete / review-complete 通过 evidence_check 校验 artifact 存在

## Rationale

单模型自评有系统性偏差(同样的训练 · 同样的 bias)。
物化为 evidence check 兜底。

## 相关

- 命令权威:`state.py --help` + [../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py)(各 stage 契约 schema · 现行权威)
- 通用引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
