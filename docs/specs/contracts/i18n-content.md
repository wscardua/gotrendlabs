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
- A primeira UI de comentários usa textos fixos em `pt-BR`; extração completa para catálogos `pt-BR`/`en` fica para `FEAT-I18N-001`.
- Mensagens de erro de reCAPTCHA permanecem fixas em `pt-BR` nesta fatia; extração para catálogos fica para `FEAT-I18N-001`.
