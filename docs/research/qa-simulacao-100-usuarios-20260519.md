# Relatorio de QA - Simulacao com 100 usuarios

Data da rodada: 2026-05-19  
Ambiente: `http://127.0.0.1:8000/` + `http://127.0.0.1:8001`  
Run principal: `qa_20260519_seededops`  
Coordenacao: consolidacao automatizada a partir de 100 personas sinteticas

## Resumo executivo

A plataforma suportou uma rodada operacional com 100 usuarios sinteticos realizando login, navegacao, leitura de perfil/wallet/ledger/badges, previsao, comentarios, sugestoes, feedbacks e operacoes administrativas. Nao houve erro bloqueante nos fluxos autenticados depois que os usuarios foram semeados diretamente no banco local.

Dois achados importantes apareceram antes da rodada principal:

- emails com dominio reservado `.test` foram recusados pelo validador de email da API;
- cadastro automatizado via API foi bloqueado por reCAPTCHA ativo, com mensagem `Confirme que voce nao e um robo.`

Por isso, a rodada principal criou usuarios sinteticos diretamente no banco local e operou login/fluxos reais pela API/web. Nenhuma correcao foi aplicada.

## Cobertura executada

- Usuarios sinteticos criados: 100
- Logins via API: 100
- Mercados existentes lidos: 13
- Mercados abertos usados para previsao: 9
- Previsoes criadas: 100
- Comentarios criados: 60
- Reacoes criadas: 20
- Sugestoes criadas: 35
- Feedbacks criados: 40
- Admin Ops:
  - listagem de mercados, filas, comentarios, badges e taxonomia
  - revisao de 6 sugestoes
  - revisao de 6 feedbacks
  - conversao de 1 sugestao em rascunho
  - recompensa de 3 feedbacks
  - recompensa de 3 sugestoes

Paginas web amostradas responderam `200`: home, categorias, badges, ranking, conceitos, seguranca, sugestao, feedback, detalhes de mercados e telas de Admin Ops.

Metricas observadas:

- latencia media da rodada: 0.359s
- p95 observado: 2.182s
- erros de execucao na rodada principal: 0

## Achados principais

### 1. Cadastro automatizado/local de QA nao passa com reCAPTCHA ativo

Impacto: medio para QA e automacao; esperado em producao, mas atrapalha simulacoes locais e testes E2E autenticados.

Evidencia:

- `POST /auth/register` retornou `422`
- mensagem: `Confirme que voce nao e um robo.`
- afetou 100 tentativas com dominio valido `qa-gotrendlabs.dev`

Recomendacao:

- Criar um modo explicitamente controlado de teste local para seed de usuarios ou bypass de reCAPTCHA apenas em ambiente de desenvolvimento/teste.
- Alternativa segura: comando de management `seed_qa_users` com prefixo e limpeza por `run_id`, sem alterar contrato publico de cadastro.

### 2. Dominio `.test` e recusado pelo validador de email

Impacto: baixo/medio; `.test` e comum em fixtures, mas o validador Pydantic/EmailStr rejeita dominios reservados.

Evidencia:

- `qa_20260519_realops_001@gotrendlabs.com.br` retornou erro de validacao.
- Mensagem tecnica exposta: `The part after the @-sign is a special-use or reserved name...`

Recomendacao:

- Usar dominios de QA nao reservados nas fixtures (`qa-gotrendlabs.dev`, por exemplo), ou padronizar gerador local.
- Melhorar a mensagem de erro exibida para usuario final, evitando texto tecnico em ingles.

### 3. Conceito GTL/probabilidade/retorno ainda gera ambiguidade

Impacto: medio para onboarding e confianca.

Padrao das personas:

- 62 personas apontaram que o fluxo funciona, mas precisa reduzir ambiguidade entre GTL Credits, probabilidade e retorno.
- 25 personas, especialmente novatos e usuarios apressados, pediram mais orientacao antes de prever.

Recomendacao:

- Adicionar microcopy perto da acao de previsao explicando:
  - GTL nao e dinheiro real;
  - probabilidade e consenso atual;
  - retorno estimado e informativo ate a resolucao;
  - stake fica bloqueado no ledger.

### 4. Fonte e criterio de resolucao precisam de destaque maior

Impacto: medio para usuarios ceticos e confianca operacional.

Padrao das personas:

- 13 personas do perfil "analista cetico" pediram fonte/evidencia e criterio de resolucao mais destacados antes da previsao.

Recomendacao:

- Aproximar fonte e criterio de resolucao do bloco de confirmacao de previsao.
- Considerar um resumo compacto no ticket de previsao: fonte esperada, criterio e data/zone de fechamento.

### 5. Comentarios funcionam, mas pedem ferramentas de leitura

Impacto: baixo/medio.

Evidencia:

- 60 comentarios criados com sucesso.
- 20 reacoes criadas com sucesso.
- Personas citaram ordenacao/legibilidade como melhoria.

Recomendacao:

- Planejar ordenacao ou filtros simples em comentarios: recentes, mais curtidos, ocultar negativos.
- Avaliar paginacao quando volume crescer.

## Observacoes por area

### Autenticacao

Login via API funcionou para 100 usuarios semeados. Cadastro publico ficou bloqueado por reCAPTCHA, como esperado quando a protecao esta ativa, mas isso pede caminho de seed para QA local.

### Feed e mercado

Paginas de feed/detalhe responderam `200`. A confirmacao de previsao criou registros em 9 mercados abertos sem erros bloqueantes.

### Wallet e ledger

Cada usuario autenticado consultou wallet e ledger com status `200`. Previsoes bloquearam stake e recompensas administrativas foram aplicadas a itens selecionados.

### Ranking e badges

Ranking e badges responderam `200` para 100 usuarios. Nao houve erro de contrato durante leitura.

### Sugestoes e feedback

Sugestoes e feedbacks autenticados funcionaram. Admin Ops conseguiu revisar, converter e recompensar itens selecionados.

### Admin Ops

Contratos administrativos responderam `200` com usuario staff sintetico. A rodada confirmou listagem de mercados, filas, comentarios, badges e taxonomia, alem de acoes de revisao, conversao e recompensa.

## Dados criados

Prefixos usados:

- usuarios comuns: `qa_20260519_seededops-001@qa-gotrendlabs.dev` ate `qa_20260519_seededops-100@qa-gotrendlabs.dev`
- staff sintetico: `qa_20260519_seededops-staff@qa-gotrendlabs.dev`
- sugestoes/feedbacks: textos contendo `QA qa_20260519_seededops`

Esses dados ficaram no banco local para auditoria da rodada. Para remover depois, recomenda-se uma limpeza por prefixo/run_id em usuarios, sessoes, sugestoes, feedbacks, comentarios, previsoes e entradas de ledger relacionadas.

## Recomendacoes priorizadas

1. Criar mecanismo controlado de seed/cleanup de QA para ambientes locais.
2. Melhorar mensagem de erro de email invalido para dominios reservados.
3. Reforcar microcopy de previsao: GTL, probabilidade, retorno e stake bloqueado.
4. Levar fonte/criterio de resolucao para mais perto da acao de prever.
5. Adicionar ferramentas basicas de leitura em comentarios.
6. Criar checklist visual/E2E com navegador para validar estados autenticados renderizados, alem dos contratos API.

## Proximos passos sugeridos

Nenhuma correcao foi aplicada. Antes de implementar, decidir:

- se os dados da rodada devem ser preservados ou limpos;
- se o seed de QA deve virar comando oficial de desenvolvimento;
- quais melhorias entram na proxima branch: cadastro/QA, microcopy de previsao ou comentarios.
