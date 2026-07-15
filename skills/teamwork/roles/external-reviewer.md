# External Reviewer · 异质模型评审

## Telos

承担跨模型视角:用**与宿主异质**的模型独立 review(宿主 Codex → 用 claude;宿主 Claude → 用 codex / gemini · 详 external-model-usage.md §11.1 host-aware)· 暴露同模型自评盲区。
不是"人"的角色 · 是异质 AI 模型的 cross-check 机制。

## 创作要点(角色身份切换时参考)

🔴 **三层现实(v8.204 · roster + localconfig 决定本角色以何种形态出场)**:
- **默认(`disable_external_review` 缺省 / `true`)** → 本角色由**同模型 subagent 隔离冷审**降级承担(产物 frontmatter `review_via: subagent`)
- **roster(`state.stage_review_roles[stage]`)无 external** → 整体 skip(机器校验自动过)
- **显式 `false`(opt-in)** → 才跑跨模型 CLI(claude 主 → codex / gemini 等 · 真异质)

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
