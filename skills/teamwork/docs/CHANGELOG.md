# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.341 · 评审力度减法侧分级 +「直接做」形态正名(用户拍板)

> case(jolichatbox 域名配置):v8.334-337 链条全部正常工作(深调研/判断卡/跳 ui·browser),但四轴全低的配置改动仍默认吃满六路评审 —— 用户当场问「这么简单的需求为什么还要那么多 review」,消费 AI 中途 re-init 切 micro 落地开 MR(自评:「按全链启动了 —— 这是错配」)。
> 用户拍板目标形态:**按理说直接开发,完成后架构师 review 一下,PM 验收盯 staging 部署就可以了。**

### 变更
- **3.7 装配判断表补减法侧(加减两侧都要判)**:**超低**(纯配置/删除/文案级 · 无契约面 · diff/断言可验)→ 建议改走 `preset=micro`(同 feature re-init 合法 · 消费实证)+ **micro 附加轻门**(execute 完成后单路 architect diff 冷审〔subagent 错开 · 只拦 BLOCKER〕· PM 验收 = MR diff + 合并后盯 staging〔await-merge 自动带 CI〕);**低**(行为性但小)→ goal `[fast]` 单路合并 · blueprint 0 路 · **review `[architect]` 单路(用户形态)**;中 = 缺省;高 = 加法触发。
- **一致性倒逼**:判断卡/装配卡评审力度行,路数与四轴对不上必须写「为什么不降」(写不出就降)。
- **prepare §2.2「坚持 micro」正名**:行为性小改动亦合法(留痕)+ 附轻门建议 —— 消费 AI 的逃生路径转正。goal brief 同步。

### 测试
`test_review_intensity_tiers_v8341.py` 9 条:超低档 = 用户拍板句 / 低档逐 stage 缺省 / 判据机械 / 一致性倒逼 / 单路仍错开 / prepare 正名 / brief。全库全绿。

## v8.340 · ship1 后 CI pipeline 自动检查(用户拍板)

> 用户:另外 ship1 之后需要自动检查 CI 的 pipeline。
> 呼应点:await-merge 的 docstring 里写着原始痛点「CI 红无人接」(实证 132h 长尾)—— 但它只轮询合并态,CI 一直没人看。本版给这句话配上机器动作,并与 v8.339 的 MR 窗口期修复口闭环。

### 变更
- **push 记录成功即自动查一次 CI**(工具内建 · `_mr_ci_status` best-effort):emit `ci_status`(passing / failing / pending / none / unknown)—— 刚 push 常为 pending = 确认 pipeline 已起;failing → emit 直接带 `ci_fix_hint`(jump 回 dev 修复口);unknown(gh/glab 缺失或未登录)不拦流程。
- **await-merge 每轮轮询带 CI**:MR 未合并且 CI 红 → **不再傻等合并**,立即以 `CI_FAILING` 退出 + 修复口指引(红灯检查置于 MERGED 判定之前 · 测试锁顺序);MERGED / WAITING emit 均回显最后一次 `ci_status`。修复循环:jump 回 dev → push 重跑 → await-merge 续走(同一 MR)。
- 解析层纯函数化:GitHub `gh pr checks`(退出码 0/8/其他 × 行状态 · `_parse_gh_checks` 单测锁五态);GitLab `glab mr view -F json` 读 pipeline 字段。ship-stage 新节「MR 窗口期 CI 自动检查」。

### 测试
`test_ci_watch_v8340.py` 9 条:解析五态 / push emit 字段 / await-merge 轮询接线 + 红灯先于 MERGED / 修复口闭环 v8.339 / spec 节。v8339 spec 锚随新节重定位。全库全绿。

## v8.339 · MR 窗口期修复:同 feature 回 dev · 不开 Bug 流(用户拍板)

> case(supersdk SCLI):ship1 已 push,PR 上 3 个已知代码 blocker —— 消费 AI 按「Ship 后不可回」判成「必须开 Bug 流再合回」。用户纠偏:直接在当前 feature 回 dev 修,不要新开 bug。
> 判断:MR 反馈循环是交付的一部分 —— 逼开 Bug 流 = 把「改 PR」变成新立项(新 worktree / 新链 / 新文档全套税)。

