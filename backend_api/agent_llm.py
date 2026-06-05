import json
import os
import time

import httpx

from backend_api.agent_prompts import COMMENT_JSON_SCHEMA


class AgentLLMError(Exception):
    pass


def _responses_endpoint(base_url):
    return f"{str(base_url or '').rstrip('/')}/responses"


def _extract_output_text(payload):
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    output = payload.get("output") or []
    chunks = []
    for item in output:
        if item.get("type") not in {"message", "output_text"} and item.get("role") != "assistant":
            continue
        for content in item.get("content") or []:
            if content.get("type") not in {"output_text", "text"}:
                continue
            text = content.get("text")
            if text:
                chunks.append(text)
    return "\n".join(chunks).strip()


def request_market_comment(*, config, prompt):
    provider = (config.get("ai_llm_provider") or "openai").lower()
    if provider not in {"openai", "bedrock"}:
        raise AgentLLMError("Provedor LLM não suportado nesta fatia.")
    secret_env = "AWS_BEARER_TOKEN_BEDROCK" if provider == "bedrock" else "OPENAI_API_KEY"
    api_key = os.environ.get(secret_env, "").strip()
    if not api_key:
        raise AgentLLMError(f"{secret_env} ausente.")

    body = {
        "model": config.get("ai_model") or "gpt-5.4-mini",
        "input": prompt,
        "store": False,
    }
    if provider == "openai":
        body["text"] = {
            "format": {
                "type": "json_schema",
                "name": "gotrendlabs_ai_market_comment",
                "strict": True,
                "schema": COMMENT_JSON_SCHEMA,
            }
        }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    timeout = max(1, int(config.get("ai_openai_timeout_seconds") or 20))
    retries = max(0, int(config.get("ai_openai_max_retries") or 0))
    endpoint = _responses_endpoint(config.get("ai_llm_base_url") or "https://api.openai.com/v1")
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = httpx.post(endpoint, headers=headers, json=body, timeout=timeout)
            if response.status_code >= 400:
                raise AgentLLMError(f"LLM HTTP {response.status_code}: {response.text[:300]}")
            payload = response.json()
            output_text = _extract_output_text(payload)
            if not output_text:
                raise AgentLLMError("Resposta LLM sem output_text.")
            parsed = json.loads(output_text)
            return parsed
        except (httpx.HTTPError, json.JSONDecodeError, AgentLLMError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.5)
    raise AgentLLMError(str(last_error))
