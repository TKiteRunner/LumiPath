"""
GenerateReviewTool — LiteLLM 生成面试复盘报告，写入 interview_reviews 表。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
import uuid

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.base import BaseTool, register_tool
from app.agents.llm import chat
from app.db.engine import AsyncSessionLocal

logger = structlog.get_logger(__name__)

_REVIEW_PROMPT = """你是一位专业的面试复盘教练。请根据以下面试记录，生成结构化的复盘报告。

## 面试信息
- 公司：{company}
- 职位：{role}
- 轮次：第 {round} 轮
- 状态：{status}
- 时间：{scheduled_at}

## 面试题目及回答
{questions_block}

## 要求
请输出严格的 JSON，字段如下：
{{
  "summary": "整体复盘总结（200字以内）",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["待改进1", "待改进2"],
  "improvement_plan": "具体改进计划（markdown格式）",
  "score_overall": 75
}}
只输出 JSON，不要有任何额外文字。"""


@register_tool(name="generate_review", version="1.0.0")
class GenerateReviewTool(BaseTool):

    async def execute(self, user_id: str, interview_id: str = "", model: str = "gpt-4o-mini", db: AsyncSession | None = None, **kwargs) -> dict[str, Any]:
        if not interview_id:
            return {"status": "error", "message": "interview_id is required"}

        async with _session(db) as session:
            # 1. 查面试基础信息
            interview_row = await session.execute(
                text("""
                    SELECT i.id, i.role, i.round, i.status, i.scheduled_at, i.notes,
                           c.name AS company_name
                    FROM interviews i
                    JOIN companies c ON c.id = i.company_id
                    WHERE i.id = :iid AND i.user_id = :uid AND i.deleted_at IS NULL
                """),
                {"iid": interview_id, "uid": user_id},
            )
            interview = interview_row.mappings().one_or_none()
            if not interview:
                return {"status": "error", "message": "Interview not found"}

            # 2. 查题目
            q_rows = await session.execute(
                text("""
                    SELECT question_text, my_answer, standard_answer, category, score
                    FROM interview_questions
                    WHERE interview_id = :iid
                    ORDER BY order_index
                """),
                {"iid": interview_id},
            )
            questions = [dict(r) for r in q_rows.mappings().all()]

        # 3. 拼 prompt
        q_block = "\n\n".join(
            f"**Q{i+1}** [{q.get('category','')}]：{q['question_text']}\n"
            f"我的回答：{q.get('my_answer') or '（未记录）'}\n"
            f"参考答案：{q.get('standard_answer') or '（未记录）'}"
            for i, q in enumerate(questions)
        )
        prompt = _REVIEW_PROMPT.format(
            company=interview["company_name"],
            role=interview["role"],
            round=interview["round"],
            status=interview["status"],
            scheduled_at=str(interview["scheduled_at"] or "未记录"),
            questions_block=q_block or "（无题目记录）",
        )

        # 4. LLM 调用
        try:
            raw = await chat(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.3,
                max_tokens=1500,
            )
            review_data = json.loads(raw)
        except json.JSONDecodeError:
            review_data = {"summary": raw, "strengths": [], "weaknesses": [], "improvement_plan": "", "score_overall": None}
        except Exception as exc:
            logger.error("GenerateReview LLM failed", error=str(exc))
            return {"status": "error", "message": str(exc)}

        # 5. 写入 interview_reviews（upsert）
        now = datetime.now(timezone.utc)
        async with _session(db) as session:
            await session.execute(
                text("""
                    INSERT INTO interview_reviews
                        (id, interview_id, summary, strengths, weaknesses, improvement_plan, score_overall, ai_model, generated_at, version)
                    VALUES
                        (:id, :iid, :summary, :strengths, :weaknesses, :plan, :score, :model, :now, 1)
                    ON CONFLICT (interview_id) DO UPDATE SET
                        summary          = EXCLUDED.summary,
                        strengths        = EXCLUDED.strengths,
                        weaknesses       = EXCLUDED.weaknesses,
                        improvement_plan = EXCLUDED.improvement_plan,
                        score_overall    = EXCLUDED.score_overall,
                        ai_model         = EXCLUDED.ai_model,
                        generated_at     = EXCLUDED.generated_at,
                        version          = interview_reviews.version + 1
                """),
                {
                    "id": str(uuid.uuid4()),
                    "iid": interview_id,
                    "summary": review_data.get("summary", ""),
                    "strengths": review_data.get("strengths", []),
                    "weaknesses": review_data.get("weaknesses", []),
                    "plan": review_data.get("improvement_plan", ""),
                    "score": review_data.get("score_overall"),
                    "model": model,
                    "now": now,
                },
            )
            await session.commit()

        logger.info("GenerateReviewTool", user_id=user_id, interview_id=interview_id)
        return {"status": "ok", "interview_id": interview_id, "review": review_data}

    @property
    def tool_schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "description": "Generate an AI interview review report for a completed interview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "interview_id": {"type": "string", "description": "UUID of the interview to review"},
                    "model": {"type": "string", "default": "gpt-4o-mini", "description": "LLM model to use"},
                },
                "required": ["interview_id"],
            },
        }


from contextlib import asynccontextmanager


@asynccontextmanager
async def _session(db: AsyncSession | None):
    if db is not None:
        yield db
    else:
        async with AsyncSessionLocal() as session:
            yield session
