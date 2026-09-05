---
id: FEAT-INTEGRITY-001
titulo: "Ledger Criptografico de Integridade para Mercados"
versao: 0.1
status_spec: draft
status_impl: implementada_aguardando_deploy
ultima_atualizacao: 2026-09-05
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - integrity-ledger.md
  - market-lifecycle.md
  - prediction-payloads.md
  - domain-events.md
  - i18n-content.md
dependencias:
  - FEAT-MARKET-001
  - FEAT-MARKET-002
  - FEAT-PRED-001
  - FEAT-RES-001
  - FEAT-NOTIFY-001
impacta:
  - backend-api
  - database
  - scheduler-jobs
  - communications
  - admin-ops
  - frontend-web
  - mobile-flutter
aprovacao: pendente
---

# Ledger Criptografico de Integridade para Mercados

## Objetivo

Criar um registro interno assinado e verificavel para detectar alteracoes indevidas na definicao publicada, nas acoes de previsao, no resultado e no historico final de cada mercado.

O mecanismo oferece rastreabilidade e deteccao criptografica de adulteracao. Nao e blockchain publica, nao e descentralizado e nao promete imutabilidade absoluta.

## Protocolo v1

- identificador: `gtl-integrity/v1`
- canonicalizacao: JSON UTF-8, chaves em ordem lexicografica, separadores compactos, Unicode preservado, timestamps UTC RFC 3339 e numeros monetarios inteiros
- hash: SHA-256, armazenado em hexadecimal minusculo
- assinatura: Ed25519 por AWS KMS `ECC_NIST_EDWARDS25519`/`SIGN_VERIFY`, algoritmo KMS `ED25519_SHA_512`
- entrada assinada: bytes ASCII do hash SHA-256 hexadecimal, enviados como `RAW`
- toda prova preserva payload canonico exato, hash, assinatura, algoritmo, `key_id`, fingerprint SHA-256 da chave publica e timestamp
- `key_id` historico permanece no registro para suportar rotacao

## Estados e transicoes

Fluxo principal: `draft -> scheduled -> open -> locked -> resolved -> sealed`.

Estado terminal alternativo: `canceled`.

- `draft`: campos editaveis.
- `scheduled`: aguarda publicacao/abertura.
- `open`: exige definicao assinada criada atomicamente e bloqueia alteracao de campos protegidos.
- `locked`: nao aceita previsoes e aguarda resultado.
- `resolved`: efeitos atuais de wallet, reputacao, badges e comunicacoes ja ocorreram; `seal_due_at = resolved_at + market_seal_window_hours`.
- `sealed`: final criptografico; nao admite edicao, reabertura, cancelamento ou desfazer resolucao.
- `canceled`: preserva regras de refund atuais; `sealed` nunca transita diretamente para cancelado.

`resolved -> locked` e permitido somente antes de `seal_due_at`, exige motivo e auditoria, reverte os efeitos atuais e limpa `seal_due_at`. Uma nova resolucao inicia janela completa. Depois de `sealed`, correcao cria `market_corrected` append-only referenciando o evento anterior.

## Definicao publicada

Na publicacao, a FastAPI cria `market_integrity_definitions` na mesma transacao da mudanca para `open`. O payload inclui identificador/versao, titulo, resumo, tipo, taxonomia, opcoes ordenadas, criterio e fonte de resolucao, datas, timezone e regra de fechamento. Sem assinatura valida a transacao falha.

Mercados legados ja publicados recebem `integrity_status=legacy_unregistered`; nunca sao assinados retroativamente como prova original.

## Compromissos de previsao

Previsao inicial, reforco e revisao criam recibos distintos em `prediction_commitments`, na mesma transacao da previsao. Falha de assinatura aborta toda a mutacao.

O payload inclui id estavel da acao, mercado, versao da definicao, opcao, stake, sequencia/tipo, timestamp do servidor, `user_commitment` e referencia anterior. `user_commitment` usa HMAC-SHA-256 com segredo controlado pelo servidor e nunca expoe id bruto, email, nome, IP ou token.

## Ledger global

`integrity_ledger_events` e uma cadeia global append-only. Cada insercao obtém lock transacional global, calcula sequencia monotona, `previous_event_hash`, hash canonico e assinatura. Eventos v1: `market_published`, `prediction_committed`, `market_locked`, `market_reopened`, `market_resolved`, `market_resolution_undone`, `market_sealed`, `market_canceled` e `market_corrected`.

