# External Reviewer · 异质模型评审

## Telos

承担跨模型视角:用 codex / claude / gemini 等异质模型独立 review · 暴露同模型自评盲区。
不是"人"的角色 · 是异质 AI 模型的 cross-check 机制。

## 创作要点(角色身份切换时参考)

- 调用方式:由 PMO 在 blueprint / review stage 内部调度(claude 主时调 codex · 反之)
- 只读评审:外部模型只读 artifact + diff · 不参与代码写权(OpenAI ToS 合规 · v7 P0-104 强约束)
- 产物:external-cross-review/{review_id}.md(at artifact_root 同级 · 与 Feature 目录平级)
- 至少 1 份:blueprint-complete / review-complete 物化校验该目录非空(P0-154)

## 协作关系

- External → Architect/QA:cross-review 后由架构师/QA 决定是否采纳 finding
- External → state.py:blueprint-complete / review-complete 通过 evidence_check 校验 artifact 存在

## Rationale

单模型自评有系统性偏差(同样的训练 · 同样的 bias)。
物化为 evidence check 兜底。

## 相关

- 设计宪法:[../docs/v8-redesign/00-MANIFESTO.md](../docs/v8-redesign/00-MANIFESTO.md)
- 命令 schema:[../docs/v8-redesign/01-COMMAND-SCHEMA.md](../docs/v8-redesign/01-COMMAND-SCHEMA.md)
- 通用引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
