# Imagens de badges — rollout de 2026-10-09

Fonte atual: WFLOW-20261009-BADGE-CLOSE-001. Fechamento técnico, integração e habilitação produtiva concluídos; homologação humana/MFA e qualidade real do par permanecem pendentes.

## GitHub e testes

- [PR #144](https://github.com/wscardua/gotrendlabs/pull/144), descrição aprovada pelo usuário antes da submissão; merge `edac7c791d5591676bd4e02bc5b48ccec94e7cbc`.
- Local: 442 testes aprovados/776.623s, PostgreSQL isolado e provedor simulado; browsers de badges/mercados e checks aprovados.
- [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/37976222496): Success, build completo aprovado, 442 testes/404.860s, OK (skipped=1).
- [CI e deploy de main](https://github.com/wscardua/gotrendlabs/actions/runs/37977374007): Success, build completo aprovado, 442 testes/435.034s, OK (skipped=1), deploy aprovado.
- O skip corresponde às roles dedicadas ausentes no CI; o cenário passou no banco local com essas roles. Não confundir 442 descobertos com 442 executados sem skip no CI.

## Produção

SSM `0ef915d1-86a7-4d68-b7be-0490f7ab6478`: Success; migration `admin_ops.0025_badge_image_jobs` aplicada, fronteiras DB conferidas, serviços e executor atualizados. RDS tinha recuperação anterior ao rollout em 2026-10-09T18:51:40Z, retenção automática de um dia.

SSM `557fda54-8b9b-44f7-93c3-e454578fa1bd`: Success. Grants da role FastAPI para flag/fila, defaults SQL e constraints conferidos. API monta `badge_images` RW e privado RO; worker monta privado e públicos RW; proxy não monta privado, daemon permanece sem mídia. Probes próprios efêmeros de escrita foram removidos. Worker usa `badge-image-bedrock-pair-v2`, tem credencial configurada, sem expô-la. Health 200; configurações, consulta e preview anônimos 401.

SSM `7706d120-db28-404d-80a2-6750e267deaf`: Success. Fila de badges sem trabalhos ativos antes da habilitação; `badge_image_enabled` false → true pelo serviço existente e evento `badge_image.settings_update`, ator de sistema, antes/depois auditados. Política de thumbnails integralmente preservada, `GTL_THUMB_ENABLED=1` mantido; nenhum provedor invocado.

SSM `97e83285-ffb1-434b-9e0d-aedb6daa45b2`: Success. Flags de badges e thumbnails true, executor observa habilitação persistida e fila continua vazia. A consulta complementar `e1252e51-d48a-4c7d-84a1-df1bc8aef7e7` falhou ao tentar ler manutenção como coluna de SiteConfig; a leitura corrigida usa a configuração canônica `platform_config`, sem alteração de schema/domínio.

Contagens antes/depois: 3 mercados, 8 definições de badges, 8 concessões. Nenhum registro real foi criado/editado pelo smoke. Mídia DEV, credenciais e logs não foram versionados. Branch local `feature/admin-ai-badges` preservada.

## Configuração e acesso

Stable Image Core `stability.stable-image-core-v1:1`, Bedrock Runtime/Oregon (`us-west-2`), badges 1:1 e mercados 3:2; timeout 180s por chamada. Limites compartilhados: 10 imagens/operador e 50 globais por 24h, 5 solicitações/item; duas imagens reservadas por par. Retenção de candidatas 24h. Nenhum novo recurso AWS; agentes textuais preservados.

Site público responde 200 na tela de manutenção; manutenção ativa foi preservada. Admin Ops e novos endpoints web exigem login. JS atualizado foi conferido por HTTP; tentativa de acessar arquivo sob mídia privada retorna 404, sem mount privado no proxy.

## Pendências reais

Operador com MFA homologa criação/edição, regeneração e salvamento do par em produção. Inferência paga de homologação exige autorização específica; o rollout não fez chamadas pagas. Credencial presente e mocks não comprovam acesso efetivo da conta ao modelo nem qualidade/coerência das duas variantes. Não declarar inferência produtiva ou aumento de engajamento validados. Pausa funcional: desligar apenas a flag de badges, preservando thumbnails, schema e arquivos.
