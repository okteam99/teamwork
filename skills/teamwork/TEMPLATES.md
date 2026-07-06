# 文档模板索引

完整模板清单与按流程导航见 [templates/README.md](./templates/README.md)。本文件保留**格式权威红线**。

---

## 🔴 格式权威红线

```
├── 🔴 templates/ = 格式唯一真相源
│ 任何 teamwork 产出文档（PRD / TC / TECH / state.json / review-log 等）
│ 的格式、字段、frontmatter schema、表头结构 —— 以 templates/ 下对应模板为准。
│
├── 🔴 禁止以 peer Feature 产物为格式基准
│ 不得说"先参考一下最近一个 Feature 的 state.json / PRD 格式"。
│ peer Feature 的产物可能装的是老 schema、或被手动改过，抄过去 = 漂移放大。
│
├── 🟢 peer Feature 可作"内容参考"（允许）
│ ├── AC 怎么写得干净（内容层面）
│ ├── 类似业务的 TC 用例套路复用（业务逻辑层面）
│ ├── 架构决策的历史背景（ADR 追溯）
│ └── ⚠️ 但"怎么排字段、怎么写 frontmatter" 必须回 templates/ 对齐
│
├── 🔴 二者不一致时以 templates/ 为准
│ 发现 peer Feature 与 templates/ 格式不一致 → templates/ 优先；
│ 在 concerns 记录漂移（"F0xx 的 state.json 缺 ship 字段，建议归档时补齐"）。
│
└── 🔴 state.json 特别注意
 state.json 由 `tools/state.py` 单源维护(schema 演化由 state.py + _v8_stage_specs.py 控制)。
 peer Feature 的 state.json 可能是老 schema · 必须走 state.py validate。
```

📎 该红线由 PMO / PM / RD 共同遵守，触发流程见 roles/{pmo,pm,rd}.md 对应「格式权威」条目。
