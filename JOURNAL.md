# JOURNAL — gitdig 开发流水账

> 这是用 Claude Code (CC) + superpowers 插件做 gitdig 的完整记录。

---

## Day-by-day: 装 superpowers，搞清楚要做什么

### 搞清楚 superpowers 是啥

一开始以为 superpowers 是个 npm 包，搜了半天没找到对。后来看了一眼官方 plugin 页面（https://claude.com/plugins/superpowers），才知道要在 CC 会话里用 `/plugin` 命令装：

```bash
# 方式一：官方 marketplace（最简单）
/plugin install superpowers@claude-plugins-official

# 方式二：community marketplace（如果上面装不上）
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

装完重启 CC，控制台出现了一行确认：

```
SessionStart:startup hook succeeded: Success
```

这说明 superpowers 的 hook 已经生效。之后 `/help` 里多了几个命令：
- `/superpowers:brainstorm` — Socratic 式提问，逼你把需求想清楚再动手
- `/superpowers:write-plan` — 生成分步执行计划
- `/superpowers:execute-plan` — 按计划批量执行

第一反应：**感觉有点啰嗦**。我只想做个小工具，非要走 brainstorm → plan → execute 三步流程，有点像项目管理工具硬套到写脚本上。

但还是老老实实跑了一遍 `/superpowers:brainstorm`。

提问过程大概是这样的（摘录核心几轮）：

> **superpowers:** 你要解决什么具体痛点？
> **我:** 每天站会前要手动 `git log --oneline --since=yesterday`，然后整理
> **superpowers:** 你的「用户」只有你自己吗？还是团队共享？
> **我:** 主要自用，但想让它可以看多个仓库
> **superpowers:** 输出格式固定还是可配置？
> **我:** …（被问到才意识到自己没想过 Slack 粘贴场景）

**"原来还能这样"之一：** brainstorm 强制让我想出了 `--format slack` 这个用例，原本根本没打算做。这个功能是被问出来的，不是我主动设计的。

### 写代码，踩第一个坑

核心逻辑写完，第一次测试：

```bash
python3 src/gitdig.py --since 7d
# 输出: ── 在 gitdig 没找到提交记录 ──
```

仓库里明明有两个 commit。排查了一会儿，发现是 `datetime.fromisoformat()` 在 Python 3.9 不支持 `2026-06-21 12:48:36 +0800` 这种带时区的格式，直接 `ValueError` 被吞掉了，提交全部跳过。

**卡了约 20 分钟**。修法很简单，手动截掉时区部分再解析：

```python
ts_clean = ts_str.rsplit(" ", 1)[0]  # 去掉 "+0800"
ts = datetime.fromisoformat(ts_clean)
```

这个 bug 比较典型：不报错、只是悄悄不返回数据。如果没写测试，可能很晚才发现。

---

### 测试、多仓库、打磨边界

跑完测试 21 passed，整体比较满意。

发现了一个设计缺陷：`EMOJI_MAP` 是个模块级 dict，`--no-emoji` 直接 mutate 了它，如果在同一进程里多次调用 `main()` 会有副作用。对 CLI 工具无所谓，对库来说不对。记下来但不改——这是个 CLI，over-engineering 没必要。

---

## 我对 CC 的认知变化

### 刚开始使用的认知

"CC 就是个高级 shell 助手，帮我写代码、执行命令。superpowers 感觉是强迫症附件。"

用法：把需求直接扔给 CC，期待它一次性出正确结果。

### 使用完之后的认知

CC 的价值不只是「生成代码」，更在于**把隐性的设计决策显式化**。

具体例子：

1. **superpowers 的 brainstorm 阶段**——一开始觉得烦，但它问的那些问题（"你的用户只有你？""输出固定格式还是可配置？"），其实是好的设计 review 提问。我自己写代码时经常跳过这些问题，等写到一半发现接口设计不对再改。

2. **execute-plan 的批次执行**——CC 会把大任务拆成小步骤，每步骤有 checkpoint。这对我这种倾向于一口气写完再测试的习惯是个反力。虽然有时感觉打断了心流，但确实减少了「写了 200 行发现方向错了」的情况。

---

## 至少两件"原来还能这样"的事

### 1. brainstorm 能问出你自己没意识到的需求

上面说了，`--format slack` 是被 superpowers 问出来的。这让我意识到：对于 CC 来说，最有价值的不是「帮我写这段代码」，而是「帮我想清楚这件事值不值得做、怎么做」。

### 2. `.claude/skills/` 可以作为项目内的"给 AI 的 README"

我给 gitdig 写了 `gitdig-extend.md`，描述如何给它加新输出格式。下次在 CC 里说「给 gitdig 加 HTML 格式」，CC 会自动加载这个 skill，直接按照里面的步骤走，不用再解释项目结构。

**这改变了我对文档的态度**：以前写 README 是给人看的，现在还要给 AI 看，写法不一样——人看文档要叙述性，AI 看 skill 要结构化、步骤明确。

---

## 至少一件"这玩意还不行"的事

### CC 对"我刚才改了什么"的上下文感知很差

做 multi-repo 支持时，我让 CC 帮我改 `build_parser()` 里的 `--repo` 参数，从 `default="."` 改成支持 `action="append"`。

CC 改完之后，忘记同步更新 `main()` 里对 `args.repo` 的读取逻辑（原来是直接用 `args.repo`，改成 append 后应该判断 `None`）。

**提示片段（复现）：**

```
我: 把 --repo 改成支持多次指定
CC: [修改了 build_parser，加了 action="append"]
    [没动 main() 里的 args.repo 读取]
