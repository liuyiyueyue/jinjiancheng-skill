# 金渐成历史观点与投资思路

基于金渐成公众号历史文章的分析 skill，帮助理解他的判断依据、操作条件、失败反思与观点变化。回答可以保留直接、具体的表达方式，但会区分作者原话、内容归纳与对新问题的推演。

项目提供可在 Codex 和 Claude Code 中使用的四个 skill，以及 Anthropic API 和 AWS Bedrock 两个命令行入口。这是文章检索与提示词方案，没有训练专属模型，不代表作者本人或其当前表态。

## 内容如何组织

- **长期原则**：风险承受能力、收益来源、基本面与估值、资金和仓位安排。
- **阶段判断**：必须带日期和适用条件，不能把当时判断直接用于今天。
- **个人操作**：区分计划与成交、个人与家庭账户、持有意向与后来的退出。
- **失败与修正**：将中国平安的亏损反思与加仓方法一起讨论，保留方法的边界。

例如，早期文章中的“茅台打算长持”，需要与2024年清仓自述一起理解；“越跌越买”要结合基本面和现金条件，也要看到平安案例。固定“50%底仓+50%做T”、所有房产一律不能投等说法，不作为作者的通用规则。

维护入口：

- [共用回答原则](.claude/skills/jinjiancheng/references/answer-policy.md)
- [从文章整理的思考框架](.claude/skills/jinjiancheng/references/thinking-framework.md)
- [观点与操作时间线](.claude/skills/jinjiancheng/references/view-timeline.md)
- [18篇核心文章来源索引](.claude/skills/jinjiancheng/references/source-index.md)

## 在 Codex 中使用

将整个仓库作为 Codex 项目打开。如果使用 Codex CLI，请在仓库根目录启动：

```bash
cd /path/to/jinjiancheng-skill
codex
```

在 Codex 对话框中（不是终端里）用 `$` 调用 skill：

```text
$jinjiancheng 请按文章日期说明他对中国平安的看法如何变化。
$jinjiancheng-cn-stock 他是否始终持有茅台？请区分持有计划和后续卖出。
$jinjiancheng-us-stock 资金较少的人可以照搬他的分批加仓方法吗？
$jinjiancheng-real-estate 他是否反对在所有地区投资所有类型的房产？
```

提问时可以指定历史时点，例如：“只使用截至2023年12月31日已经发表的文章。”

Codex 通过 `.agents/skills/` 发现这四个项目 skill。每个入口都是指向对应 `.claude/skills/` 目录的相对符号链接，因此两个客户端共用同一套指令和资料。请保留完整仓库，包括知识库和参考文件；只复制单个 skill 目录并不够。检出仓库时需要保留符号链接（Windows 用户可使用 WSL 或支持符号链接的 Git 环境）。

