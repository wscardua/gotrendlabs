# Release Google Play 1.2.3+17 — 06/11/2026

## Preparação

Solicitação do usuário: compilar e enviar uma nova release à Google Play Console já aberta/logada. Canal existente confirmado na UI: Closed testing - Alpha; versão ativa 1.2.2+16. Próxima versão/build: 1.2.3+17. Nenhum rollout público de produção faz parte desta entrega.

Código-base: origin/main 30c6bec antes da preparação. A versão/build deve ser integrada antes de compilar; o SHA efetivo, checksum e tamanho serão registrados após o build limpo. URLs de compilação: `GTL_API_BASE_URL=https://gotrendlabs.com.br/api`, `GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br`. Assinatura e Firebase da release16 reutilizados via arquivos locais ignorados, sem expor segredos.

Validação local: flutter analyze --no-pub limpo; flutter test --no-pub com 129 testes aprovados. Contém MFA da PR #191 e preserva resiliência da #188. ResolutionCriteriaText e seus quatro testes foram comparados byte a byte com o worktree mobile-login-fix: idênticos e já integrados desde caee7aa (17/10); a pendência anterior de ausência desse componente foi corrigida, sem alteração de UI.

## Notas de versão pt-BR

Corrigimos o acesso de contas administrativas com verificação em duas etapas. Agora é possível confirmar o login pelo autenticador ou por código de recuperação. Mantivemos as melhorias de estabilidade e a leitura completa dos critérios de resolução.

## Resultado

Integração, build assinado, validação de metadados e upload ainda pendentes na preparação deste documento. Publicação no canal e revisão da Google são estados distintos; registrar o estado observado após envio, sem afirmar disponibilidade antecipada.

MCP sem ajustes: ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial preservados. Sem mudança de API/backend/web nem política mínima de build. Smoke com conta administrativa real no artefato novo só será declarado se executado.
