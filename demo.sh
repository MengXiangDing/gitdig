#!/usr/bin/env bash
# gitdig 演示脚本
# 录屏前：把终端字体调大（18-20px），深色主题

GITDIG="python3 $(dirname "$0")/src/gitdig.py"
REPO_A="$(dirname "$0")"
REPO_B="$HOME/Desktop/mxd/gitdig"

pause() { sleep "${1:-2}"; }

run() {
  echo "$ $*"
  eval "$@"
}

banner() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  pause 1
}

clear

# ── 1. 帮助 ──────────────────────────────────────────────
banner "① 查看帮助"
run $GITDIG --help
pause 3

# ── 2. 最近 7 天（本仓库） ────────────────────────────────
banner "② 过去 7 天的提交"
run $GITDIG --repo "$REPO_A" --since 7d
pause 3

# ── 3. 按作者过滤 ────────────────────────────────────────
banner "③ 只看某位作者的提交"
run $GITDIG --repo "$REPO_B" --since 30d --author "mengxiangding"
pause 3

# ── 4. 多仓库同时查看 ────────────────────────────────────
banner "④ 同时看两个仓库"
run $GITDIG --repo "$REPO_A" --repo "$REPO_B" --since 7d
pause 3

# ── 5. Slack 格式 ────────────────────────────────────────
banner "⑤ 生成 Slack 消息格式（可直接粘贴）"
run $GITDIG --repo "$REPO_B" --since 7d --format slack
pause 3

# ── 6. 输出 Markdown 文件 ────────────────────────────────
banner "⑥ 导出 Markdown 周报"
run $GITDIG --repo "$REPO_A" --since 7d --out /tmp/gitdig-report.md
echo ""
cat /tmp/gitdig-report.md
pause 3

# ── 7. CI 友好模式 ───────────────────────────────────────
banner "⑦ --no-emoji 模式（适合 CI / 纯文本环境）"
run $GITDIG --repo "$REPO_A" --since 7d --no-emoji
pause 2

echo ""
echo "✅  演示完毕"
