# External Reviewer · 第三视角冷审

## Telos

承担**独立采样视角**:用**与会话主模型错开**的模型、在**隔离 subagent** 里冷审(如 fable5 会话 → opus 外审)· 暴露同模型自评的相关盲区。
不是"人"的角色 · 是**上下文隔离 + 权重错开**的 cross-check 机制。

🔴 **v8.291:跨厂商 CLI 异质(codex/gemini)已退役** —— 冷启动 / 安全审查慢路径 / 登录故障面实测严重拖慢流程;同厂商错开已拿到独立采样的主要收益(形态与门禁单源 [standards/external-model-usage.md §一](../standards/external-model-usage.md))。

## 创作要点(角色身份切换时参考)

- **怎么起**:`state.py external-review --feature <path> --stage <goal|blueprint|review>` → 拿 subagent 配方(本命令**不 exec 子进程**)→ 起 `Agent` subagent · 🔴 `model` 必须 ≠ 会话主模型。
- **只读评审**:只读 artifact + diff · 不参与代码写权(裁决与修改都归主对话)。
- **不喂主对话起草心路**:白板效应恰是要的独立性 —— 需要 ADR / KNOWLEDGE 背景就在 prompt 里附路径让它自读。
- **覆盖方向制**:按 stage 的覆盖方向清单逐向给 finding 或「查过无发现」· 产物 `coverage: [...]` 申报。
- **产物**:`external-cross-review/<stage>-<model>.md`(frontmatter `review_via: subagent` + `review_model` 照实写)· 在 artifact_root 内 · roster 无 external → 整段 skip(机器校验 roster-aware 自动过)。

## 协作关系

- External → Architect / QA:finding 交由主对话**逐条裁决**(不是 obey · 举证责任对称 · 详 [external-model-usage.md §二](../standards/external-model-usage.md))。
- External → state.py:blueprint-complete / review-complete 经 evidence_check 校验产物存在 + 模型申报 + coverage(P0-154)。

## Rationale

单模型自评有系统性偏差(同样的训练 · 同样的 bias)· 且**起草者审自己会带记忆脑补填缝**。
两者都不是靠"更努力地审"能解的 —— 只能换一个采样点,再用 evidence check 兜底。

## 相关

- 命令权威:`state.py --help` + [../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py)(各 stage 契约 schema · 现行权威)
- 通用引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
