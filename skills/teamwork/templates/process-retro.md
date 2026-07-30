# 流程复盘模板(feature 级 · 耗时归因 + 阶段反思)

> 位置:`{子项目}/docs/retros/<feature-id>-process.md`
> **telos**:装**台账装不下的那部分** —— 逐 stage 的耗时归因与流程反思。
> 台账(`project-specs/PROCESS-LEDGER.md`)一行一 feature、单元格 ≤1 行,只放**可查表算账的字段**;
> 「这 318 分钟花在哪」「哪个环节是纯过场」这类叙述压进单元格就废了,归本文件。
>
> 🔴 **区别同目录的业务复盘** `docs/retros/<feature-id>.md`(需求怎么演进 / 技术选型踩了什么坑 · 知识层):
> **本文件只复盘 teamwork 流程本身** —— 时间花在哪、哪个环节没产生价值。别混写。
>
> **写入时机**:ship1 archive 的规划 gate(worktree 内 · 与台账行同时)· 路径加进 `--planning-artifacts`
> 随 feature MR 原子合入 git。台账「⏱️ 耗时归因」列填 `<开销轮>/<总轮> · 详 <本文件相对路径>`。
>
> **消费方**(🔴 指名 · 写而不读 = 白写):年检算**协调开销占比趋势** + 验证提效改动是否真起效;
> 「纯过场候选」跨 feature 复发 → 该环节进砍单;「流程新判例」→ 反馈框架。

---

```markdown
---
feature_id: <ID>
flow: <Feature / Feature·micro / Bug>
total_wall: <2.4h>            # 照抄 ship1 emit 的 ledger_timing.total_wall
ai_autonomous_min: <88>       # 同上(已扣跨 session 空闲)
await_user_min: <32>          # 同上
host: <claude-code>
---

# 流程复盘 · <ID>

## 一、各阶段耗时(机器数据 · 照抄 `ledger_timing.per_stage` · 不肉眼算)

| stage | 耗时 | 其中等用户 | 总轮次 | 其中协调开销 |
|---|---|---|---|---|
| goal | 95m | 20m | 4 | 0 |
| blueprint | 318m | 0 | 6 | 2 |
| dev | … | | | |

> 🔴 `总时长 − AI自主 − 待用户` = **未标记挂机空闲**(过夜/跨天 · 不冒充 AI 工作)。

## 二、耗时归因(🔴 本文件的核心 · 台账里放不下的就是这段)

逐 stage 写「这段时间花在哪」。**只有当场记得住** —— ship 时回填要靠产物 mtime 反推。

### <stage 名>

- **协调开销 <M>/<N> 轮**,类型:<双档同步 / 门禁重试 / 格式修 / 返工重写 / 无>
- **最大的一笔**:<一句话:哪几轮、在做什么、有没有产生设计或实现价值>
- **可避免吗**:<能 → 怎么避(具体到规则/顺序/工具);不能 → 为什么是必要成本>

> 判据:**「这一轮产生了新的设计判断或新的实现吗?」** 没有 = 协调开销。
> 典型开销:文档间对齐(A 改了 B 要跟着改)· 门禁不熟撞了重试 · 用户改选后的连锁重写。

## 三、流程反思(固定四问 · 空写「无」· 🔴 照实写不美化)

- **拦住真问题**:<external confirmed N 条(列举)/ test 抓回归 / diagnose 改变修复方向 | 无>
- **纯过场候选**:<零 finding + 零修订 + 全默认的环节 | 无>
- **流程新判例**:<违规/摩擦 → 建议反馈 teamwork(consuming 项目不自改 spec)| 无>
  🔴 **非「无」时**:台账「反思摘要」列必须以 `判例:` 前缀开头(年检数「连续数月无新判例」靠 grep 它 · 正文留在本节)。
- **成本异常**:<rounds 过多 / bypass(理由)/ 重试 | 无>

## 四、起草可预防性(照抄 `ledger_authoring_preventability`)

- <可预防 N / 总 M> · 缺的起草考虑点:<并发时序;迁移前历史数据预检 | 全 emergent>

## 五、给下一个 feature 的一句话

<最值得改的一件事 · 没有就写「无」>
```

---

## 起草纪律

- 🔴 **机器数据照抄不肉眼算**:§一 与 §四 全部来自 ship1 archive emit(`ledger_timing` / `ledger_authoring_preventability`)。
- 🔴 **§二 只写有开销的 stage**;零开销的 stage 在 §一 表里记 `0` 即可,不必展开成段。
- 🟢 **不追求长**:一个顺利的 feature 这份文档可能只有 §一 + 四个「无」+ 一句话,那也是有效数据
  (「这次没开销」与「没记录」是两回事,年检要分得开)。
- ❌ **不写业务内容**(需求怎么变、技术怎么选)—— 那是 `docs/retros/<feature-id>.md` 的事。
