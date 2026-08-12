# 工作区合同

## Owner

- 原游戏：结构与原文真源，只读。
- `localization.yaml`、`glossary.json`、`style-guide.md`、`rules/`：可迁移项目配置。
- `.local/machine.json`：本机路径与当前源指纹，不作为可迁移配置。
- `translations/staging/`：候选译文，无交付资格。
- `translations/staging/checkpoints/`：中断批次的可恢复候选，不是翻译记忆或正式译文。
- `translations/accepted/mapping.json`：通过门禁的正式译文 owner。
- `dist/`：从原游戏和 accepted 重建的补丁生成物，禁止手改。

## 路径与绑定

工作区不得位于原游戏内，也不得把 `dist` 指向原游戏。换电脑后运行 `bind`；路径变化不影响复用，内容指纹变化会阻断旧 accepted 直接生成。

## Mapping

内部 mapping 是 `{stable_text_id: translated_text}`。外部候选必须同时携带当前 ID 与原文，重新绑定成功后才能进入 staging。顺序批次 ID、旧路径或外部工具缓存不是正式身份。

## 已有项目

若当前项目已有规则、真源索引、正式 mapping、审查队列、staging 和生成合同，项目 owner 优先。Skill 不运行 `init` 建立平行体系；只复用现有数据或生成临时适配产物。修订必须经项目既有门禁晋级。

## 检查点与恢复

`checkpoint` 接受不完整 mapping，但仍检查未知 ID、空译、控制码、占位符、换行、术语和残留。输出记录 `source_fingerprint`、`task_set_hash`、稳定 ID、原文、结构签名、译文及 `quality_state=provisional`。

`resume` 在本地读取 `translations/staging/checkpoints/`：

- 只复用仍匹配当前 ID、原文和结构签名的条目。
- 同 ID 不同译文时失败关闭，不按时间覆盖。
- 输出 `resume-tasks.json` 只包含剩余任务，并输出合并后的 `resume-candidate.json`。
- 源版本变化时逐条重绑定；绝对路径变化本身不使检查点失效。
- 检查点不得自动成为 glossary、style 示例或可靠 memory。

所有条目完成后，仍需对完整候选运行 `validate -> accept -> generate -> verify`。恢复成功不等于质量验收通过。
