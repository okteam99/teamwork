# Codex Agent 定义文件

> 本目录包含 Codex CLI 的自定义 agent 定义。
> 安装时由 `install.sh` 复制到项目的 `.codex/agents/` 目录。
> 
> 📎 这些 toml 文件定义了 Codex 版 Teamwork 的 Subagent，
>    与 Claude Code 的 Task 工具等价。PMO 在 prompt 中引用 agent name 即可 spawn。

## 文件索引

| 文件 | 对应 Stage | 说明 |
|------|-----------|------|
| rd-developer.toml | Dev Stage | RD TDD 开发 + 单元测试 |
| reviewer.toml | Review Stage | 架构师 CR ∥ QA 代码审查（并行） |
| tester.toml | Test Stage | 集成测试 ∥ API E2E |
| planner.toml | Plan Stage | PM PRD + PL-PM 讨论 + 评审 |
| designer.toml | UI Design / Panorama | Designer UI 设计 |
| e2e-runner.toml | Browser E2E Stage | 浏览器端到端测试 |
