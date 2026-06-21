# Skill: gitdig 新增输出格式

## 目标
帮助开发者给 gitdig 增加新的输出格式（如 Slack 消息、JIRA 注释、HTML 等）。

## 上下文
- 核心文件：`src/gitdig.py`
- 渲染函数约定：接收 `(commits: list[Commit], repo: Path, since: datetime, until: datetime) -> str`
- 已有格式：`render_terminal`（彩色终端）、`render_markdown`（标准 Markdown）、`render_slack`（Slack mrkdwn）
- 格式选择逻辑在 `main()` 函数里的 `fmt` 变量判断处（`if fmt == "md": ... elif fmt == "slack": ...`）

## 步骤

### 1. 新增渲染函数
在 `# ─── 渲染 ───` 区块末尾添加新函数，命名为 `render_<format_name>`。

参考签名：
```python
def render_slack(commits: list[Commit], repo: Path, since: datetime, until: datetime) -> str:
    """生成 Slack-friendly 的 mrkdwn 格式文本"""
    ...
```

### 2. 扩展 --format 参数
在 `build_parser()` 中修改（把新格式名加到 choices 列表里）：
```python
p.add_argument("--format", choices=["terminal", "md", "slack", "<new_format>"], ...)
```

### 3. 在 main() 中接入
在格式判断块中添加对应 elif 分支。

### 4. 写一个简单测试
在 `tests/test_render.py` 中添加测试用例，构造假数据跑通渲染函数。

## 注意
- 不要引入外部依赖，保持零依赖原则
- emoji 在某些环境可能渲染异常，需加 `--no-emoji` 参数时降级为 ASCII 符号
