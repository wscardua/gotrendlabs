---
id: FEAT-INTEGRITY-001
titulo: "Ledger Criptografico de Integridade para Mercados"
versao: 1.2
status_spec: aprovada
status_impl: implementada_validada
ultima_atualizacao: 2026-09-07
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
aprovacao: aprovada_pelo_usuario_em_2026-09-07
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
- chaves publicas historicas ficam em `integrity_signing_keys`, com protecao append-only; isso permite verificacao apos rotacao/reinicio sem persistir ou exportar material privado

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

Como a plataforma ainda não foi lançada ao público, mercados atuais sem definição assinada não são migrados nem permanecem no catálogo. Um comando operacional explícito, idempotente e protegido por `dry-run` remove todos os mercados sem `market_integrity_definitions`, inclusive rascunhos/agendados pré-lançamento, e seus efeitos operacionais relacionados, depois de inventário e snapshot validado. Toda publicação criada após o corte deve ter definição assinada pelo fluxo autoritativo; a API preserva defesa para recusar previsão ou selagem sem essa prova.

## Compromissos de previsao

Previsao inicial, reforco e revisao criam recibos distintos em `prediction_commitments`, na mesma transacao da previsao. Falha de assinatura aborta toda a mutacao.

O payload inclui id estavel da acao, mercado, versao da definicao, opcao, stake, sequencia/tipo, timestamp do servidor, `user_commitment` e referencia anterior. `user_commitment` usa HMAC-SHA-256 com segredo controlado pelo servidor e nunca expoe id bruto, email, nome, IP ou token.

## Ledger global

`integrity_ledger_events` e uma cadeia global append-only. Cada insercao obtém lock transacional global, calcula sequencia monotona, `previous_event_hash`, hash canonico e assinatura. Eventos v1: `market_published`, `prediction_committed`, `market_locked`, `market_reopened`, `market_resolved`, `market_resolution_undone`, `market_sealed`, `market_canceled` e `market_corrected`.

A assinatura de cada evento vincula todos os seus metadados persistidos: protocolo, tipo de evento, tipo/identificador da entidade, mercado, referencia/hash do payload, sequencia, elo anterior, timestamp e IDs opcionais de correlacao/causalidade. A verificacao tambem confere algoritmo e fingerprint contra a chave publica historica identificada por `key_id`; alterar qualquer coluna protegida invalida o evento.

Triggers PostgreSQL rejeitam `UPDATE` e `DELETE`; FKs nao usam cascata destrutiva. As tabelas de integridade ficam fora das rotinas comuns de retencao.

## Checkpoints e verificacao incremental

`integrity_ledger_checkpoints` preserva atestacoes assinadas e append-only da auditoria global. O payload inclui intervalo e quantidade de eventos verificados, head observado, ultimo hash valido, checkpoint anterior, tipo `full`/`incremental`, versao do verificador, estado e eventual sequencia/codigo da primeira divergencia.

O daemon verifica somente eventos posteriores ao ultimo checkpoint valido em cada ciclo. Sem checkpoint ou ao completar 24 horas desde a ultima auditoria integral, percorre a cadeia desde o primeiro evento. Depois de divergencia confirmada, uma falha identica no mesmo head e reutilizada por ate uma hora sem nova assinatura; mudanca do head, solicitacao explicita ou fim do backoff dispara nova auditoria integral. Isso preserva alerta recorrente sem varredura `O(E)` e chamada KMS a cada ciclo de cinco minutos.

A consulta publica valida assinatura/hash do checkpoint mais recente e compara sua sequencia/hash ao head atual; nunca percorre toda a cadeia. Head posterior gera `pending`, head regressivo ou divergente gera `failed`, e ausencia de checkpoint gera `unavailable`. A selagem adquire o lock global e executa auditoria integral fresca ate o head capturado na mesma transacao antes de avaliar o mercado. Assim, nenhum evento historico fica confiado apenas ao checkpoint anterior no momento irreversivel do Seal.

## Selagem e Merkle

