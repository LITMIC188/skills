# 固定注册字段

以下按固定顺序逐项给出字段名、字段类型和示例值。示例值就是本技能的实际配置，不是待填写占位符。[registration.json](registration.json) 仅含四个键。Codex 技术标识为 web-design，外部 name 和 UI 名称保持 Web-Design。

## 字段一：name

- 字段名：name
- 字段类型：string
- 示例值：`Web-Design`

## 字段二：description

- 字段名：description
- 字段类型：string
- 示例值：

当且仅当用户本条输入经 Unicode NFKC、去除首尾空白、连续空白压缩及英文忽略大小写后，字面包含“设计网页”“设计网站”“设计工作台布局”“skills<Web-Design>”任一核心触发词，或字面包含“优化 React 页面性能”“优化 Next.js 页面性能”“测试 webapp”任一扩展触发词且所有扩展触发短语之外另有“网页”“网站”“工作台布局”“React”“Next.js”“webapp”任一领域词时使用；显式调用 skills<Web-Design> 直接触发，单独扩展短语不触发；用于网页/网站/工作台布局设计、React/Next.js 页面性能优化与 webapp 测试。

## 字段三：triggers

- 字段名：triggers
- 字段类型：string[]
- 示例值（JSON 数组）：

```json
["设计网页","设计网站","设计工作台布局","skills<Web-Design>","优化 React 页面性能","优化 Next.js 页面性能","测试 webapp"]
```

- 核心触发词：前 4 项，命中任一即直接触发。
- 扩展触发词：后 3 项，须在遮蔽所有扩展触发短语后，与剩余上下文中的网页/网站/工作台布局/React/Next.js/webapp 任一领域词共现。
- 显式调用：skills<Web-Design> 优先触发，不校验扩展共现。
- 核心/扩展的数组位置与词序不可更改；不得增加未定义的同义词触发。

## 字段四：match_description

- 字段名：match_description
- 字段类型：string
- 示例值：

匹配必须先对输入和词表执行 Unicode NFKC、首尾去空白、连续空白压缩为单个空格；英文忽略大小写，中文按完全一致的连续字面匹配。包含 skills<Web-Design> 时优先直接匹配；否则包含设计网页、设计网站、设计工作台布局任一核心短语时直接匹配；否则须包含优化 React 页面性能、优化 Next.js 页面性能、测试 webapp 任一扩展短语，且遮蔽输入中所有扩展短语后的上下文另有网页、网站、工作台布局、React、Next.js、webapp 任一领域词才匹配。英文领域词须有非 ASCII 字母数字下划线边界。其余输入不匹配，不作近义词或语义推断；空白压缩不删除内部空格。

## 注册器接入契约

1. 将四字段存储为注册资料，不把自定义 triggers、match_description 填入 Codex 不支持的 frontmatter 顶层字段。
2. 对候选请求调用 ../scripts/match_trigger.py；仅 matched=true 才执行 Web-Design 的流程。
3. 未匹配、执行错误、依赖缺失是不同状态；无匹配正常退出，执行错误不得当作已匹配。
4. 仅按 NFKC、去首尾空白、连续空白压缩判断等价；`Skills<Web-Design>` 和全角调用标记命中，`skills <Web-Design>` 不命中。
5. 独立 `优化 React 页面性能` 不命中；`React 项目：优化 React 页面性能` 命中。不将触发短语自身的领域词或另一个扩展短语自身的领域词计为额外证据。
6. 完整规则和失败回退标准以 ../SKILL.md 的第 2–4 节为准，注册描述与脚本须同步维护。
7. `--stdin` 接口的输入和 JSON 输出都使用 UTF-8；非法输入或损坏的注册文件返回非零退出码，注册器不得据此继续调用技能。

