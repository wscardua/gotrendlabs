# Orientações para agentes

## Impacto no MCP

Em toda mudança de funcionalidade, regra de domínio, API, autenticação, persistência ou documentação editorial, analisar explicitamente se o MCP precisa de ajustes. Verificar ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial exposta, conforme o escopo. Implementar e testar os ajustes necessários; quando não houver ajuste, registrar a conclusão e o motivo no workflow ou no resumo da entrega. Não inferir novas permissões MCP a partir de ações humanas do Admin Ops.

## Compatibilidade e legado

Por orientação do usuário, o sistema ainda está em desenvolvimento e não exige compatibilidade com legado. Preferir contratos atuais explícitos e atualizar seus consumidores diretamente; não criar campos opcionais, fallbacks ou caminhos de compatibilidade apenas para atender clientes ou formatos antigos. Preservar integridade dos dados, segurança e regras de domínio. Continuar analisando o impacto no MCP em cada mudança.