我: 报错了，args.repo 是 None
CC: 啊对，我漏了 main() 那边，补上
```

这是个经典的「局部改对了、全局没跟上」问题。CC 改单一函数很准，但跨函数的联动影响需要我显式指出。

**结论：** CC 目前不擅长「这里改了，那里要联动改」的影响面推断，特别是对没有测试覆盖的路径。这也是为什么写测试不是锦上添花——它强迫你把联动关系显式化。

---

## 再给一周我会怎么改进

1. **加 `--interactive` 模式**：让用户从列表里勾选要包含的提交，再生成报告。用 Python `curses` 或简单的序号选择都行。

2. **支持配置文件**：`~/.gitdigrc` 配置默认仓库列表，不用每次 `--repo a --repo b`。

3. **加 `--copy` 标志**：直接把输出复制到剪贴板（macOS 用 `pbcopy`，Linux 用 `xclip`），站会前一条命令 + 粘贴搞定。

4. **加 CI hook**：在 `.claude/hooks/` 里写一个 pre-commit hook，每次提交前用 gitdig 检查一下 commit message 是否符合 conventional commits 格式——把工具自身用起来。

5. **修掉 EMOJI_MAP mutation 问题**：改成在 `render_*` 函数里接受参数，而不是 mutate 全局变量。

---

## 换个角色思考

假设我要给一个**完全没碰过 CC 的产品同学**配置 CC 让她开始用，我会怎么做？

她的日常工作是：写需求文档（飞书文档）、整理会议纪要、管理需求优先级、跟研发对齐技术方案。

### 我会给她配什么

**Skill 1: `prd-writer`**
帮她把一句话需求扩展成结构化 PRD 草稿，包含背景、目标用户、功能列表、边界 case。
为什么：她最费时间的是从「领导说了一句话」到「写出一份让研发看懂的文档」，这段转化 CC 擅长。

**Skill 2: `meeting-follow-up`**
读取飞书妙记逐字稿，提取 Action Items、结论、待确认问题，生成飞书任务。
为什么：会议结束后 30 分钟之内要出纪要，她每次都很头疼。这个 skill 能把 AI 接入她的日常节奏，而不是让她专门「开一个 AI 会话」。

**Hook: `on-doc-save`**
文档保存时自动检查：有没有缺少「验收标准」字段？有没有遗漏「影响范围」？
为什么：她写 PRD 经常漏字段，研发追问。Hook 把检查变成自动的，不需要她主动想。

### 关键原则

不要让她「先学 CC」，要让 CC 嵌进她**已有的工作流**里。
对产品同学来说，最大的阻力不是技术，而是「我为什么要多开一个工具」。
所以 skill 的触发场景要和她已有的飞书文档、会议工作流直接挂钩，
而不是让她在 CC 里重新建立工作习惯。

第一周目标：让她有一次「这玩意帮我省了 20 分钟」的真实体感。有了这次体感，她会自己来找更多用法。

