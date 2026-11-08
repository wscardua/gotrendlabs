---
id: FEAT-ADSENSE-001
titulo: "Verificação do site no Google AdSense"
versao: 1.0
status_spec: aprovada
status_impl: implementada_validada_localmente
ultima_atualizacao: 2026-11-08
origem:
  - solicitação do proprietário em 2026-11-08
contratos_afetados: []
dependencias: []
impacta:
  - frontend-web
---

# Verificação AdSense sem anúncios

GET `/ads.txt` é público em todos os ambientes, retorna 200, Content-Type `text/plain` e exatamente `google.com, pub-4771800155732970, DIRECT, f08c47fec0942fa0` com LF final. HEAD retorna os mesmos metadados sem corpo. Não depende de sessão/banco/API e permanece acessível durante manutenção por exceção de caminho exato.

O head de `base.html` recebe uma única meta `google-adsense-account` com `ca-pub-4771800155732970` quando `settings.PRODUCTION_MODE` é verdadeiro. O modo existente usa GOTRENDLABS_ENV=prod/production ou DJANGO_DEBUG=0; DEV/testes comuns não recebem identificação. O publisher ID é público e versionado. Não há configuração secreta ou infraestrutura nova.

A [documentação de conexão](https://support.google.com/adsense/answer/7584263?hl=en), consultada em 2026-11-08, aceita meta tag como método de verificação antes de Request review. O [guia ads.txt](https://support.google.com/adsense/answer/12171612?hl=en) orienta publicação na raiz e conferência pública. O script fornecido pelo proprietário (`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4771800155732970`, async/crossorigin=anonymous) fica reservado para integração futura; não é carregado nesta etapa.

Fora do escopo: Auto ads, unidades/espaços, simulações, mudanças de layout/CSP/consentimento, deploy, push e operações no painel Google. GTL Credits continuam educativos, sem dinheiro real. Preparação técnica não comprova aprovação editorial ou aprovação pelo Google.

Arquitetura: entrega Django pelo proxy Caddy existente; contexto de identificação sem I/O; nenhuma regra crítica sai da FastAPI. Não exige ADR, migration ou mudança OpenAPI/MCP. Ferramentas, schemas, contratos, autenticação, permissões, erros, replays e orientação editorial MCP permanecem iguais.

## Aceite

- Cliente anônimo recebe status/tipo/corpo exatos em GET e HEAD sem corpo, inclusive em manutenção.
- Home e páginas públicas renderizam meta única dentro do head em produção e nenhuma em DEV; não contêm script AdSense, unidades ou slots.
- Rotas existentes e manutenção da home preservadas.
- Testes locais usam o virtualenv existente e não escrevem em produção.
- Após aprovação da entrega: publicar, conferir HTTPS /ads.txt e meta no HTML, verificar conexão no painel e solicitar revisão. Nenhuma dessas ações faz parte da implementação local.
