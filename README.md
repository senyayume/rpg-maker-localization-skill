# RPG Maker MV/MZ 简体中文汉化 Skill

面向 Codex 的 RPG Maker MV/MZ 汉化技能，用于审计、继续翻译、审查旧译文、验证并生成安全的简体中文补丁。

> A Codex skill for auditing, continuing, reviewing, validating, and delivering Simplified Chinese localization for RPG Maker MV/MZ games.

## 功能

- 审计已解包的 RPG Maker MV/MZ 游戏目录。
- 抽取数据库、系统文本、地图事件、公共事件和已确认的插件可见文本。
- 按 exact source 去重，准备带必要上下文的翻译任务。
- 接管已有汉化项目，复用项目自己的真源、mapping、staging 和门禁。
- 审查初版译文中的错译、术语、指代、人物口吻、连续剧情和中文自然度问题。
- 使用 `checkpoint` 和 `resume` 保存进度，只继续尚未完成的任务。
- 检查控制码、占位符、换行、术语、文本残留及 JSON 结构。
- 从只读原游戏重新生成独立补丁并验证输出。

## 支持范围

- RPG Maker MV、RPG Maker MZ。
- 英语、日语或英日混合原文到简体中文。
- 已解包且能够读取 `data/*.json` 的游戏。
- Codex/Agent 翻译，以及符合 mapping 合同的外部候选译文。

暂不支持自动解密、XP/VX/VX Ace、图片重绘、语音处理及其他目标语言。未知 JavaScript 字符串、资源名和 note/meta 不会被自动当作可翻译文本。

## 安装

前置要求：

- Codex（支持本地 Skills）。
- Git。
- Python 3.11 或更高版本。
- Windows 使用 PowerShell 7（`pwsh`）；macOS/Linux 使用常见 POSIX shell。

### Windows PowerShell

```powershell
git clone https://github.com/senyayume/rpg-maker-localization-skill.git `
  "$env:USERPROFILE\.codex\skills\rpg-maker-localization"

python -m pip install -r `
  "$env:USERPROFILE\.codex\skills\rpg-maker-localization\scripts\requirements.txt"
```

如果目标目录已经存在，更新现有安装，不要再次 clone：

```powershell
git -C "$env:USERPROFILE\.codex\skills\rpg-maker-localization" pull --ff-only
```

### macOS / Linux

```bash
git clone https://github.com/senyayume/rpg-maker-localization-skill.git \
  ~/.codex/skills/rpg-maker-localization

python -m pip install -r \
  ~/.codex/skills/rpg-maker-localization/scripts/requirements.txt
```

已有安装使用：

```bash
git -C ~/.codex/skills/rpg-maker-localization pull --ff-only
```

重新启动 Codex 或开启新任务后，即可通过 `$rpg-maker-localization` 使用。

安装后可以先验证 CLI：

```powershell
python "$env:USERPROFILE\.codex\skills\rpg-maker-localization\scripts\rpg_localize.py" --help
```

## 新项目快速开始

以下命令在 Skill 的 `scripts` 目录执行：

```powershell
python .\rpg_localize.py audit --game <游戏目录>
python .\rpg_localize.py init --workspace <汉化工作区> --engine rpg-maker-mz
python .\rpg_localize.py bind --workspace <汉化工作区> --game <游戏目录>
python .\rpg_localize.py extract --workspace <汉化工作区>
python .\rpg_localize.py prepare --workspace <汉化工作区>
```

翻译 Agent 根据 `translations/batches/tasks.json` 生成 mapping。候选完成后执行：

```powershell
python .\rpg_localize.py validate --workspace <汉化工作区> --mapping <候选mapping.json>
python .\rpg_localize.py accept --workspace <汉化工作区> --mapping <候选mapping.json> [--review <审查证据.json>]
python .\rpg_localize.py generate --workspace <汉化工作区>
python .\rpg_localize.py verify --workspace <汉化工作区>
```

原游戏目录始终只读；补丁生成到工作区的 `dist/`。

## 已有汉化项目

如果项目已经有真源文档、正式 mapping、翻译记忆、staging、审查队列或生成管线，不要运行 `init` 建立第二套体系。

Skill 会优先读取项目规则与当前真源，复用项目自己的 owner 和门禁。旧译文审查只报告有证据的问题；修订先进入项目现有 staging，通过项目原有验收链路后才能晋级正式译文。