O daemon seleciona mercados `resolved` vencidos com `FOR UPDATE SKIP LOCKED`. Folhas sao os hashes dos compromissos das posicoes definitivas `resolved`, ordenadas por sequencia da posicao, prediction id e commitment id. Mercado sem previsoes usa SHA-256 de bytes vazios como raiz.

Pares sao concatenados como bytes dos hashes; nivel impar duplica a ultima folha. `market_merkle_leaves` preserva indice, hash da folha e prova com orientacao. A raiz e recalculada antes do commit.

O Seal referencia definicao, versao, raiz, resultado/evidencia/timestamps, mercado, protocolo e evento anterior. A transacao persiste folhas, Seal, evento `market_sealed` e estado `sealed`. Qualquer falha mantem `resolved`, gera log operacional fora da transacao falha e permite retry idempotente.

## Contratos e visibilidade

- visitante: resumo, definicao, Seal, eventos publicos do ciclo do mercado, totais agregados de compromissos, chave/fingerprint e pacote de prova sem PII nem referencia individual de previsao
- usuario autenticado: recibo e prova Merkle apenas das proprias previsoes
- admin: estado operacional, falhas/tentativas e auditoria completa
- clientes nao assinam nem decidem validade

Estados publicos de integridade: `not_published`, `registered`, `resolved_pending_seal`, `seal_retry_pending`, `canceled_preserved`, `sealed`, `verification_failed`.

`legacy_unregistered` permanece apenas como valor defensivo temporario para diagnosticar dado inconsistente durante a limpeza; nao pode ser estado de um mercado ativo apresentado no catalogo apos o corte.

- `seal_retry_pending` significa falha operacional de assinatura/persistencia com nova tentativa segura pendente; nao indica adulteracao.
- `canceled_preserved` significa que o mercado foi cancelado e os registros de integridade ja emitidos foram preservados; resultado e Seal sao etapas nao aplicaveis.
- `verification_failed` fica reservado a inconsistencia criptografica comprovada ou ausencia de prova obrigatoria em qualquer estado publicado. Um alerta de integridade pendente prevalece sobre `registered`, `resolved_pending_seal` e `sealed` nos resumos consumidos por cards web/mobile, impedindo selo verde enquanto a divergencia conhecida nao for resolvida e revalidada.

A verificacao publica nao valida apenas os bytes armazenados contra si mesmos. Ela tambem reconstrói a definicao atual do mercado e o resultado operacional atual para compara-los aos snapshots assinados. Em mercado selado, valida ainda cada compromisso assinado incluido nas folhas, a raiz/provas Merkle, o Seal e a cadeia global. Validadores confrontam payload, chave publica, algoritmo, fingerprint, protocolo, timestamps, identificadores relacionais, referencias anteriores e demais metadados persistidos aplicaveis. Campos nao aplicaveis sao `null`, nunca tratados como falha.

A prova publica omite eventos `prediction_committed`, IDs de compromisso, timestamps individuais de previsao e qualquer outra referencia que permita individualizar uma acao. Ela expoe apenas `count`, inclusao no Seal e `predictions_root` agregado quando existente. Recibos e provas individuais continuam restritos ao proprio usuario; a auditoria completa continua restrita ao Admin Ops.

O contrato final usa `market_valid`, `ledger_chain_valid` e `overall_valid`, todos nullable quando ainda nao existe evidencia suficiente. `verification_status` distingue `verified`, `pending`, `failed` e `unavailable`. Falha especifica do mercado ou global produz `overall_valid=false`; backlog normal do daemon produz `overall_valid=null`, nunca falso positivo nem alegacao de adulteracao. Seal exige `overall_valid=true`.

## Experiencia web e mobile

Cards web preservam integralmente a thumbnail do mercado e mostram um selo iconizado com escudo/check sobreposto no canto superior direito da imagem:

- `Definicao registrada` para mercado publicado com definicao assinada valida
- `Historico finalizado e verificavel` para mercado `sealed`

O selo nao substitui imagem, fallback ou icone editorial do mercado. Seu nome acessivel comunica o estado sem depender apenas de cor; o texto completo aparece em tooltip e na experiencia de verificacao.

