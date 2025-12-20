import json
import logging

from django.conf import settings

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_ollama import ChatOllama
except Exception:  # pragma: no cover - optional dependency
    ChatOllama = None
    HumanMessage = None
    SystemMessage = None

logger = logging.getLogger(__name__)


def _strip_code_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_json_object(text: str) -> dict | None:
    if not text:
        return None
    cleaned = _strip_code_fence(text.strip())
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None
    candidate = cleaned[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _generate_product_copy(title: str) -> tuple[dict[str, str] | None, str | None]:
    if not title:
        return None, "Title is required."
    if ChatOllama is None:
        return None, "langchain-ollama is not installed."

    model = getattr(settings, "OLLAMA_MODEL", "llama3.1")
    base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    timeout = float(getattr(settings, "OLLAMA_TIMEOUT", 60))

    system_prompt = (
        "You are a copywriter for ecommerce furniture listings. "
        "Return only JSON with keys: description, seo_title, seo_description."
    )
    user_prompt = (
        f"Title: {title}\n"
        "Requirements:\n"
        "- description is plain text with line breaks.\n"
        '- First line: "Description"\n'
        '- Second line: "FREE SHIPPING"\n'
        "- Third line: blank\n"
        "- Then 6 to 12 short lines of features; no bullets or numbering.\n"
        "- Include the title in one line.\n"
        "- seo_title is 70 characters or fewer.\n"
        "- seo_description is 320 characters or fewer.\n"
        "- Return only JSON."
    )

    llm = ChatOllama(
        model=model,
        base_url=base_url,
        timeout=timeout,
        temperature=0.4,
    )
    try:
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
    except Exception as exc:  # pragma: no cover - network/ollama errors
        logger.warning("Ollama request failed: %s", exc)
        return None, f"Ollama request failed: {exc}"

    content = getattr(response, "content", "") or ""
    data = _extract_json_object(content)
    if not data:
        logger.warning("Ollama response did not contain JSON content.")
        return None, "Ollama response did not contain JSON content."

    result: dict[str, str] = {}
    for key in ("description", "seo_title", "seo_description"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            result[key] = value.strip()

    if not result:
        return None, "Ollama response did not include required fields."
    return result, None


def generate_product_copy(title: str) -> dict[str, str] | None:
    result, _error = _generate_product_copy(title)
    return result


def generate_product_copy_with_error(title: str) -> tuple[dict[str, str] | None, str | None]:
    return _generate_product_copy(title)
