# 质量门禁

候选进入 accepted 前必须通过：

- 当前 manifest 的键集合、非空字符串和源指纹。
- 控制码、占位符、变量、转义和源换行签名。
- 本批命中术语、明确记录的白名单和 contextual override。
- 英日残留、原文照抄、提示词复读和明显伪翻译检查。
- 102/402 事件关系、occurrences 完整展开和路径存在性。
- 生成后的 JSON 类型、键、数组长度、事件 code 和非文本值不变。

独立审计只在有证据时触发：歧义、关键新术语、选项、复杂指代、重要连续剧情、插件文本、自动门禁问题及分层抽样。审计只报告问题 ID、证据和建议；它不代替结构门禁，也不全量复写译文。

`validate` 返回非空 `review_tasks` 时，`accept` 必须接收审查证据。以验证报告中的 `review_binding` 为模板，在完成语义复审后保持其中的 `source_fingerprint`、`task_set_hash`、`mapping_hash` 和完整 `reviewed_ids`，并确保 `unresolved_ids` 为空。任一绑定过期、风险 ID 缺失或仍有未解决项时失败关闭。没有风险复审任务的候选保持 `technical-pass`；完成当前风险复审合同的候选记为 `reviewed`。`generate` 会再次核对正式 mapping、任务集合与接受记录，禁止接受后手工改写。

无法确认的条目进入人工确认清单，不得用占位译文放行。

## 复用信任

- `provisional`：断点候选，仅完成逐条确定性检查，不证明语义质量。
- `technical-pass`：通过当前确定性门禁，但仍可能需要风险复审或显式全量审查。
- `reviewed`：在 technical-pass 基础上完成当前合同要求的语义复审。

普通续译只对全部条目运行本地确定性门禁，再把风险条目、连续剧情和规定抽样交给审查 Agent；不得因恢复检查点而重发全部旧译文。只有用户明确要求全量语义或文学审查时，才逐批读取全部原文与旧译文。

发现旧译文错误时，使受影响的候选、派生记忆和同源传播结果失效；按当前稳定 ID、exact source 和 occurrences 修订。语境需要不同译法时使用 contextual override，不静默全局覆盖。
