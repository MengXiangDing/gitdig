# gitdig 🔍

> 从 git 历史挖出你的工作日报，一条命令搞定每日站会

## 是什么

`gitdig` 是一个零依赖的 Python CLI 工具，读取本地 git 仓库的提交历史，
按天、按作者分组，生成干净的站会报告 / 周报摘要，输出到终端或 Markdown 文件。

## 解决了什么

每天站会前的那 3 分钟：打开终端、敲 `git log --oneline --since=yesterday`、
手动整理成"我昨天做了……"——重复且烦人。

`gitdig` 一条命令解决：

```bash
gitdig                         # 默认：今天的提交
gitdig --yesterday             # 昨天的工作
gitdig --since 2d              # 过去两天
gitdig --since 1w              # 过去一周
gitdig --repo ~/work/other     # 指定其他仓库
gitdig --author "Alice"        # 过滤作者
gitdig --out report.md         # 输出到文件
```

## 怎么跑

**要求：** Python 3.9+ （无其他依赖）

```bash
# 1. 克隆
git clone <this-repo> gitdig
cd gitdig

# 2. 安装（可选，也可直接 python src/gitdig.py）
pip install -e .

# 3. 跑起来
gitdig --yesterday
```

## 示例输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 2026-06-20  (昨天)   repo: myapp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
● feat: 接入支付宝回调接口            [Alice]  14:32
● fix: 修复订单状态机边界条件          [Alice]  11:08
● chore: 更新依赖版本                  [Bob]   10:15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
共 3 条提交 · 2 位贡献者