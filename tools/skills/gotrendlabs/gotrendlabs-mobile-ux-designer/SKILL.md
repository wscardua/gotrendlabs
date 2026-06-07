---
name: gotrendlabs-mobile-ux-designer
description: Use esta skill para criar ou revisar UX/UI mobile do GoTrendLabs em Flutter, incluindo design system dark-first, telas, componentes, navegação, estados de loading/erro/vazio e aderência às referências visuais fornecidas pelo usuário sem copiar marcas ou telas.
---

# GoTrendLabs Mobile UX Designer

Use esta skill quando a tarefa envolver design, experiência, componentes visuais, telas Flutter, protótipos mobile ou revisão de qualidade visual do app.

## Objetivo

Manter o mobile com experiência dark-first, editorial, densa e própria do GoTrendLabs, inspirada nas referências visuais fornecidas pelo usuário sem copiar identidade, marca ou composição literal.

## Fluxo padrão

1. Ler `docs/specs/features/mobile-ux.md`.
2. Ler `docs/specs/features/mobile-mvp.md`.
3. Revisar telas afetadas contra as referências: cards visuais fortes, detalhe com hero, abas `Visao geral`/`Comunidade`, bottom nav e bottom sheets.
4. Confirmar que a copy preserva moeda educativa e evita linguagem de aposta/trading/dinheiro real.
5. Atualizar critérios visuais em `docs/specs/testing/mobile-acceptance.md` quando o design mudar.
6. Pedir validação visual por emulador/screenshot quando houver implementação.

## Regras

- Primeira tela deve ser experiência útil, não landing page.
- Use imagens/contexto real de mercado quando disponível; fallback visual deve ser legível.
- Cards e detalhes devem proteger legibilidade com overlay, contraste e tipografia adequada.
- Componentes devem ter estados `loading`, `empty`, `error`, `unauthenticated`, `stale` e bloqueado.
- Não copiar marca, naming, textos, ícones proprietários ou layout literal do app de inspiração.
- Evitar termos como `apostar`, `trade`, `cash`, `depósito`, `saque`, `lucro garantido`.
- Controles de previsão não podem induzir opção pré-selecionada.

## Entradas principais

- `docs/specs/features/mobile-ux.md`
- `docs/specs/features/mobile-mvp.md`
- `docs/specs/testing/mobile-acceptance.md`
- referências visuais fornecidas pelo usuário na conversa

## Saídas esperadas

- direção visual consistente
- componentes/telas especificados
- critérios de QA visual atualizados
- riscos de cópia ou desalinhamento de produto sinalizados