### 变更
- **jump-to-stage 在 pushed 态开唯一放行口**:`--to dev` + `--reason`(必填)→ 放行,`ship.reopened_fixes[]` + concerns WARN(`mr-window-reopen`)双留痕 · **ship.phase 保持 pushed**(MR 还开着 · 事实不变)· completed_stages 不动;`--to` 其他 stage 照旧拒(hint 三分:未合并修代码 → 本口;已合并 → Bug 流;放弃 → close-unmerged)。reset-prev 的 pushed hint 同步指向本口。
- **ship-stage 新节「MR 窗口期修复」**:五步(jump 回 dev → dev 证据门照跑 · review/test 按修复规模与装配 → `push` 重跑 rerecord 更新同一 MR → zip 不重开〔初版墓碑 · 修复轮文档随接力卡〕→ 边界:平台已合并才走 Bug 流);SKILL Feature 停等链 ⑥ 带指针。
- push 重跑(rerecord + WARN)与 archive 幂等重入为既有机制 —— 本版零新命令,只开一个受控口。

### 测试
`test_mr_window_reopen_v8339.py` 6 条:放行 + 双留痕 + phase/历史不变 / 其他 stage 照拒 / reset-prev hint / 非 pushed 态不记 reopened / ship-stage 五要素 / SKILL 指针。全库全绿。

## v8.338 · 方向类停等第 2 项恒为「继续讨论」(用户拍板)

> 用户:PRD 和 Feature Planning 给出 1/2/3 选项时,第 2 项永远都是继续讨论 —— 目的是方便 AI 和用户讨论清楚目标和方向。

### 变更
- **SKILL R5(b) 新增恒定规则**(⏸️ 标记 · 红密度门撞线后按判例自降红):方向类停等(PRD 终确认 + Feature Planning 全部 R5)第 2 项恒为「继续讨论」—— 修订/落地是讨论收敛后的事,不逼用户在「确认」与「给修改点」之间二选一。
- **四处载体落位**:goal 终确认(2=按反馈修订重审 → 2=继续讨论〔目标与方向 · 想法/疑虑直接说〕)· planning 全景确认(2=要改全景 → 2=继续讨论,收敛后再改再确认)· planning 拆解讨论(措辞统一「继续讨论」+ 方向疑虑入口)· planning 收尾(2=继续讨论插位 · 原选项顺延 1/3/4/5/6 ·「一步到位」与自动合并硬门同步改号 1/3)。

### 测试
`test_option2_discuss_v8338.py` 5 条:R5(b) 恒定规则 / 四载体逐处(含收尾重排与硬门改号)。全库全绿。

## v8.337 · 链装配卡固定三槽:评审力度不许再丢(用户纠偏)

> case(supersdk 实证):PRD 终确认导读的「链装配」实际输出 =「进 UI 设计、也进浏览器验收 / 不改数据库 / 动到的面…」—— 只剩环节与影响面,**评审力度整维丢失**(是否需要评审、几路、谁审、为什么,一个字没有),流程阶段也没按链展示。用户预期:根据复杂度配置**流程阶段(有哪些)+ 评审力度(是否需要 · 需要几个评审)**。
> 根因 = v8.302 老病:导读要求是形容词式(「环节取舍 + 下游评审面」)—— 形容词糊得过,槽位糊不过。
> 用户同步锚定目的:**尽量降低流程税** —— 槽位不是加税:评审减没减、减到几路,必须让用户一眼可核(减税要减在明处);整卡 ≤6 行、每槽一行、理由一句,防槽位自己变新税。

### 变更
- **goal-stage 3.7 ② 固定三槽(缺槽即漏 · 整卡 ≤6 行)**:①**流程阶段** —— 完整链逐段展示、可选段标 进/跳 + 一句理由;②**评审力度** —— 逐评审 stage 一行「**是否需要 × 几路 × 谁 × 理由**」,**收到零也显式写 `0 路 + 理由`**;③**四轴证据**各半句。默认执行/不阻塞语义不变。
- PRD 终确认导读「🔗 链装配」项与 goal brief 同步指槽位。

### 测试
`test_assembly_card_slots_v8337.py` 8 条:全链形态 / 四问逐项 / 零路显式 / 证据槽 / 减税可见 + ≤6 行防新税 / 导读指槽 / brief 载体。全库全绿。