No web, o selo abre a verificacao em modal tanto no card quanto no detalhe do mercado, com a rota publica completa preservada como fallback sem JavaScript. O modal prioriza explicacoes para publico leigo, responde o que foi protegido e o que cada verificacao significa, e deixa hashes, chave, protocolo e pacote em uma secao tecnica progressiva. `resolved` mostra `Resultado em finalizacao` e horario estimado de selagem. A estetica permanece editorial, sem logos cripto, trading ou apostas.

No detalhe de um mercado `sealed`, o estado principal aparece como `Mercado concluido` para deixar claro que previsoes, apuracao e resultado ja terminaram. A explicacao complementar informa que o resultado foi publicado e que o registro de integridade foi finalizado; o rotulo compacto usa `Concluido e verificavel`. A verificacao continua acessivel somente pelo escudo sobre a thumbnail, sem botao textual redundante.

O bloco lateral do detalhe se apresenta como `Ciclo do mercado` e usa copy publica coerente em todos os estados: `Mercado agendado`, `Mercado em apuracao`, `Resultado publicado`, `Mercado concluido` e `Mercado cancelado`. Mercados que ja nao aceitam previsoes nunca exibem `Fecha em` nem contagem regressiva de fechamento. O estado `resolved` diferencia resultado publicado de registro de integridade ainda em finalizacao. Em `sealed`, a ultima etapa do ciclo aparece concluida, nao em processamento.

A primeira leitura da verificacao deve responder, nesta ordem: para que a pagina serve; se alguma alteracao indevida foi detectada; quais etapas da vida do mercado ja foram protegidas; e o que aconteceria se um registro fosse alterado. Limites e ressalvas nao formam uma secao destacada no modal compacto; a transparencia institucional e tecnica permanece no rodape, nas paginas publicas e nos detalhes progressivos. Termos como hash, assinatura, chave e protocolo ficam recolhidos em detalhes tecnicos e recebem explicacao por analogia antes de serem exibidos.

Sem alongar a pagina, o bloco introdutorio deve resumir o metodo em tres sinais: impressao digital por hash para detectar mudanca de conteudo, assinatura criptografica para confirmar origem com chave privada protegida e encadeamento para evidenciar alteracao ou remocao na sequencia. No detalhe do mercado, o escudo sobre a thumbnail e o unico acionador de verificacao; nao deve haver botao textual redundante abaixo do titulo.

Depois de previsao inicial, reforco ou revisao, o detalhe do mercado confirma de forma compacta que foi emitido um comprovante assinado, explica que ele permite conferir a origem e detectar alteracoes e oferece acesso ao recibo individual em modal responsivo. A rota completa continua como fallback sem JavaScript. A interface usa os dados de `integrity_receipt` retornados pela FastAPI e nao simula assinatura no Django.

Cada acao da posicao mantem seu proprio comprovante: entrada inicial, cada reforco e cada revisao aparecem separadamente no historico de comprovantes do detalhe, identificados por tipo e sequencia. Uma acao nova referencia a anterior quando aplicavel; nenhuma assinatura anterior e substituida ou apagada.

Os comprovantes permanecem acessiveis ao titular em todos os estados posteriores a publicacao, inclusive `locked`, `resolved`, `sealed` e `canceled`. O fechamento do mercado remove apenas as acoes de previsao; nunca oculta a trilha criptografica ja emitida. Em `sealed`, o mesmo comprovante passa a incluir sua prova Merkle quando aplicavel.

No detalhe web autenticado, `Sua posicao` ocupa sempre o mesmo nivel da hierarquia: depois do estado ou resultado oficial e antes das acoes disponiveis. O mesmo componente apresenta opcao escolhida, total de GT₵, quantidade de entradas, situacao pessoal e comprovantes da previsao inicial, reforcos e revisoes em `open`, `locked`, `resolved`, `sealed` e `canceled`. Confirmacoes de nova previsao, reforco ou revisao aparecem dentro desse componente; acerto ou erro do usuario nao deve ser misturado ao bloco de resultado oficial do mercado.

