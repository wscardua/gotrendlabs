# Contrato: I18n e Conteúdo

## Princípios

- Todo texto fixo da interface deve ser externalizado.
- `pt-BR` é o idioma base atual.
- `en` é o primeiro idioma adicional suportado.

## Regras

- Usuário possui preferência de idioma.
- Datas, números e formatações respeitam localidade ativa.
- Slugs e identificadores não dependem exclusivamente do texto traduzido.
- Conteúdo de mercado traduzido precisa manter rastreabilidade ao conteúdo base.
- A marca pública atual da plataforma é `GoTrendLabs`; nomes técnicos e históricos não precisam ser renomeados quando forem identificadores, caminhos, tabelas, comandos ou registros legados.
- A moeda educativa é exibida em textos de produto como `GT₵`; nomes técnicos, campos e sufixos internos permanecem como `_gtl`.
- Estados técnicos podem ter rótulos públicos diferentes: `locked` deve aparecer para usuários finais como `Em apuração`, preservando `locked`/`Fechado` apenas em contexto técnico, histórico ou operacional.

## Campos de conteúdo com potencial multilíngue

- título do mercado
- descrição
- resolução pública
- emails
- mensagens de interface
- mensagens de reCAPTCHA ausente, inválido, expirado ou indisponível
- mensagens de comentário, reação, convite de login e moderação

## Estado atual

- `pt-BR` permanece como idioma base.
- O branding visível usa `GoTrendLabs`; `GTL Credits` permanece como nome textual da moeda educativa quando aparecer em avisos ou documentação de produto.
- A copy pública do feed usa `Em alta`, `Abertos`, `Em apuração`, `Prever`, `carteira educativa`, `crédito reservado` e `resolução auditável` como glossário base desta fatia.
- A primeira UI de comentários usa textos fixos em `pt-BR`; extração completa para catálogos `pt-BR`/`en` fica para `FEAT-I18N-001`.
- Mensagens de erro de reCAPTCHA permanecem fixas em `pt-BR` nesta fatia; extração para catálogos fica para `FEAT-I18N-001`.
