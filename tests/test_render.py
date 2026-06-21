# -*- coding: utf-8 -*-
"""
gitdig 渲染函数单元测试
运行: python3 -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import datetime
from pathlib import Path
from gitdig import (
    Commit,
    render_terminal,
    render_markdown,
    render_slack,
    commit_emoji,
    label_date,
    parse_since,
)
import pytest
from datetime import date, timedelta


# ─── 辅助数据 ────────────────────────────────────────────────────────────────

def make_commits(n=3) -> list[Commit]:
    base = datetime(2026, 6, 20, 10, 0, 0)
    return [
        Commit(
            hash=f"abc{i:05d}",
            author="Alice" if i % 2 == 0 else "Bob",
            timestamp=base.replace(hour=10 + i),
            subject=f"feat: feature number {i}",
        )
        for i in range(n)
    ]

FAKE_REPO = Path("/fake/repo/myapp")
SINCE = datetime(2026, 6, 20, 0, 0, 0)
UNTIL = datetime(2026, 6, 21, 0, 0, 0)


# ─── commit_emoji ────────────────────────────────────────────────────────────

def test_commit_emoji_feat():
    assert commit_emoji("feat: add login") == "✨"

def test_commit_emoji_fix():
    assert commit_emoji("fix: null pointer") == "🐛"

def test_commit_emoji_unknown():
    assert commit_emoji("random commit message") == "●"

def test_commit_emoji_case_insensitive():
    assert commit_emoji("FEAT: uppercase") == "✨"


# ─── label_date ──────────────────────────────────────────────────────────────

def test_label_date_today():
    assert label_date(date.today()) == "今天"

def test_label_date_yesterday():
    assert label_date(date.today() - timedelta(days=1)) == "昨天"

def test_label_date_days_ago():
    label = label_date(date.today() - timedelta(days=5))
    assert "5 天前" in label


# ─── parse_since ─────────────────────────────────────────────────────────────

def test_parse_since_days():
    result = parse_since("3d")
    expected_date = (datetime.now() - timedelta(days=3)).date()
    assert result.date() == expected_date

def test_parse_since_weeks():
    result = parse_since("1w")
    expected_date = (datetime.now() - timedelta(weeks=1)).date()
    assert result.date() == expected_date

def test_parse_since_date_string():
    result = parse_since("2026-01-15")
    assert result.year == 2026
    assert result.month == 1
    assert result.day == 15

def test_parse_since_invalid():
    with pytest.raises(ValueError):
        parse_since("not-a-date")


# ─── render_terminal ─────────────────────────────────────────────────────────

def test_render_terminal_empty():
    out = render_terminal([], FAKE_REPO, SINCE, UNTIL)
    assert "没找到" in out

def test_render_terminal_shows_repo_name():
    commits = make_commits(2)
    out = render_terminal(commits, FAKE_REPO, SINCE, UNTIL)
    assert "myapp" in out

def test_render_terminal_shows_author():
    commits = make_commits(2)
    out = render_terminal(commits, FAKE_REPO, SINCE, UNTIL)
    assert "Alice" in out or "Bob" in out

def test_render_terminal_shows_commit_count():
    commits = make_commits(3)
    out = render_terminal(commits, FAKE_REPO, SINCE, UNTIL)
    assert "3" in out


# ─── render_markdown ─────────────────────────────────────────────────────────

def test_render_markdown_empty():
    out = render_markdown([], FAKE_REPO, SINCE, UNTIL)
    assert "没找到" in out

def test_render_markdown_has_header():
    commits = make_commits(2)
    out = render_markdown(commits, FAKE_REPO, SINCE, UNTIL)
    assert "# gitdig" in out
    assert "myapp" in out

def test_render_markdown_has_hash():
    commits = make_commits(1)
    out = render_markdown(commits, FAKE_REPO, SINCE, UNTIL)
    assert "abc00000" in out


# ─── render_slack ────────────────────────────────────────────────────────────

def test_render_slack_empty():
    out = render_slack([], FAKE_REPO, SINCE, UNTIL)
    assert "没找到" in out

def test_render_slack_bold_repo_name():
    commits = make_commits(2)
    out = render_slack(commits, FAKE_REPO, SINCE, UNTIL)
    assert "*myapp*" in out

def test_render_slack_no_html():
    commits = make_commits(2)
    out = render_slack(commits, FAKE_REPO, SINCE, UNTIL)
    assert "<" not in out