在 Codex CLI 中输入 `/skills` 检查是否已发现这些 skill。打开项目后若未显示，请重启 Codex。详情见[官方 skill 文档](https://learn.chatgpt.com/docs/build-skills)。

回答由当前 Codex 会话生成。项目的本地原文读取工具需要 Python 3；关键词检索还需要安装 `jieba`（见下文）。此用法不需要 Anthropic 或 AWS 凭证。本地检索命令本身不会调用模型 API；Codex 会将读取到的材料作为回答上下文。

## 在 Claude Code 中使用

在此项目中打开 Claude Code，调用项目内的 skill：

```text
/jinjiancheng 他对中国平安的操作如何变化？失败后反思了什么？
/jinjiancheng-cn-stock 他是否始终持有茅台？请按文章日期说明。
/jinjiancheng-us-stock 小资金能照搬他的左侧加仓方法吗？
/jinjiancheng-real-estate 他是否反对所有地区、所有类型的房产投资？
```

四个入口位于 `.claude/skills/<名称>/SKILL.md`，专项入口引用同一份回答原则、原文索引和时间线。请保留完整项目，单独复制一个 `SKILL.md` 不会同时带上所需的资料。

问历史时点时明确“只使用截至某日已经发表的文章”；问今天的市场时，历史文章只能提供思考框架，实时价格与财务信息需要另行核实。

## 先查本地原文

检索用到 `jieba`；按编号读取精选原文只需 Python 标准库。下面的命令不调用模型 API：

```bash
python3 -m pip install jieba

python3 jinjiancheng_grounding.py "中国平安"
python3 jinjiancheng_grounding.py "茅台" --as-of 2023-12-31
python3 jinjiancheng_grounding.py --source S04 --full
```

检索输出包含全文及相关核对摘录，不再固定只取文章前1500字。核对摘录会补充观点变化和失败案例；它们不代表主题全部材料，关键词命中也不意味着能够支持任何结论。

## 命令行生成回答

两个入口共用回答原则、原文和核对摘录，支持 `--as-of YYYY-MM-DD`。实际生成会将问题与选中的文章材料发送给对应服务。

### Anthropic API

```bash
python3 -m pip install anthropic jieba
export ANTHROPIC_API_KEY='你的 API key'
export ANTHROPIC_MODEL='你账号可用的模型 ID'

python3 jinjiancheng_ai.py "龙头股是否越跌越买就行？"
python3 jinjiancheng_ai.py "茅台是否已经清仓？" --as-of 2023-12-31
```

### AWS Bedrock

```bash
python3 -m pip install boto3 jieba
# 使用已配置的 AWS profile、环境变量或运行环境的角色凭证
export AWS_REGION='us-east-1'
export BEDROCK_MODEL_ID='你账号和区域可用的模型或推理配置 ID'

python3 jinjiancheng_bedrock.py "他的固定底仓比例是多少？"
python3 jinjiancheng_bedrock.py "中国平安是什么持仓状态？" --as-of 2022-12-31
```

显式设置模型 ID；脚本保留的历史默认值不是当前可用性的保证。费用取决于所选模型与实际输入输出，本文不承诺固定单次价格。旧版 [Bedrock说明](Bedrock使用说明.md) 中的模型、定价、区域和控制台示例需要按服务方当前文档核对。

## 回答示例

以下是编辑性示范，不是金渐成原话，也不是已运行模型的实测结果。

**问：他是不是一直坚持拿着茅台？**

> 要分时间看。2022年11月的文章写的是成本低、打算长持；2024年年度回顾已经明确说全部清仓。这里体现的是持有计划后来发生变化。
>
> 据这些文章推演，长期持有也需要保留重新判断和退出的条件。若要应用到今天，还需要核实当前企业状况、估值及自己的资金约束。
>
> 依据：S01《想不出标题》（2022-11-05）、S08《我的2024年度~》（2024-12-25）。

原文、概括和推演应可区分，引用应能支持具体主张。没有找到依据时应明确说明，不编造名言、精确比例、当前持仓或成功率。

## 数据范围与限制

- 知识库：375篇，769,981个正文字符，`publish_time` 范围为 **2022-11-05—2026-04-29**。
- 离线目录：477个 `index.html`；其中并非全部都有可用正文，不把文件夹日期当作知识库覆盖范围。
- 核对材料：18篇核心文章、43段连续原文摘录，保存在 [sources.json](.claude/skills/jinjiancheng/references/sources.json)。
- 来源编号、标题、日期和路径对应知识库记录。文章发布时间与文中回顾的交易时间需要分别理解。
- 交易、收益、行情和预测是作者当时的自述；本项目没有独立核验他的投资业绩或预测命中率。
- 本项目不能从历史资料判断作者在知识库截止日期之后的真实持仓，也不能提供实时行情。

## 验证内容质量

离线验证：

```bash
python3 -m pip install jieba
python3 -m unittest discover -s tests -v
```

验证包含原文摘录与元数据一致性、日期过滤、关键段落保留，以及两个模型入口传入的材料和规则。服务调用使用模拟对象，不产生 API 费用。

[16个内容评估问题](.claude/skills/jinjiancheng/references/evaluation-cases.json) 用于进一步评估真实回答，包括历史时点、错误前提、资金适配和信息不足等情况。方法见 [内容评估](.claude/skills/jinjiancheng/references/evaluation.md)。离线测试通过不等于这些生成回答已通过评估，也不意味着投资方法已被验证。

## 项目结构

```text
.agents/skills/                 # Codex: links to the four .claude/skills folders
.claude/skills/
  jinjiancheng/SKILL.md
  jinjiancheng/references/        # 共用原则、时间线、来源与评估
  jinjiancheng/agents/openai.yaml # Codex display metadata; each skill has one
  jinjiancheng-cn-stock/SKILL.md
  jinjiancheng-us-stock/SKILL.md
  jinjiancheng-real-estate/SKILL.md
jinjiancheng_grounding.py        # 本地资料与两个入口共用的内容逻辑
jinjiancheng_ai.py               # Anthropic API 入口
jinjiancheng_bedrock.py          # Bedrock 入口
jinjiancheng_knowledge_base.json # 原始知识库
金渐成-历史文章-离线版/           # 原始归档
tests/                         # 离线内容与请求验证
```

## 使用范围

仅供个人学习使用，请勿用于商业目的。原始内容版权归金渐成公众号所有。

生成内容是基于历史文章的分析，不构成作者当前的投资建议。个人决策仍需结合自身处境和经过核实的当前信息。
