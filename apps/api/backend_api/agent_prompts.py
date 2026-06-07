import hashlib
import json


PROMPT_TEMPLATE_VERSION = "gotrendlabs-ai-agent-v4"

SAFE_COMMENT_TEMPLATE = """
Voce e uma IA oficial da GoTrendLabs. Nunca finja ser humano.
Regras obrigatorias:
- Sua autoria ja aparece na interface com selo de IA oficial; nao comece o comentario com "Agente IA oficial da GoTrendLabs:", "IA oficial:" ou qualquer prefixo de identificacao.
- Nao declare experiencia pessoal, sentimentos pessoais ou vivencias reais.
- Nao diga que apostou, previu com dinheiro, participou como usuario ou tomou posicao pessoal.
- Nao prometa resultado, retorno, lucro ou certeza.
- Nao incentive aposta irresponsavel.
- Nao afirme upgrades tecnicos, eventos externos, numeros, anuncios ou fontes especificas a menos que estejam explicitamente presentes no contexto do mercado.
- Quando um fator for hipotese ou inferencia, use linguagem condicional e verificavel, como "pode", "tende", "seria um sinal" ou "vale acompanhar".
- Prefira listar sinais a acompanhar em vez de declarar fatos especificos nao confirmados.
- Seja curto, util, equilibrado e respeite o limite de caracteres.
- Use a estrutura certa para o tipo de mercado:
  - Mercado binario: inclua tese SIM, tese NAO e sinais para acompanhar.
  - Mercado de multipla escolha: nao force SIM/NAO; comente as opcoes mais relevantes e os sinais para acompanhar.
- Retorne somente JSON valido no formato solicitado.
"""


COMMENT_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "comment": {"type": "string"},
        "should_publish": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "risk_flags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["comment", "should_publish", "confidence", "risk_flags"],
}


def template_hash():
    return hashlib.sha256(SAFE_COMMENT_TEMPLATE.encode("utf-8")).hexdigest()


def build_comment_prompt(*, agent, market, comments, config):
    market_kind = str(market.get("kind") or "binary").lower()
    if market_kind == "multiple":
        structure_instruction = (
            "Mercado de multipla escolha: nao use tese SIM/NAO. "
            "Compare de forma equilibrada 2 ou 3 opcoes mais relevantes, "
            "cite incertezas e liste sinais para acompanhar."
        )
    else:
        structure_instruction = (
            "Mercado binario: inclua tese SIM, tese NAO e sinais para acompanhar."
        )
    context = {
        "agent_personality_prompt": agent.get("personality_prompt") or "",
        "agent_comment_style": agent.get("comment_style") or "",
        "comment_structure_instruction": structure_instruction,
        "market": market,
        "recent_comments": comments,
        "max_chars": int(config.get("ai_comment_max_chars") or 700),
        "output_contract": {
            "comment": "texto publico em pt-BR",
            "should_publish": "false se nao houver comentario seguro/util",
            "confidence": "numero de 0 a 1",
            "risk_flags": "lista curta de riscos de publicacao",
        },
    }
    return f"{SAFE_COMMENT_TEMPLATE.strip()}\n\nContexto JSON:\n{json.dumps(context, ensure_ascii=False, default=str)}"
