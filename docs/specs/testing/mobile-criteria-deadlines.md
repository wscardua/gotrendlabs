# Mobile — critério expansível e fechamento explícito

WFLOW-20261017-MOBILE-CRITERIA-DEADLINES, 17/10/2026. Correção da investigação: além da implementação web (bf81c0f/PR160), existia implementação Flutter aprovada em 12/10, não commitada, no checkout gotrendlabs-mobile-login-fix (ResolutionCriteriaText). A primeira investigação omitiu esse checkout. A versão de quatro linhas expansível registrada abaixo foi substituída pela restauração do componente aprovado.

## Alteração

`ResolutionCriteriaPreview` mede o texto na largura/escala/locale reais; quatro linhas recolhidas, botão somente quando excede a altura, expansão integral sem reescrita e sem perda de parágrafos. “Ver critério completo / Recolher critério” informa estado expanded em Semantics. Troca do texto/mercado reinicia a prévia. Critério continua antes do ticket e integridade por último.

Detalhe exibe `close_label` da API junto de `expected_resolution_label`, sem tratar fechamento como apuração, sem relógio ou cálculo crítico no cliente e sem fabricar data ausente. Rótulos de fechamento e previsão permanecem distintos. MCP analisado: sem ajustes, pois payloads, ferramentas, permissões, erros, replay e política não mudam; só estado visual e consumo de campos já existentes.

## Verificações

- `flutter analyze`: nenhum problema (3.7s).
- `flutter test`: 118 aprovados; novos cenários para texto longo expandir/recolher intacto, prévia a 1×/2× e texto curto sem botão com prazos distintos.
- APK debug local separado compilado (9s), mantendo Firebase opcional desativado na entrada de QA. O Gradle versionado e o package principal não foram alterados.
- Atualização do pacote QA físico via install -r concluída (Success), sem apagar dados. A tela entrou em Dozing e bloqueou; o usuário a desbloqueou. Conferência visual então concluída no Samsung SM-G980F, mercado FURIA local: fechamento 18/10/2026 12:00 BRT, resolução prevista 20/10/2026 18:03 BRT e prévia de quatro linhas com botão visíveis. Detalhe aberto pela busca normal do app; deixado na prévia para o usuário. Não foram feitas previsões/login ou mudanças no critério. Expansão/recolhimento completos foram testados nos widgets; a inspeção física confirmou a prévia/controle/datas. Evidência privada em `.runtime/mobile-physical/criteria-preview.png`.

A tentativa inicial de teste de tela inteira em fonte 2× revelou overflow em HeroMeta/CompactMetricTile existentes; o teste de fonte ampliada foi isolado no componente do critério para verificar esta alteração sem misturar as limitações desses outros componentes. Testes da tela inteira em escala normal preservam a integração. Lacuna documentada em known-gaps; não se afirma QA completo do app com fonte 2×. A primeira tentativa de interação também precisou aguardar o relayout após ensureVisible antes de tocar o controle; teste corrigido, sem suprimir exceções.

Sem produção, merge, deploy, operações financeiras, previsões reais ou alterações de critérios cadastrados.

## Restauração da apresentação aprovada — 17/10/2026

Reutilizados sem alterações ResolutionCriteriaText e seus quatro testes do checkout mobile-login-fix, sem importar mudanças de autenticação. Prévia de três linhas, texto integral selecionável em painel inferior com rolagem e Fechar. Fechamento e resolução prevista preservados. Sem mudanças de contrato/API/MCP; nenhuma nova permissão. Evidências finais no workflow WFLOW-20261017-RESTORE-MOBILE-CRITERIA.

## Posição dos prazos — 17/10/2026

WFLOW-20261017-MOBILE-DEADLINE-PLACEMENT: fechamento/previsão movidos ao rodapé do resumo, após divisor e com bodySmall secundário. Critério mantém o componente restaurado. Analyze limpo, 120 testes aprovados, build/install .local Success. Inspeção física Samsung na escala atual sem overflow do bloco; captura .runtime/mobile-physical/placement-summary.png. Sem novo QA visual em escala ampliada; sem API/MCP alterados.
