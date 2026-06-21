# /project:review

对 gitdig 当前代码做一轮快速质量审查。

## 检查清单

### 可靠性
- [ ] `git_log()` 对空仓库 / 无提交 / 网络超时是否有兜底？
- [ ] `parse_since()` 对非法输入是否给出友好错误？
- [ ] 仓库路径包含空格时是否正常工作？

### 可用性
- [ ] `--help` 输出是否清晰？示例是否覆盖常见用法？
- [ ] 错误信息是否带 `[gitdig]` 前缀，方便定位？
- [ ] 长提交 subject 截断是否保留语义？

### 代码质量
- [ ] `render_terminal` 和 `render_markdown` 有无重复逻辑可提取？
- [ ] `EMOJI_MAP` 是否覆盖了常见 conventional commit 类型？
- [ ] `label_date()` 是否处理了未来日期边界？

### 安全
- [ ] 传入 `subprocess.run` 的参数是否都经过路径校验，无注入风险？

## 运行方式
在项目根目录执行：
```bash
python3 src/gitdig.py --help
python3 src/gitdig.py --repo . --since 7d
python3 -m pytest tests/ -v   # 如果有测试
```
