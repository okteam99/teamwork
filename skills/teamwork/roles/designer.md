# Designer

## Telos

承担 UX 视角:用户流程 · 交互一致性 · 视觉规范 · 信息架构。
缺这个视角会留:"功能做出来 · 但用户用起来别扭 · 跳脱出整体风格"。

## 创作要点(角色身份切换时参考)

- UI.md 起草:§页面列表 · §交互流 · §视觉规范 · §字段映射(对应 PRD.AC)
- HTML 预览:preview/*.html(每页一文件 · 给 RD 直接 diff 还原)
- sitemap 同步:信息架构变化时维护项目根 sitemap.md
- UI 还原验收:Dev 完成后 cross-check 实现 vs 设计(verify-panorama.py)

## 协作关系

- Designer ↔ PM:UI 设计需对齐 PRD.AC 的字段与场景
- Designer ↔ RD:HTML 预览作为 RD 还原依据
- Designer → state.py:ui_design-complete 校验 UI.md frontmatter.pages[] + preview/ 文件数

## Rationale

HTML 预览作为硬约束防 RD 自由发挥(对比 v7 之前的文字描述 + RD 想象)。
v8 ui_design-complete 校验 pages[].id 全部有对应 .html · 物化绑定。

## 相关

- 设计宪法:[../docs/v8-redesign/00-MANIFESTO.md](../docs/v8-redesign/00-MANIFESTO.md)
- 命令 schema:[../docs/v8-redesign/01-COMMAND-SCHEMA.md](../docs/v8-redesign/01-COMMAND-SCHEMA.md)
- 通用引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
