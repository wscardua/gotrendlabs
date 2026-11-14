import json
import os
import math

import httpx

from apps.api.backend_api.agent_prompts import (
    COMMENT_JSON_SCHEMA, REVIEW_JSON_SCHEMA, SAFE_COMMENT_TEMPLATE, REVIEW_TEMPLATE,
)


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


def validate_output(value, schema):
    """Validate both providers locally, including Bedrock without strict schema support."""
    kind = schema["type"]
    valid = {"object": type(value) is dict, "array": type(value) is list,
             "string": type(value) is str, "boolean": type(value) is bool,
             "number": type(value) in (int, float)}[kind]
    if not valid:
        raise AgentLLMError("invalid_output_type")
    if "enum" in schema and value not in schema["enum"]:
        raise AgentLLMError("invalid_output_enum")
    if kind == "object":
        if set(value) != set(schema["required"]):
            raise AgentLLMError("invalid_output_fields")
        for key, item in value.items():
            validate_output(item, schema["properties"][key])
    elif kind == "array":
        if len(value) > schema.get("maxItems", 100):
            raise AgentLLMError("invalid_output_array")
        for item in value:
            validate_output(item, schema["items"])
    elif kind == "string" and len(value) > schema.get("maxLength", 10000):
        raise AgentLLMError("invalid_output_length")
    elif kind == "number" and (not math.isfinite(value) or not schema.get("minimum", value) <= value <= schema.get("maximum", value)):
        raise AgentLLMError("invalid_output_number")
    if schema is COMMENT_JSON_SCHEMA:
        has_abstention_reason = value["abstention_reason"] != "not_applicable"
        if has_abstention_reason == value["should_publish"]:
            raise AgentLLMError("invalid_abstention_reason")
    return value


def request_market_comment(*, config, prompt):
    return _request_structured(config=config, prompt=prompt, schema=COMMENT_JSON_SCHEMA,
                               instructions=SAFE_COMMENT_TEMPLATE, stage="generation")


def request_comment_review(*, config, prompt):
    return _request_structured(config=config, prompt=prompt, schema=REVIEW_JSON_SCHEMA,
                               instructions=SAFE_COMMENT_TEMPLATE + REVIEW_TEMPLATE, stage="evaluation")


def _request_structured(*, config, prompt, schema, instructions, stage):
    provider = (config.get("ai_llm_provider") or "openai").lower()
    if provider not in {"openai", "bedrock"}:
        raise AgentLLMError("Provedor LLM não suportado nesta fatia.")
    secret_env = "AWS_BEARER_TOKEN_BEDROCK" if provider == "bedrock" else "OPENAI_API_KEY"
    api_key = os.environ.get(secret_env, "").strip()
    if not api_key:
        raise AgentLLMError(f"{secret_env} ausente.")

    body = {
        "model": config.get("ai_model") or "gpt-5.4-mini",
        "input": [{"role": "system", "content": instructions},
                  {"role": "user", "content": prompt}],
        "store": False,
    }
    if provider == "openai":
        body["text"] = {
            "format": {
                "type": "json_schema",
                "name": f"gotrendlabs_ai_{stage}",
                "strict": True,
                "schema": schema,
            }
        }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    timeout = max(1, int(config.get("ai_openai_timeout_seconds") or 20))
    endpoint = _responses_endpoint(config.get("ai_llm_base_url") or "https://api.openai.com/v1")
    try:
        # Exactly one request per stage; never retry or rewrite automatically.
        response = httpx.post(endpoint, headers=headers, json=body, timeout=timeout)
        if response.status_code >= 400:
            raise AgentLLMError(f"llm_http_{response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise AgentLLMError("invalid_provider_envelope")
        output_text = _extract_output_text(payload)
        if not output_text:
            raise AgentLLMError("missing_output_text")
        return validate_output(json.loads(output_text), schema)
    except AgentLLMError:
        raise
    except httpx.TimeoutException:
        raise AgentLLMError("provider_timeout") from None
    except httpx.HTTPError:
        raise AgentLLMError("provider_network_failure") from None
    except (ValueError, TypeError, AttributeError, KeyError):
        raise AgentLLMError("invalid_or_unavailable_provider_response") from None