Nos cards, mercados `resolved` e `sealed` usam o CTA curto `Resultado`. A acao secundaria de compartilhamento e um botao iconizado neutro, com nome acessivel e tooltip `Compartilhar mercado`, preservando o estilo editorial e sem competir com o CTA principal.

A linguagem visual segue esta semantica: verde somente para verificacao executada e aprovada; azul para processo ativo; amarelo para prazo ou retry operacional; cinza para aguardando, nao aplicavel ou ausencia historica; vermelho somente para diferenca criptografica detectada. Em `open`, previsoes aparecem como comprovantes sendo registrados, nao como etapa concluida. Em `locked`, aparecem como registros encerrados. Em `resolved`, resultado registrado e finalizacao pendente ficam distintos. Em `canceled`, resultado e finalizacao sao `Nao se aplica`.

No Admin Ops, a acao `Auditar integridade` deve estar disponivel para qualquer mercado, inclusive `draft`, `scheduled`, `open`, `locked`, `resolved`, `sealed` e `canceled`, tanto no browse geral quanto na fila de resolucao quando o mercado estiver presente nela. A tela operacional executa a verificacao autoritativa ao abrir por contrato staff read-only, sem depender do rate limit publico, e separa cada controle em `Aprovado`, `Diferenca detectada`, `Aguardando etapa` ou `Sem prova historica`: assinatura e correspondencia da definicao, compromissos de previsao, resultado, Seal, Merkle, eventos do mercado e cadeia global. Etapa futura ou nao aplicavel nunca aparece como falha. A auditoria de integridade e distinta da auditoria da resolucao, que continua dedicada aos efeitos de participantes, wallet e badges.

## Configuracao e operacao

- `market_seal_window_hours`: default 12, faixa 1..168, alteracao auditada no Admin Ops
- producao exige `GOTRENDLABS_INTEGRITY_KMS_KEY_ID` e `GOTRENDLABS_USER_COMMITMENT_SECRET`
- permissao `kms:Sign` fica limitada ao runtime/adaptador de integridade; verificacao usa chave publica em cache
- timeouts/retries KMS sao limitados e auditados sem payload sensivel
- dashboard mostra resolvidos aguardando, proximos do prazo, falhas e selados
- no inicio de todo ciclo, antes de fechamento, selagem, comunicacoes ou outras rotinas, o daemon executa auditoria criptografica somente leitura sobre todos os mercados e a cadeia global, independentemente do estado, da existencia de definicao ou de selagem pendente; ausencia de definicao e esperada apenas em `draft`/`scheduled`
- a deteccao operacional acontece na primeira passagem do daemon posterior a divergencia; a interface e a documentacao devem comunicar a cadencia real do ambiente, sem prometer deteccao instantanea
- diferencas de definicao, resultado, compromisso, Merkle, Seal ou elo do ledger criam alerta operacional `high` em fila propria; indisponibilidade de KMS/transporte e retry de selagem nao sao classificados como adulteracao
- alertas sao deduplicados por escopo e tipo de falha, preservam primeira/ultima deteccao e contagem de ocorrencias; revisao administrativa nao altera a prova e o alerta volta a `pending` se a divergencia persistir no ciclo seguinte
- auditoria incremental abre cada ciclo; auditoria integral ocorre no bootstrap, no maximo a cada 24 horas e imediatamente antes de cada Seal, sem depender de requisicao publica
- divergencia global identica no mesmo head nao cria novo checkpoint nem chama KMS em todo ciclo; o daemon reapresenta o alerta deduplicado e repete a auditoria integral depois de uma hora, quando o head mudar ou por solicitacao explicita
- enquanto a auditoria global estiver em `failed`, o ciclo suprime todas as tentativas de Seal antes de iterar mercados vencidos, evitando que cada candidato contorne o backoff; fechamento, retenção e comunicações continuam isolados
- a interface informa sequencia verificada, sequencia atual, eventos pendentes e horario/tipo da ultima auditoria sem prometer atualizacao instantanea

### Evolucoes operacionais pos-rollout

