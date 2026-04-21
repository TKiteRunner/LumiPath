"""
笔记服务：Markdown 读写 + frontmatter 解析 + wikilink/tag 抽取
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import frontmatter

from app.config import settings


# ── ParsedNote ────────────────────────────────────────────────────────────────
@dataclass
class ParsedNote:
    metadata: dict = field(default_factory=dict)
    body: str = ""
    wikilinks: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    checksum: str = ""
    word_count: int = 0

    @property
    def title(self) -> str | None:
        # 优先用 frontmatter title，其次取正文第一个 H1
        if fm_title := self.metadata.get("title"):
            return str(fm_title)
        m = re.search(r"^#\s+(.+)$", self.body, re.MULTILINE)
        return m.group(1).strip() if m else None

    @property
    def note_date(self) -> date | None:
        d = self.metadata.get("date")
        if isinstance(d, date):
            return d
        if isinstance(d, str):
            try:
                return date.fromisoformat(d)
            except ValueError:
                return None
        return None

    @property
    def is_private(self) -> bool:
        return bool(self.metadata.get("private", False))


# ── 解析函数 ──────────────────────────────────────────────────────────────────
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]")
_HASHTAG_RE = re.compile(r"(?<!\w)#([\w/\u4e00-\u9fff]+)")


def parse_note(content: str) -> ParsedNote:
    """解析 Markdown 内容，提取 frontmatter/wikilinks/tags。"""
    post = frontmatter.loads(content)
    body: str = post.content

    wikilinks = _WIKILINK_RE.findall(body)
    # 合并 frontmatter tags + 正文 #tag，去重
    fm_tags: list[str] = list(post.metadata.get("tags", []))
    body_tags = _HASHTAG_RE.findall(body)
    all_tags = list(dict.fromkeys(fm_tags + body_tags))

    checksum = hashlib.sha256(content.encode()).hexdigest()
    word_count = len(body.split())

    return ParsedNote(
        metadata=dict(post.metadata),
        body=body,
        wikilinks=wikilinks,
        tags=all_tags,
        checksum=checksum,
        word_count=word_count,
    )


# ── 文件 IO ───────────────────────────────────────────────────────────────────
def get_vault_path(user_id: str) -> Path:
    return Path(settings.vault_base_path) / str(user_id)


def get_daily_note_path(user_id: str, note_date: date) -> Path:
    return get_vault_path(user_id) / "daily" / f"{note_date.isoformat()}.md"


def read_note_file(file_path: Path) -> str:
    """读取 .md 文件内容。文件不存在返回空字符串。"""
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


def write_note_file(file_path: Path, content: str) -> None:
    """原子写：tmp → rename，确保不留半写文件。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = file_path.with_suffix(".md.tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(file_path)
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


# ── 模板渲染 ─────────────────────────────────────────────────────────────────
def render_daily_template(note_date: date) -> str:
    """用 Jinja2 子集渲染日记模板。"""
    from jinja2 import Environment
    env = Environment()

    template_content = """---
type: daily
date: {{ date }}
title: "{{ date }} 学习日志"
mood: focused
energy: 7
tags: []
related_interviews: []
related_okr: []
---

# {{ date }} 学习日志

## 🎯 今日目标
- [ ]
- [ ]

## 📚 学习内容


## 🧠 复盘
### 做得好的

### 待改进

### 关键洞察

## 🔗 关联
- 面试:
- OKR:
- 概念:

## 💡 明日计划
- [ ]
"""
    t = env.from_string(template_content)
    return t.render(date=note_date.isoformat())
