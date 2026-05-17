---
name: orynth-django-web
description: Use esta skill para implementar a camada web do Orynth com Django, templates server-rendered, HTMX, Alpine.js, i18n de interface e admin Django, sempre respeitando os contratos e limites definidos nas specs.
---

# Orynth Django Web

Use esta skill quando a tarefa principal estiver na camada de apresentação e operação web em Django.

## Objetivo

Implementar páginas, componentes server-rendered, interações HTMX, estados locais simples e telas administrativas sem mover lógica crítica para a UI.

## Fluxo padrão

1. Verificar workflow de implementação aberto quando houver mudança multi-documento.
2. Ler a feature alvo em `docs/specs/features/`.
3. Ler `docs/specs/architecture/frontend-web.md`.
4. Ler os contratos listados no frontmatter da feature.
5. Revisar `docs/specs/testing/` para critérios de aceite e fluxos esperados.
6. Implementar templates, views, formulários, partials HTMX e i18n.
7. Registrar testes executados ou pendentes no workflow/estado.

## Regras

- A UI representa o estado do domínio; ela não redefine a regra.
- Toda mutação relevante deve passar por contratos do backend.
- Não hardcode textos críticos; respeite `pt-BR` e `en`.
- HTMX serve para atualização parcial; Alpine.js serve para estado local simples.
- O admin Django é suporte e operação, não atalho para burlar regras do domínio.
- Mudança visual que altera comportamento deve voltar para a spec antes de fechar.

## Entradas principais

- `docs/specs/features/`
- `docs/specs/architecture/frontend-web.md`
- `docs/specs/contracts/`
- `docs/specs/testing/`

## Saídas esperadas

- páginas e fluxos web coerentes com a spec
- interações HTMX previsíveis
- mensagens e rótulos preparados para i18n
- aderência às fronteiras entre UI e domínio
