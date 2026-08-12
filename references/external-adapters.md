# 外部工具边界

## 外部候选

外部译文只作为 staging 候选。导入时核对当前稳定 ID、exact source、源指纹和结构签名，再走与 Agent 译文相同的门禁。

## rvpacker-txt-rs

仅在用户显式要求覆盖对账时使用。检测本机命令，不自动下载或安装；复制原游戏到临时镜像，只执行 `read -i <mirror>`。结果仅用于发现 JSON extractor 可能遗漏的文本，不自动新增规则，不执行 write，不参与 accepted 或 dist。

## rpgmtranslate-qt

可作人工校对、资产查看和插件标签 lint 工具。其工程文件不是正式译文 owner。

## AiNiee 类工具

可导出任务并导入候选，不复制其源码、缓存或 API 状态。AiNiee 源码采用 AGPL-3.0；文件交换不改变本 Skill 的 owner 边界。
