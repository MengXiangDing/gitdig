#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gitdig — git 日报生成器
从本地 git 仓库提取提交历史，生成格式化的站会报告。

用法:
    python src/gitdig.py [options]
    gitdig [options]          # pip install -e . 之后
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import NamedTuple


# ─── 数据结构 ────────────────────────────────────────────────────────────────

class Commit(NamedTuple):
    hash: str
    author: str
    timestamp: datetime
    subject: str


# ─── git 交互 ────────────────────────────────────────────────────────────────

def git_log(repo: Path, since: datetime, until: datetime, author: str = "") -> list[Commit]:
    """调用 git log，返回 Commit 列表。"""
    fmt = "%H\x1f%an\x1f%ai\x1f%s"
    cmd = [
        "git", "-C", str(repo),
        "log",
        f"--since={since.isoformat()}",
        f"--until={until.isoformat()}",
        f"--format={fmt}",
        "--all",
    ]
    if author:
        cmd += [f"--author={author}"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[gitdig] git 出错: {e.stderr.strip()}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("[gitdig] 找不到 git，请先安装 git", file=sys.stderr)
        sys.exit(1)

    commits = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f", 3)
        if len(parts) != 4:
            continue
        hash_, author_name, ts_str, subject = parts
        try:
            # Python 3.9 的 fromisoformat 不支持 "+0800" 格式，需手动处理
            # git 返回格式：2026-06-21 12:48:36 +0800
            ts_clean = ts_str.strip()
            if ts_clean[-5] in ("+", "-") and " " in ts_clean:
                # 去掉末尾时区偏移，直接用本地时间部分
                ts_clean = ts_clean.rsplit(" ", 1)[0]
            ts = datetime.fromisoformat(ts_clean)
        except ValueError:
            continue
        commits.append(Commit(
            hash=hash_[:8],
            author=author_name,
            timestamp=ts,
            subject=subject,
        ))

    return commits


def is_git_repo(path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--git-dir"],
        capture_output=True,
    )
    return result.returncode == 0


# ─── 渲染 ────────────────────────────────────────────────────────────────────

EMOJI_MAP = {
    "feat":    "✨",
    "fix":     "🐛",
    "docs":    "📝",
    "chore":   "🔧",
    "refactor":"♻️",
    "test":    "🧪",
    "perf":    "⚡",
    "style":   "💅",
    "ci":      "🤖",
    "revert":  "⏪",
    "merge":   "🔀",
    "wip":     "🚧",
}

def commit_emoji(subject: str) -> str:
    low = subject.lower()
    for prefix, emoji in EMOJI_MAP.items():
        if low.startswith(prefix):
            return emoji
    return "●"


def label_date(d: date) -> str:
    today = date.today()
    if d == today:
        return "今天"
    elif d == today - timedelta(days=1):
        return "昨天"
    elif d == today - timedelta(days=2):
        return "前天"
    else:
        delta = (today - d).days
        return f"{delta} 天前"


def render_terminal(commits: list[Commit], repo: Path, since: datetime, until: datetime) -> str:
    if not commits:
        return f"  ── 在 {repo.name} 没找到提交记录 ──\n"

    # 按日期分组
    by_day: dict[date, list[Commit]] = {}
    for c in commits:
        day = c.timestamp.date()
        by_day.setdefault(day, []).append(c)

    lines = []
    width = 60
    bar = "─" * width

    for day in sorted(by_day.keys(), reverse=True):
        day_commits = sorted(by_day[day], key=lambda c: c.timestamp, reverse=True)
        label = label_date(day)
        lines.append(f"\n{bar}")
        lines.append(f"📅  {day}  ({label})   仓库: {repo.name}")
        lines.append(bar)
        for c in day_commits:
            icon = commit_emoji(c.subject)
            time_str = c.timestamp.strftime("%H:%M")
            # 右对齐作者和时间
            left = f"  {icon} {c.subject}"
            right = f"[{c.author}]  {time_str}"
            # 简单截断长行
            max_left = width - len(right) - 2
            if len(left) > max_left:
                left = left[:max_left - 1] + "…"
            padding = " " * max(1, width - len(left) - len(right))
            lines.append(f"{left}{padding}{right}")

    authors = sorted({c.author for c in commits})
    lines.append(bar)
    lines.append(f"共 {len(commits)} 条提交 · {len(authors)} 位贡献者 · {', '.join(authors)}")
    lines.append("")
    return "\n".join(lines)


def render_markdown(commits: list[Commit], repo: Path, since: datetime, until: datetime) -> str:
    if not commits:
        return f"_在 `{repo.name}` 没找到提交记录_\n"

    by_day: dict[date, list[Commit]] = {}
    for c in commits:
        day = c.timestamp.date()
        by_day.setdefault(day, []).append(c)

    lines = [f"# gitdig 报告 · {repo.name}\n"]
    lines.append(f"时间范围: `{since.date()}` → `{until.date()}`\n")

    for day in sorted(by_day.keys(), reverse=True):
        day_commits = sorted(by_day[day], key=lambda c: c.timestamp, reverse=True)
        label = label_date(day)
        lines.append(f"## {day} ({label})\n")
        for c in day_commits:
            icon = commit_emoji(c.subject)
            time_str = c.timestamp.strftime("%H:%M")
            lines.append(f"- {icon} **{c.subject}** — {c.author} @ {time_str} `{c.hash}`")
        lines.append("")

    authors = sorted({c.author for c in commits})
    lines.append(f"---\n_共 {len(commits)} 条提交 · {len(authors)} 位贡献者_\n")
    return "\n".join(lines)


# ─── 时间解析 ────────────────────────────────────────────────────────────────

def parse_since(s: str) -> datetime:
    """解析 --since 参数，支持：1d / 2d / 1w / 2w / YYYY-MM-DD"""
    s = s.strip()
    now = datetime.now()

    if s.endswith("d"):
        days = int(s[:-1])
        target = now - timedelta(days=days)
        return target.replace(hour=0, minute=0, second=0, microsecond=0)
    elif s.endswith("w"):
        weeks = int(s[:-1])
        target = now - timedelta(weeks=weeks)
        return target.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # 尝试 YYYY-MM-DD
        return datetime.strptime(s, "%Y-%m-%d")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def render_slack(commits: list[Commit], repo: Path, since: datetime, until: datetime) -> str:
    """生成 Slack mrkdwn 格式，可直接粘贴到 Slack 消息里。"""
    if not commits:
        return f"_在 `{repo.name}` 没找到提交记录_\n"

    by_day: dict[date, list[Commit]] = {}
    for c in commits:
        day = c.timestamp.date()
        by_day.setdefault(day, []).append(c)

    lines = [f"*{repo.name}* 工作汇报"]
    for day in sorted(by_day.keys(), reverse=True):
        day_commits = sorted(by_day[day], key=lambda c: c.timestamp, reverse=True)
        label = label_date(day)
        lines.append(f"\n*{day}* ({label})")
        for c in day_commits:
            icon = commit_emoji(c.subject)
            lines.append(f"  {icon} {c.subject} _{c.author}_ `{c.hash}`")

    authors = sorted({c.author for c in commits})
    lines.append(f"\n共 {len(commits)} 条 · {', '.join(authors)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gitdig",
        description="从 git 历史挖出工作日报",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  gitdig                          今天的提交
  gitdig --yesterday              昨天的提交
  gitdig --since 3d               过去三天
  gitdig --since 1w               过去一周
  gitdig --since 2026-06-01       从某天起
  gitdig --repo ~/work/myapp      指定仓库路径
  gitdig --repo a --repo b        同时看多个仓库
  gitdig --author Alice           只看某人的提交
  gitdig --out report.md          输出到 Markdown 文件
  gitdig --format slack           生成 Slack 消息格式
  gitdig --no-emoji               不用 emoji（CI 友好）
        """,
    )
    p.add_argument("--repo", default=None, metavar="PATH", action="append",
                   help="git 仓库路径（可多次指定；默认：当前目录）")
    p.add_argument("--since", metavar="RANGE",
                   help="起始时间，支持 1d / 2d / 1w / YYYY-MM-DD")
    p.add_argument("--yesterday", action="store_true",
                   help="等价于 --since 1d，只看昨天")
    p.add_argument("--author", default="",
                   help="按作者名过滤（模糊匹配）")
    p.add_argument("--out", metavar="FILE",
                   help="输出到文件（自动推断 Markdown 格式）")
    p.add_argument("--format", choices=["terminal", "md", "slack"], default="terminal",
                   dest="fmt", help="输出格式（默认 terminal）")
    p.add_argument("--no-emoji", action="store_true", dest="no_emoji",
                   help="用 ASCII 符号替代 emoji（终端不支持 emoji 时用）")
    p.add_argument("--version", action="version", version="gitdig 0.1.0")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # no-emoji 模式：替换全局 EMOJI_MAP
    if args.no_emoji:
        for k in EMOJI_MAP:
            EMOJI_MAP[k] = "*"

    # 解析仓库路径（支持多仓库）
    raw_repos = args.repo if args.repo else ["."]
    repos = []
    for r in raw_repos:
        p = Path(r).expanduser().resolve()
        if not p.is_dir():
            print(f"[gitdig] 路径不存在: {p}", file=sys.stderr)
            sys.exit(1)
        if not is_git_repo(p):
            print(f"[gitdig] 不是 git 仓库: {p}", file=sys.stderr)
            sys.exit(1)
        repos.append(p)

    # 解析时间范围
    now = datetime.now()
    if args.yesterday:
        yesterday = now - timedelta(days=1)
        since = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        until = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    elif args.since:
        since = parse_since(args.since)
        until = now
    else:
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        until = now

    # 每个仓库各生成一份报告
    fmt = args.fmt
    if args.out and args.out.endswith(".md") and fmt == "terminal":
        fmt = "md"

    all_output: list[str] = []
    for repo in repos:
        commits = git_log(repo, since, until, author=args.author)
        if fmt == "md":
            block = render_markdown(commits, repo, since, until)
        elif fmt == "slack":
            block = render_slack(commits, repo, since, until)
        else:
            block = render_terminal(commits, repo, since, until)
        all_output.append(block)

    output = "\n".join(all_output)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"[gitdig] 已写入: {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
