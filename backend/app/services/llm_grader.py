import json
import re
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.core.config import settings


DEFAULT_BASE_URL = "https://sub.vcnovb.cn/v1"
DEFAULT_API_KEY = (
    "sk-a2fc537e653ab9951f509b54332e0b7425bd741070c32b7fb6e045e3e28b0c24"
)
DEFAULT_MODEL = "gpt-5.4"


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").split())


def _build_client() -> AsyncOpenAI:
    base_url = settings.LLM_BASE_URL or DEFAULT_BASE_URL
    api_key = settings.LLM_API_KEY or DEFAULT_API_KEY
    try:
        return AsyncOpenAI(api_key=api_key, base_url=base_url)
    except TypeError as exc:
        if "proxies" not in str(exc):
            raise

        http_client = httpx.AsyncClient()
        return AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client,
        )


def _extract_json_object(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if not text:
        raise ValueError("Empty model response")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")

    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Model response JSON is not an object")
    return parsed


async def grade_submission(
    extracted_text: str,
    assignment_requirements: str,
    grading_rubric: dict | None,
) -> dict:
    normalized_text = _normalize_text(extracted_text)
    normalized_requirements = _normalize_text(assignment_requirements)
    rubric_text = json.dumps(grading_rubric or {}, ensure_ascii=False)
    prompt = (
        "你是一位严厉的大学助教。请根据以下内容打分（0-100分）："
        f"【作业要求：{normalized_requirements}】"
        f"【评分标准：{rubric_text}】"
        f"【学生作答：{normalized_text}】"
        '。返回 JSON 格式：{"score": 整数, "comment": "评语", "reason": "扣分原因"}。'
    )

    try:
        client = _build_client()
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你必须只返回合法 JSON，不要返回 Markdown 代码块。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content if response.choices else ""
        payload = _extract_json_object(content or "")

        raw_score = payload.get("score", 0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0

        score = max(0.0, min(100.0, score))
        comment = str(payload.get("comment", "") or "AI 评分暂时不可用")
        reason = str(payload.get("reason", "") or "模型未返回扣分原因")

        print(f"[LLM] 真实评分完成，分数：{score}")
        return {
            "score": score,
            "comment": comment,
            "reason": reason,
        }
    except Exception as exc:
        print(f"[LLM] API 调用失败: {exc}")
        return {
            "score": 0.0,
            "comment": "AI 评分暂时不可用",
            "reason": f"API 调用失败: {exc}",
        }
