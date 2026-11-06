# Integração remota — MFA mobile e origem de releases

Integração solicitada pelo usuário em 06/11/2026. Este recibo atesta código integrado à main remota; publicação de app e conclusão de deploy produtivo são estados separados. O acompanhamento pós-merge foi concluído conforme evidências abaixo.

- PR: [#191](https://github.com/wscardua/gotrendlabs/pull/191).
- Merge remoto: `ed018f837c13d35a3a77e9741f5490abe1c28703`.
- Implementações: `06f7c6e` (MFA) e `05f8053` (gate/governança de release).
- Confirmação: fetch origin main seguido de merge-base confirmou ambos os commits como ancestrais de origin/main.
- [CI do PR](https://github.com/wscardua/gotrendlabs/actions/runs/42238971291): aprovado; 681 testes em 386,220 s, 3 skips; builds Docker, snapshot OpenAPI e testes JS aprovados.
- Validação local: 129 testes Flutter, análise estática limpa, APK debug compilado, sete testes Python do gate e integração Gradle verificada. Ambiente virtual existente reutilizado.
- [Pipeline pós-merge](https://github.com/wscardua/gotrendlabs/actions/runs/42240420306): concluído com sucesso; 681 testes em 449,559 s, 3 skips, builds/contratos/JS aprovados e deploy via SSM com status Success.
- [Execução documental #192](https://github.com/wscardua/gotrendlabs/actions/runs/42240762634): concluída com sucesso; deploy corretamente ignorado por docs-only.
- Smoke pós-deploy: `GET https://gotrendlabs.com.br/api/health` respondeu HTTP 200, `status=ok`, `checks.api=ok` e `checks.database=ok`. Isso não equivale a homologação do login no APK distribuído.
- Gate de origem testado também contra checkout temporário limpo da main remota `ade0032119ec8bb7e5d9d42bcf0ddd48c8a35bd0`: aceito após fetch. Checkout temporário removido; worktree original preservado.

## Comportamento integrado

Login administrativo mobile reconhece desafio MFA, oferece enrollment por chave manual, TOTP/recuperação e exibição dos recovery codes. Só ativa sessão após verificação; cancelamento descarta desafio/resposta pendente. FastAPI segue autoritativa, sem novo contrato ou regra de domínio.

Release Android exige fetch, checkout limpo e HEAD igual à main remota atualizada. Debug permanece disponível. AGENTS e checklist exigem comparar a versão anterior e registrar SHA, versão/build, checksum, canal e regressões. O gate não substitui a reconciliação funcional de releases anteriores.

## Pendências preservadas

Não houve upload/publicação de novo APK/AAB. Antes da próxima distribuição: reconciliar o critério compacto de resolução preservado no worktree gotrendlabs-mobile-login-fix, integrar essa alteração, preparar versão/build e validar login administrativo com conta real no artefato novo. O código anterior permanece preservado. Nenhuma credencial/TOTP foi solicitada ou registrada.

MCP sem ajustes necessários em ferramentas, schemas, contratos, permissões, erros, replays ou orientação editorial. Nenhuma permissão inferida de ações humanas de Admin Ops.

## Reconciliação corrigida antes da release 17

Em 06/11, a comparação byte a byte mostrou que ResolutionCriteriaText e seus quatro testes do worktree anterior já estavam na main desde caee7aa (17/10). Portanto, a pendência de critério registrada acima estava incorreta e foi resolvida por evidência, sem mudar a UI. MFA integrado pela #191 é o ajuste a empacotar na 1.2.3+17.
