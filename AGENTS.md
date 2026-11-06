# Orientações para agentes

## Impacto no MCP

Em toda mudança de funcionalidade, regra de domínio, API, autenticação, persistência ou documentação editorial, analisar explicitamente se o MCP precisa de ajustes. Verificar ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial exposta, conforme o escopo. Implementar e testar os ajustes necessários; quando não houver ajuste, registrar a conclusão e o motivo no workflow ou no resumo da entrega. Não inferir novas permissões MCP a partir de ações humanas do Admin Ops.

## Compatibilidade e legado

Por orientação do usuário, o sistema ainda está em desenvolvimento e não exige compatibilidade com legado. Preferir contratos atuais explícitos e atualizar seus consumidores diretamente; não criar campos opcionais, fallbacks ou caminhos de compatibilidade apenas para atender clientes ou formatos antigos. Preservar integridade dos dados, segurança e regras de domínio. Continuar analisando o impacto no MCP em cada mudança.

## Integridade de entregas e releases

- Distinguir explicitamente os estados implementado/testado localmente, commitado, integrado à main e distribuído. Um build instalado ou enviado à loja não comprova integração do código.
- Toda implementação/correção deve ser commitada na branch de trabalho antes da entrega; alterações de outras tarefas devem ser preservadas e identificadas, nunca incluídas incidentalmente. Não declarar entrega integrada/concluída em produção com código apenas em worktree local.
- Artefatos destinados à distribuição devem partir de checkout limpo do commit atual da main remota, após fetch, com versão/build e configuração registrados. Antes do build, integrar e validar as alterações da release na main. Para validar mudanças ainda não integradas, usar builds de debug.
- Antes de substituir uma versão distribuída, comparar seu recibo, funcionalidades e origem com a nova base e verificar worktrees/branches com correções pendentes. Diferenças sem reconciliação impedem liberar a nova versão. Não presumir que estar na main garante conter tudo que foi distribuído anteriormente.
- Registrar por artefato: commit de origem, versão/build, canal, checksum, validações e pendências. Publicação requer conferir que o artefato selecionado corresponde a esse recibo.
- Manter testes de regressão dos fluxos corrigidos. No Android, o gate de origem do release bloqueia checkout sujo, branch não integrada e falha ao atualizar a referência remota.
