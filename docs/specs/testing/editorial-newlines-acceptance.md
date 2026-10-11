# Aceite: quebras de linha no parecer editorial

Nota posterior: a mudança de responsabilidade humana de 2026-10-11 substitui gates de conteúdo na aprovação/publicação. A equivalência de quebras continua aplicável aos validadores e alertas de preparação. Consulte [aceite vigente](human-editorial-attestation-acceptance.md).

2026-10-11, FEAT-EDITORIAL-001. Produção mercado 44 consultado somente por MCP: linha única válida `Anúncio esperado: não informado`. Validador anterior rejeitava a mesma linha com CRLF; Chrome headless confirmou que textarea com LF é enviada como CRLF em formulário POST.

- LF/CRLF/CR devem aceitar não informado, ISO com offset e Z; declaração válida de ausência de pendências deve ter comportamento equivalente.
- Data sem offset, texto inválido, anúncio duplicado, fechamento igual/posterior ao anúncio e pendências ausentes/duplicadas continuam rejeitados.
- Parecer humano com CRLF deve salvar/aprovar em banco isolado, preservando exatamente o documento enviado. Nenhuma aprovação de produção efetuada.

Evidência: 11 testes/OK em 10.523s (unitários e API/DB isolado test_gtl_mcp_delete_fixes), Chrome headless POST/CRLF aprovado. OpenAPI --check, compilação, diff --check aprovados; DEV API/web HTTP200 com reload automático. Sem migration, mudança de payload MCP, alteração de dados produtivos ou deploy. Publicação e homologação autenticada produtiva ainda pendentes.
