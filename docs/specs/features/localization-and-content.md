---
id: FEAT-I18N-001
titulo: "Localização e conteúdo"
versao: 0.2
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-20
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - i18n-content.md
dependencias:
  - FEAT-AUTH-001
impacta:
  - frontend-web
  - backend-api
  - communications
  - admin-ops
aprovacao: pendente
---

# Localização e conteúdo

## Objetivo

Garantir que interface, emails e conteúdo administrativo do produto sejam compatíveis com operação multilíngue desde o MVP.

## Escopo incluído

- textos fixos de interface
- preferência de idioma
- conteúdo traduzível de mercado
- formatação local

## Escopo excluído

- expansão para múltiplos alfabetos complexos
- tradução automática irrestrita sem rastreabilidade

## Fluxo do usuário

Usuário interage com o sistema no idioma preferido e recebe conteúdo e formatação consistentes com sua localidade.

## Comportamento esperado

- nenhuma tela crítica depende de texto hardcoded
- idioma influencia páginas, emails e mensagens

## Regras de domínio

- conteúdo base e traduzido precisam permanecer rastreáveis
- identificadores não dependem apenas da tradução
- branding visível usa `GoTrendLabs`, preservando `GTL Credits` como nome textual da moeda educativa e identificadores técnicos `gotrendlabs_*`

## Responsabilidades por camada

- `frontend-web`: strings, formatação e renderização local
- `backend-api`: exposição de campos localizáveis e preferência
- `communications`: templates por idioma
- `admin-ops`: revisão e manutenção de conteúdo localizado

## Dados e persistência

- preferência de idioma
- conteúdo base
- variantes traduzidas

## Contratos afetados

- `i18n-content.md`

## Observabilidade e operação

- identificar strings faltantes e falhas de fallback

## Testes esperados

- integração para troca de locale
- fluxo de interface e email nos idiomas suportados

## Critérios de aceite

- sistema funciona em `pt-BR` e `en` sem hardcodes críticos

## Impacto de mudança

Feature transversal; mudanças podem tocar várias specs e contratos ao mesmo tempo.