- separar ownership/migrations das roles de aplicacao e remover de todos os runtimes `UPDATE`, `DELETE` e `TRUNCATE` sobre tabelas append-only, mantendo triggers uniformes como defesa adicional
- substituir o isolamento apenas por configuracao do processo por identidade IAM propria do signer/FastAPI/daemon quando os workloads forem separados; o host compartilhado permanece limitacao conhecida do MVP
- antes da primeira rotacao de `GOTRENDLABS_USER_COMMITMENT_SECRET`, versionar o segredo no protocolo e manter keyring historico somente no Secrets Manager
- ligar alarmes de KMS, daemon, memoria, swap, disco e banco a um destino operacional testado e validar dimensoes reais das metricas; `INSUFFICIENT_DATA` critico deve gerar diagnostico
- executar ensaio de carga representativo da verificacao publica e observar ao menos 24 horas de checkpoints/auditorias automaticas antes do lancamento irrestrito

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
- comprovantes continuam visiveis em `locked`, `resolved`, `sealed` e `canceled`
- toda previsao persistida, humana ou de agente IA, possui exatamente um compromisso; ausencia, duplicidade ou compromisso divergente invalida a auditoria e impede a selagem
- renomear categoria, subcategoria ou evento preserva a prova; trocar a associacao taxonomica protegida do mercado invalida a definicao
- falha ou timeout da auditoria gera indisponibilidade observavel sem impedir fechamento, comunicacoes ou a continuidade do processo daemon
- comando de limpeza inicia em `dry-run`, recusa mercados com prova assinada e pode ser reexecutado sem duplicar efeitos
- auditoria do daemon detecta cada classe de adulteracao, cria alerta `high`, nao duplica o mesmo problema por ciclo e nao classifica retry operacional como adulteracao
- Admin Ops permite auditar integridade em qualquer estado, identifica o controle que falhou e distingue falha, etapa futura e ausencia historica
- mercado com qualquer verificacao aplicavel invalida, inclusive cadeia global, nunca transita para `sealed`
- alterar metadado persistido do evento que nao esteja no snapshot de negocio tambem invalida a cadeia
- cards web/mobile nunca exibem sinal positivo quando existe alerta de integridade pendente para o mercado
- limpeza pre-producao preserva concessoes/notificacoes de badge sem causalidade comprovada com os mercados removidos
- checkpoint adulterado, ausente, regressivo ou desconectado nunca produz estado verificado
- endpoint publico nao executa consulta que percorra todos os eventos globais
- auditoria incremental valida somente o delta e auditoria integral periodica chega ao mesmo resultado
- selagem executa auditoria global integral fresca e detecta adulteracao anterior ao ultimo checkpoint
- prova publica agrega compromissos e nunca retorna evento, ID, referencia ou timestamp individual de previsao
- alterar metadados persistidos de definicao, compromisso, Seal ou folha Merkle invalida a verificacao
- divergencia global identica no mesmo head respeita backoff e nao cria checkpoint/KMS a cada ciclo

## Privacidade e retenção

- `user_commitment` é HMAC-SHA-256 com segredo do servidor e não permite ao público correlacionar diretamente o usuário interno.
- Nome, email, IP, token e identificador bruto não entram em payload público. O compromisso e as provas podem ser retidos quando necessários à auditoria e integridade histórica.
- Exclusão lógica ou retificação de perfil não apaga provas append-only; o atendimento de direitos preserva a separação entre PII operacional e compromisso pseudonimizado.

## Rollout e reversao

1. Inventariar e criar snapshot validado do banco de produção pré-lançamento; remover todos os mercados atuais sem definição assinada, sem migração retroativa ou modo legado.
2. Aplicar schema e triggers.
3. Criar chave KMS/alias e politica IAM minima; configurar segredo de commitment no secret manager/runtime.
4. Publicar FastAPI/daemon antes de habilitar novos mercados.
5. Validar chave publica e teste de assinatura.
6. Liberar web/mobile alinhados ao contrato final; nao ha compatibilidade obrigatoria com builds pre-producao anteriores.

Rollback desabilita novas publicacoes/previsoes se o signer estiver indisponivel, preserva tabelas/provas e retorna daemon para retry. Nunca remover nem reescrever eventos existentes.
