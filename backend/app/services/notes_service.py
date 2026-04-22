"""
笔记服务：Markdown 读写 + frontmatter 解析 + wikilink/tag 抽取 + DB 持久化
"""
from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import frontmatter
import structlog
from sqlalchemy import delete, exists, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.note import Note, NoteLink, NoteTag

logger = structlog.get_logger(__name__)


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
# 支持 [[target]], [[target|display]], [[target#anchor]]
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]")
_HASHTAG_RE = re.compile(r"(?<!\w)#([\w/一-鿿]+)")


def parse_note(content: str) -> ParsedNote:
    """解析 Markdown 内容，提取 frontmatter/wikilinks/tags。"""
    post = frontmatter.loads(content)
    body: str = post.content

    wikilinks = _WIKILINK_RE.findall(body)
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
        tmp.unlink(missing_ok=True)
        raise


# ── 模板渲染 ─────────────────────────────────────────────────────────────────
def render_daily_template(note_date: date) -> str:
    from jinja2 import Environment
    env = Environment()
    template_content = """\
---
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


# ── DB 操作 ───────────────────────────────────────────────────────────────────

async def upsert_daily_note(
    user_id: uuid.UUID, note_date: date, content: str, db: AsyncSession
) -> Note:
    """写文件 + upsert DB + 更新 tags/links。"""
    path = get_daily_note_path(str(user_id), note_date)
    write_note_file(path, content)

    parsed = parse_note(content)
    relative_path = f"daily/{note_date.isoformat()}.md"

    note_values: dict = {
        "user_id": user_id,
        "path": relative_path,
        "type": "daily",
        "title": parsed.title or f"{note_date.isoformat()} 学习日志",
        "note_date": note_date,
        "frontmatter": parsed.metadata,
        "content_preview": parsed.body[:500] if parsed.body else None,
        "word_count": parsed.word_count,
        "checksum": parsed.checksum,
        "file_mtime": datetime.now(timezone.utc),
        "is_private": parsed.is_private,
    }

    stmt = (
        pg_insert(Note)
        .values(**note_values)
        .on_conflict_do_update(
            index_elements=["user_id", "path"],
            set_={
                "title": note_values["title"],
                "note_date": note_values["note_date"],
                "frontmatter": note_values["frontmatter"],
                "content_preview": note_values["content_preview"],
                "word_count": note_values["word_count"],
                "checksum": note_values["checksum"],
                "file_mtime": note_values["file_mtime"],
                "is_private": note_values["is_private"],
                "version": Note.version + 1,
                "deleted_at": None,
            },
        )
        .returning(Note)
    )
    result = await db.execute(stmt)
    note: Note = result.scalar_one()

    # 重建 tags
    await db.execute(delete(NoteTag).where(NoteTag.note_id == note.id))
    for tag in parsed.tags:
        db.add(NoteTag(note_id=note.id, tag=tag))

    # 重建 wikilinks
    await db.execute(delete(NoteLink).where(NoteLink.source_note_id == note.id))
    for raw_link in parsed.wikilinks:
        parts = raw_link.split("#", 1)
        slug = parts[0].strip()
        anchor = parts[1].strip() if len(parts) > 1 else None
        db.add(NoteLink(source_note_id=note.id, target_slug=slug, anchor=anchor, display_text=slug))

    await db.flush()
    logger.info("upserted daily note", user_id=str(user_id), date=str(note_date), path=relative_path)
    return note


async def list_notes(
    user_id: uuid.UUID,
    db: AsyncSession,
    type: str | None = None,
    tag: str | None = None,
) -> list[Note]:
    """列出用户笔记（按类型/标签过滤，按日期倒序）。"""
    stmt = select(Note).where(Note.user_id == user_id, Note.deleted_at.is_(None))
    if type:
        stmt = stmt.where(Note.type == type)
    if tag:
        stmt = stmt.where(
            exists().where(NoteTag.note_id == Note.id, NoteTag.tag == tag)
        )
    stmt = stmt.order_by(Note.note_date.desc().nullslast(), Note.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_note(note_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Note:
    """获取单条笔记（带权限校验）。"""
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.deleted_at.is_(None))
    )
    note = result.scalar_one_or_none()
    if not note:
        raise NotFoundError("Note not found")
    if note.user_id != user_id:
        raise ForbiddenError("Not the owner of this note")
    return note


async def delete_note(note_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    """软删除笔记。"""
    note = await get_note(note_id, user_id, db)
    note.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("deleted note", note_id=str(note_id))


async def get_note_content(note_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> str:
    """获取笔记的完整 Markdown 内容（从文件读取）。"""
    note = await get_note(note_id, user_id, db)
    file_path = get_vault_path(str(user_id)) / note.path
    return read_note_file(file_path)


# ── NotesService 类封装（供 Tool / Worker 使用）────────────────────────────────

class NotesService:
    """
    对外暴露的笔记服务类，封装模块级函数，方便 Tool 层依赖注入使用。
    """

    async def get_or_create_daily_note(
        self, user_id: str, note_date: str, db: AsyncSession | None = None
    ) -> tuple[str, dict]:
        """
        获取（或创建）指定日期的 daily note 文件内容。
        返回 (content_str, meta_dict)。meta_dict 含 id / path 等字段。
        """
        from app.db.engine import AsyncSessionLocal
        target_date = date.fromisoformat(note_date)
        path = get_daily_note_path(str(user_id), target_date)

        if path.exists():
            content = read_note_file(path)
        else:
            content = render_daily_template(target_date)

        # 查 DB 拿 meta
        meta: dict = {}
        async with _async_session(db) as session:
            result = await session.execute(
                select(Note).where(
                    Note.user_id == uuid.UUID(user_id),
                    Note.path == f"daily/{note_date}.md",
                    Note.deleted_at.is_(None),
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                meta = {"id": str(existing.id), "path": existing.path}

        return content, meta

    async def upsert_daily_note(
        self, user_id: str, note_date: str, content: str, db: AsyncSession | None = None
    ) -> Note:
        """写文件 + upsert DB（async 版本，供 Tool 层调用）。"""
        from app.db.engine import AsyncSessionLocal
        target_date = date.fromisoformat(note_date)
        async with _async_session(db) as session:
            note = await upsert_daily_note(
                user_id=uuid.UUID(user_id),
                note_date=target_date,
                content=content,
                db=session,
            )
            await session.commit()
        return note

    def upsert_from_file_path_sync(
        self, user_id: str, file_path: str, parsed: "ParsedNote", db: "Session"
    ) -> None:
        """
        同步版本（供 Celery worker 使用），将文件解析结果回写 DB。
        db 是 sqlalchemy 同步 Session。
        """
        from sqlalchemy import text as sa_text
        from datetime import timezone
        import json as _json

        relative_path = str(Path(file_path).relative_to(Path(settings.vault_base_path) / user_id))
        note_date_val = parsed.note_date
        now = datetime.now(timezone.utc)

        db.execute(
            sa_text("""
                INSERT INTO notes (id, user_id, path, type, title, note_date, frontmatter, content_preview,
                                   word_count, checksum, file_mtime, is_private, created_at, updated_at, version)
                VALUES (:id, :uid, :path, :type, :title, :ndate, :fm::jsonb, :preview,
                        :wc, :csum, :mtime, :priv, :now, :now, 1)
                ON CONFLICT (user_id, path) DO UPDATE SET
                    title          = EXCLUDED.title,
                    note_date      = EXCLUDED.note_date,
                    frontmatter    = EXCLUDED.frontmatter,
                    content_preview= EXCLUDED.content_preview,
                    word_count     = EXCLUDED.word_count,
                    checksum       = EXCLUDED.checksum,
                    file_mtime     = EXCLUDED.file_mtime,
                    is_private     = EXCLUDED.is_private,
                    updated_at     = EXCLUDED.updated_at,
                    version        = notes.version + 1,
                    deleted_at     = NULL
            """),
            {
                "id": str(uuid.uuid4()),
                "uid": user_id,
                "path": relative_path,
                "type": parsed.metadata.get("type", "free"),
                "title": parsed.title or relative_path,
                "ndate": note_date_val,
                "fm": _json.dumps(parsed.metadata, default=str),
                "preview": parsed.body[:500],
                "wc": parsed.word_count,
                "csum": parsed.checksum,
                "mtime": now,
                "priv": parsed.is_private,
                "now": now,
            },
        )
        db.commit()


# ── 内部 session 工具 ─────────────────────────────────────────────────────────

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession


@asynccontextmanager
async def _async_session(db: AsyncSession | None):
    from app.db.engine import AsyncSessionLocal
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
