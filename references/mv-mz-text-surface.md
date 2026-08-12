# MV/MZ 文本面

## 默认抽取

- Actors、Classes、Skills、Items、Weapons、Armors、Enemies、States 的用户可见字段。
- System 标题、货币、属性、技能/武器/防具/装备类型和 terms。
- MapInfos 名称与 Map `displayName`。
- 事件 101 说话人、401 对话、405 滚动文字、102 选项、402 分支，以及 320/324/325 名称类变更。
- 公共事件名称、Troops 名称与战斗事件、System 变量名、SceneGlossary 说明、选择帮助注释和 122 字符串字面量。
- 由项目规则精确声明的 MZ 357 插件命令参数。

## 只发现、不自动翻译

- JavaScript 普通字符串、文件名、资源名、note/meta 和动态表达式。
- 未经确认的插件参数。
- 图片内文字；只加入资产清单。

新增规则时必须同时证明用户可见性、字段路径和回写安全。禁止使用“递归翻译所有字符串”的宽泛规则。
