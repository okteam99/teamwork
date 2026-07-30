# 前端开发规范

> 前端 RD 必须遵守。通用规范见 📎 [common.md](./common.md) · 🔴 必读白名单 📎 [HARD-RULES.md](./HARD-RULES.md)。
> Subagent 加载指引:前端子项目加载 HARD-RULES.md(必读)+ 本文件 + common.md(按需),无需加载 backend.md。
> 📎 **实施示例 / 选型教程不入库**(裁定):组件测试写法 / 状态管理选型 / 性能优化手法 / 无障碍细则 / 构建部署实践 = 模型自带知识 · AI 按需自生成(防教程腐烂反向误导);项目特异约定归各项目 `DEV-RULES.md` / `UI-RULES.md`(用户主权)。本文件只留**模型猜不到的项目缺省**(阈值与禁令)。

---

## 一、测试阈值(项目缺省 · DEV-RULES 可覆盖)

- **覆盖率 > 70%**(CI 门禁值)· P0 流程必须覆盖。
- **测试分层归属**(框架约定 · 怎么写 AI 自觉):单元(纯函数/hook)· 组件(渲染+交互+状态)· 集成(跨组件/路由/数据流)· e2e(真实浏览器 · 归 browser_e2e stage)。

## 二、样式禁令(跨 Feature 一致性 · 单人判断守不住的)

- 🔴 **项目内统一 CSS 方案 · 禁混用**(CSS Modules / Tailwind / CSS-in-JS / Sass+BEM 选其一)—— 单 Feature 各选各的 = 样式体系碎裂,没有哪个 Feature 单独负责。
- 🔴 **组件引用 design token · 禁硬编码颜色值 / 魔法数字**;暗色模式在 token 层切换(组件层不感知主题)· token 定期与设计稿对账。
- 🔴 **全局样式仅限 reset / base / typography** · 禁在全局样式中定义业务组件样式。
