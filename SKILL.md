---
name: rpg-maker-localization
description: Audit, continue, review, validate, and deliver safe Simplified Chinese localization for RPG Maker MV/MZ games. Use for unpacked games, existing localization projects, interrupted translation, prior-draft review, data JSON, event dialogue, translation memory, glossaries, external mappings, localization QA, version updates, or patch delivery.
---

# RPG Maker MV/MZ 汉化

为已解包的 RPG Maker MV/MZ 游戏建立独立汉化工作区，以英语、日语或英日混合原文生成简体中文补丁。始终把译文质量、源结构安全和可验证交付作为完成条件。

## 入口分流

- 执行 `init` 前先检查当前目录的项目规则、真源索引、正式 mapping、staging、审查队列和生成合同。
- 已有项目以当前源码、测试、项目规则和真源文档为准；复用其 owner 与门禁，不另建 accepted、缓存或输出体系。审查旧译文时只报告有证据的问题，修订进入项目既有 staging。
- 没有现成汉化工作区时，按下方新项目流程执行。真源冲突、旧译文无法绑定当前原文或必须覆盖现有 owner 时停止并报告。

## 执行工作流

1. 先运行 `audit`，确认游戏目录、引擎、JSON 状态和加密资源。引擎为 unknown、数据目录冲突或 JSON 损坏时停止，不猜测。
2. 运行 `init` 创建工作区，再运行 `bind` 绑定本机游戏路径。原游戏始终只读，工作区不得放在游戏内部。
3. 阅读 [workspace-contract.md](references/workspace-contract.md)，确认原游戏、staging、accepted 和 dist 的 owner。
4. 运行 `extract`。标准字段见 [mv-mz-text-surface.md](references/mv-mz-text-surface.md)。未知插件字符串只进入发现报告；先证明用户可见性和回写路径，再新增精确规则。
5. 运行 `prepare` 应用 exact-source 去重、翻译记忆和术语子集。不要把完整项目文档、完整术语表或历史 staging 复制给翻译 Agent。
6. 让翻译 Agent 结合任务包中的必要上下文直接产出成稿级 mapping。保留控制码、占位符、变量、转义和源换行；不能确认的条目单列人工确认。
   若工作中断，运行 `checkpoint` 保存已完成的部分 mapping；下次运行 `resume`，只派发剩余任务。不要向翻译 Agent 重发全部旧译文。详细合同见 [workspace-contract.md](references/workspace-contract.md)。
7. 对候选运行 `validate`。完整门禁与独立审计触发条件见 [quality-gates.md](references/quality-gates.md)。不要用独立审计全量重复首译；只复审有风险证据的条目与必要抽样。
8. 只有当前候选通过门禁后才运行 `accept`。随后运行 `generate` 从原游戏重新生成补丁，再运行 `verify`。
9. 报告实际命令、任务数、候选数、问题数、输出路径和未闭合风险。未运行实机游戏时，明确把游戏内字体、溢出、交互和图片文字列为待实机验收。

## CLI

在 Skill 的 `scripts` 目录运行：

```powershell
python .\rpg_localize.py audit --game <游戏目录>
python .\rpg_localize.py init --workspace <工作区> --engine rpg-maker-mz
python .\rpg_localize.py bind --workspace <工作区> --game <游戏目录>
python .\rpg_localize.py extract --workspace <工作区>
python .\rpg_localize.py prepare --workspace <工作区>
python .\rpg_localize.py export-external --workspace <工作区> --output <交换文件.json>
python .\rpg_localize.py import-external --workspace <工作区> --input <外部返回.json>
python .\rpg_localize.py checkpoint --workspace <工作区> --mapping <部分mapping.json>
python .\rpg_localize.py resume --workspace <工作区>
python .\rpg_localize.py validate --workspace <工作区> --mapping <候选mapping.json>
python .\rpg_localize.py accept --workspace <工作区> --mapping <候选mapping.json>
python .\rpg_localize.py generate --workspace <工作区>
python .\rpg_localize.py verify --workspace <工作区>
```

核心依赖记录在 `scripts/requirements.txt`。缺失依赖时报告具体安装项；未经用户同意不要自动安装。

## Agent 协作

- 主 Agent 拥有审计、任务准备、门禁、accepted 和交付。
- 翻译 Agent 只处理当前任务包并输出 mapping；在相邻批次复用稳定会话。
- 审计 Agent 与首译会话分离，只处理高风险条目和抽样。
- 文件保存项目真相，Agent 会话不保存正式状态。源版本、profile 或合同重大变化时，在批次边界重新初始化角色。
- 检查点是 `provisional` 候选；机器门禁通过的 accepted 是 `technical-pass`。只有存在当前语义审查证据时才视为 `reviewed`。普通续译不触发全量旧译文复审；全量语义或文学审查必须由用户明确要求。

## 外部工具

需要导入外部候选或使用 rvpacker/rpgmtranslate 时，先读 [external-adapters.md](references/external-adapters.md)。外部工具不得写原游戏、accepted 或 dist。rvpacker 只能在临时镜像执行 read 覆盖对账；工具缺失或安全性无法确认时返回 unavailable。

## 停止条件

- 发现加密或未解包数据需要解密。
- 需要支持 XP/VX/VX Ace、图片重绘、语音或其他目标语言。
- 必须使用宽泛字符串扫描才能覆盖未知插件。
- 源指纹变化且旧 accepted 无法安全重绑定。
- 控制码、事件关系、结构或语义问题未闭合。

这些情况需要单独设计或用户确认，不能扩大本 Skill 的第一版边界。