在 Codex 中从项目目录启动，例如：

```text
使用 $rpg-maker-localization 接管这个已有汉化项目。先读取项目规则和当前真源，
不要新建工作区；审查当前初版译文，并把修订留在项目既有 staging。
```

至少向 Codex 指明项目根目录；如果真源文档不在常规位置，再明确给出原文目录、正式 mapping、审查队列和生成/验收入口。

技术门禁通过不等于完成全量语义或文学审查。只有明确要求全量审查时，才逐批读取全部原文与旧译文。

## 断点续译

额度、时间或故障导致任务中断时，先保存已完成的部分 mapping：

部分 mapping 是稳定任务 ID 到译文的 JSON 对象，例如：

```json
{
  "text-41e4ae984c221ad6": "药水"
}
```

```powershell
python .\rpg_localize.py checkpoint --workspace <汉化工作区> --mapping <部分mapping.json>
```

下次恢复：

```powershell
python .\rpg_localize.py resume --workspace <汉化工作区>
```

`resume` 会在本地核对源指纹、任务哈希、ID、原文和结构签名，并生成：

- `translations/batches/resume-tasks.json`：仅包含剩余任务。
- `translations/staging/resume-candidate.json`：已恢复的候选译文。
- `reports/resume.json`：完成数、剩余数、失效数和检查点数量。

同一 ID 在多个检查点中出现不同译文时会停止并报告，不会静默覆盖。已完成旧译文不会全部重新发送给翻译 Agent；只有影响指代、口吻或连续剧情时才附带少量相邻上下文。

已有项目优先使用自己的 manifest、批次 mapping、staging 和恢复合同。只有项目缺少断点能力时，才用这里的 `checkpoint`/`resume` 建立隔离适配；它不能取代项目的正式 mapping 或生成链路。

## 质量状态

- `provisional`：断点候选，只证明能够与当前任务绑定，不证明语义正确。
- `technical-pass`：通过结构、控制码、占位符、换行、术语和残留检查。
- `reviewed`：在技术门禁基础上，完成项目或任务明确要求的语义复审范围；报告必须写明已审范围、抽样规则和未审范围。

`validate` 返回非空 `review_tasks` 时，`accept` 要求 `--review`。复制验证报告的 `review_binding` 作为审查证据模板，完成列出的风险任务复审，并确保 `unresolved_ids` 为空；证据过期、覆盖不完整或仍有未解决项都会阻断正式接受。没有风险复审任务的候选仍可作为 `technical-pass` 接受。`generate` 会再次核对正式 mapping、任务集合与接受记录，禁止接受后手工改写。

未经审查的检查点不会自动成为术语、译风示例或可靠翻译记忆。发现旧译文错误时，应使相关候选和派生记忆失效；同文不同义必须记录项目级语境覆盖，不进行无证据的全局覆盖。详细合同见 [`references/workspace-contract.md`](references/workspace-contract.md) 和 [`references/quality-gates.md`](references/quality-gates.md)。

## 外部候选译文

```powershell
python .\rpg_localize.py export-external --workspace <汉化工作区> --output <交换文件.json>
python .\rpg_localize.py import-external --workspace <汉化工作区> --input <外部返回.json>
```

外部候选只能进入 staging，必须重新绑定当前原文和源指纹，并通过与 Agent 译文相同的门禁。

## 目录结构

```text
.
├── SKILL.md                 # Codex 工作流入口
├── agents/openai.yaml       # Skill UI 元数据
├── scripts/                 # CLI、确定性逻辑与测试
├── references/              # 文本面、工作区和质量合同
└── assets/                  # 工作区模板与合成 MV/MZ fixtures
```

## 测试

```powershell
python -m unittest discover -s scripts\tests -t scripts -v
```

测试只使用合成 fixtures，不包含真实游戏内容。

## 安全边界

- 不写入原游戏目录。
- 不把 Agent 会话、外部工具缓存或生成后的游戏文件当作正式译文真源。
- 不使用宽泛字符串扫描覆盖未知插件文本。
- 不自动执行解密或安装第三方工具。
- 控制码、占位符、源换行和事件结构问题未闭合时不生成正式补丁。

详细规则请查看 [SKILL.md](SKILL.md) 与 [`references/`](references/)。

## License

[MIT](LICENSE)
