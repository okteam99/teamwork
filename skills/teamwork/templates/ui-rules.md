# UI-RULES（设计规范 · 人维护 · 装策略不装视觉值）

> 🔴 **职责单源**：本文件装**设计策略 / 约定 / 规则**（该用什么 · 为什么）· **不装视觉值**（hex / px / 组件长相 = 真相 · 归 `{子项目}/docs/design/preview-project/` 代码 · markdown 复述必 drift）。规则说「该用什么、为什么」· 代码说「长什么样」。
> 🔴 **两层**（同 DEV-RULES）：`project-specs/UI-RULES.md`（workspace · 跨子项目共享设计语言）· `{子项目}/docs/UI-RULES.md`（该子项目特有 / 对全局的偏离）。单项目仓库只用一层。
> 作者：Designer / PL（人维护）· 读者：Designer 设计前必读（ui_design substep 1）+ § 交互&视觉质量 rubric 对照「既有设计系统」。

## 组件 / 控件偏好
> 优先用什么、禁用什么（代码里看不出「优先级」· 这就是规则该在的理由）
- 组件库：{如 Ant Design / MUI / 自研 · 版本}
- 列表 → {DataTable · 不用裸 table}　弹层 → {优先 Drawer · Modal 仅用于 X}　表单 → {FormField}
- 禁用：{native dialog / 自造按钮 / ...}

## 颜色 / 主题策略
> 🔴 只写**策略**（语义角色 / 暗色策略 / 新增色门槛）· hex 值在 preview-project tokens
- 语义角色：primary={定位}　danger / success / warning={各自定位}
- 暗色：{策略 · 如 surface 走 elevation 不靠纯反色}
- 🔴 新增 accent 色 / 字体 → 需 {谁} 批准（防色板膨胀）

## 间距 / 排版策略
> 只写 scale 与 rationale · 具体值在 tokens
- 间距 scale：{4 / 8px base}　字阶：{比例 · body 最小号 · 标题级不跳}　数字列：tabular-nums

## 交互约定（本 app 的模式 · 代码里看不出的判断）
- 破坏性操作：{确认风格 · inline undo / modal confirm}
- toast / 反馈：{行为 · 自动消时长}
- loading：{骨架 / 转圈 · 何时用哪个}　empty：{模式}　error：{模式}
- 导航模型：{主操作位置 / 层级}

## 可访问性 bar
- WCAG {AA / AAA}　键盘可达 + focus-visible 必有　reduced-motion 必 respected　触控 ≥ 44px

## 品牌 / 语气 + copy 约定
> cite [ui-design-stage § 交互&视觉质量 rubric C 段](../stages/ui-design-stage.md)
- 语气：{conversational / 正式 · 受众}　命名：用户视角（非系统术语）　action：active voice + 全流程同名

## 禁用清单（本项目 anti-pattern）
- {never 用 X}　{不引入新字体}
- 🔴 **页面内容禁内嵌预览控件**（状态切换 / 场景 toggle）—— 预览工具一律走 **preview dev 悬浮工具面板（右下角 · 非顶栏）**（详 ui-design-stage § preview dev 工具面板 · 悬浮 overlay 不 shift 布局 · 保证页面=真实代码）

## 变更记录
| 日期 | 变更 | 作者 |
|------|------|------|