Triggers PostgreSQL rejeitam `UPDATE` e `DELETE`; FKs nao usam cascata destrutiva. As tabelas de integridade ficam fora das rotinas comuns de retencao.

## Selagem e Merkle

O daemon seleciona mercados `resolved` vencidos com `FOR UPDATE SKIP LOCKED`. Folhas sao os hashes dos compromissos das posicoes definitivas `resolved`, ordenadas por sequencia da posicao, prediction id e commitment id. Mercado sem previsoes usa SHA-256 de bytes vazios como raiz.

Pares sao concatenados como bytes dos hashes; nivel impar duplica a ultima folha. `market_merkle_leaves` preserva indice, hash da folha e prova com orientacao. A raiz e recalculada antes do commit.

O Seal referencia definicao, versao, raiz, resultado/evidencia/timestamps, mercado, protocolo e evento anterior. A transacao persiste folhas, Seal, evento `market_sealed` e estado `sealed`. Qualquer falha mantem `resolved`, gera log operacional fora da transacao falha e permite retry idempotente.

## Contratos e visibilidade

- visitante: resumo, definicao, Seal, verificacao publica, chave/fingerprint e pacote de prova sem PII
- usuario autenticado: recibo e prova Merkle apenas das proprias previsoes
- admin: estado operacional, falhas/tentativas e auditoria completa
- clientes nao assinam nem decidem validade

Estados publicos de integridade: `not_published`, `legacy_unregistered`, `registered`, `resolved_pending_seal`, `sealed`, `verification_failed`.

## Experiencia web e mobile

Cards mostram sinal discreto com escudo/check:

- `Definicao registrada` para mercado publicado com definicao assinada valida
- `Historico finalizado e verificavel` para mercado `sealed`

O texto e o icone sao acessiveis e nao dependem apenas de cor. `resolved` mostra `Resultado em finalizacao` e horario estimado de selagem. O detalhe oferece `Verificar integridade`, com resumo humano e detalhes tecnicos progressivos. A estetica permanece editorial, sem logos cripto, trading ou apostas.

## Configuracao e operacao

- `market_seal_window_hours`: default 12, faixa 1..168, alteracao auditada no Admin Ops
- producao exige `GOTRENDLABS_INTEGRITY_KMS_KEY_ID` e `GOTRENDLABS_USER_COMMITMENT_SECRET`
- permissao `kms:Sign` fica limitada ao runtime/adaptador de integridade; verificacao usa chave publica em cache
- timeouts/retries KMS sao limitados e auditados sem payload sensivel
- dashboard mostra resolvidos aguardando, proximos do prazo, falhas e selados

## Comunicacoes

`market.sealed` cria notificacao idempotente in-app/push/email para participantes humanos: "Historico finalizado e verificavel: o registro deste mercado esta disponivel para conferencia." Payload externo nao inclui hashes extensos nem dados sensiveis.

## Testes obrigatorios

- publicacao atomica e bloqueio de campos protegidos
- recibos distintos para inicial/reforco/revisao e ausencia de PII
- resolucao/prazo/desfazer e bloqueios apos selagem
- daemon vencimento/idempotencia/concorrencia e falha KMS
- raiz/prova Merkle e adulteracao de definicao, previsao, resultado, raiz, assinatura e elo anterior
- append-only no banco
- permissao/UX Admin Ops
- estados e selos em cards/detalhe web e mobile
- OpenAPI sincronizado e notificacao idempotente
- paginas institucionais sem alegacoes enganosas

## Privacidade e retenção

- `user_commitment` é HMAC-SHA-256 com segredo do servidor e não permite ao público correlacionar diretamente o usuário interno.
- Nome, email, IP, token e identificador bruto não entram em payload público. O compromisso e as provas podem ser retidos quando necessários à auditoria e integridade histórica.
- Exclusão lógica ou retificação de perfil não apaga provas append-only; o atendimento de direitos preserva a separação entre PII operacional e compromisso pseudonimizado.

## Rollout e reversao

1. Aplicar schema e triggers.
2. Criar chave KMS/alias e politica IAM minima; configurar segredo de commitment no secret manager/runtime.
3. Publicar FastAPI/daemon antes de habilitar novos mercados.
4. Validar chave publica e teste de assinatura.
5. Liberar web/mobile compatíveis.

Rollback desabilita novas publicacoes/previsoes se o signer estiver indisponivel, preserva tabelas/provas e retorna daemon para retry. Nunca remover nem reescrever eventos existentes.
