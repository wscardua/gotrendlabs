# Especificação de Produto — MVP de Rede Social de Prediction Markets

## Status do Documento

- Versão: `0.3`
- Status: `draft para refinamento`
- Idioma: `pt-BR`
- Objetivo desta versão: alinhar visão de produto, escopo do MVP e regras centrais do sistema

---

## Resumo Executivo

O produto é uma aplicação web social onde usuários fazem previsões sobre eventos futuros usando uma moeda interna da plataforma. Nesta spec, a moeda interna adotada para o MVP será `Orynth Coins`. A experiência combina:

- feed de mercados;
- tomada de posição em mercados binários e de múltipla escolha;
- reputação baseada em desempenho;
- ranking social;
- percepção de "inteligência coletiva" a partir das probabilidades agregadas.

O MVP existe para validar se pessoas voltam com frequência para prever, acompanhar resultados e comparar desempenho com outros usuários.

O MVP não deve ser percebido como casa de apostas, cassino ou plataforma financeira. Nesta fase não haverá dinheiro real, blockchain, wallet on-chain nem negociação financeira entre usuários.

---

## Problema que o Produto Resolve

Hoje existem bons formatos para discutir o futuro, mas poucos unem:

- opinião estruturada;
- incentivo para responder com convicção;
- reputação acumulada ao longo do tempo;
- leitura coletiva de probabilidade;
- camada social simples e fácil de consumir.

O produto quer transformar previsões em uma atividade recorrente e comparável, gerando valor para o usuário em três frentes:

- entretenimento intelectual;
- sinal reputacional;
- descoberta do consenso coletivo sobre temas de interesse.

---

## Hipóteses do MVP

O MVP deve responder principalmente estas perguntas:

1. Usuários retornam para acompanhar mercados abertos e resolvidos?
2. O ranking e a reputação aumentam engajamento e retenção?
3. A interface de previsão com poucas opções e `stake` é simples o suficiente para gerar volume de previsões?
4. A probabilidade coletiva produz sinal útil ou ao menos interessante para o usuário?
5. Categorias temáticas ajudam a formar hábitos e recorrência?

---

## Objetivos do MVP

- validar retenção inicial;
- testar dinâmica social das previsões;
- medir adoção do sistema de moeda interna e reputação;
- avaliar se a probabilidade agregada é compreensível;
- nascer preparado para operação multilíngue;
- estabelecer base de confiança, segurança e auditabilidade para a plataforma;
- criar base de produto e dados para uma versão futura mais sofisticada.

## Não Objetivos do MVP

- operar com dinheiro real;
- oferecer liquidez financeira real;
- simular bolsa, exchange ou cassino;
- suportar criação aberta de mercados por qualquer usuário;
- otimizar trading em tempo real;
- construir app mobile nativo nesta fase.

---

## Posicionamento do Produto

O produto deve ser apresentado como:

- rede social de previsões;
- plataforma de inteligência coletiva;
- sistema reputacional sobre eventos futuros.

O produto não deve ser apresentado como:

- cassino;
- plataforma de apostas em dinheiro;
- exchange financeira;
- instrumento de investimento.

---

## Diretrizes de Linguagem Pública

A experiência voltada ao usuário final deve priorizar tom social, claro e confiável. A copy pública deve reforçar:

- consenso público;
- previsão ou posição própria antes do consenso mudar;
- reputação construída por histórico resolvido;
- badges como sinal público de presença, acertos, ranking e contribuição;
- O₵ como crédito educativo interno;
- resolução auditável com fonte verificável.

Na camada pública, termos com forte associação financeira ou de trading devem ser evitados quando houver equivalente mais claro:

- usar `O₵ reservadas`, `crédito reservado` ou `crédito educativo` em vez de `stake`;
- usar `crédito possível se acertar` em vez de `retorno estimado` ou `payout`;
- usar `carteira educativa` em vez de `wallet`;
- usar `prever`, `registrar previsão` ou `registrar posição` em vez de chamadas com tom de aposta;
- usar `Em apuração` para mercados `locked`, evitando `fechado` na camada pública quando o mercado ainda aguarda resolução.

Identificadores técnicos, nomes de campos, eventos de domínio, contratos de API, ledger e documentação interna podem preservar termos como `stake`, `payout`, `wallet` e `refund` quando forem necessários para precisão técnica.

---

## Público Inicial

Segmentos mais promissores para o MVP:

- usuários interessados em tecnologia e IA;
- público que acompanha games e cultura pop;
- pessoas que consomem creators e tendências de internet;
- usuários com afinidade com competição, ranking e reputação.

Motivações esperadas:

- acertar antes dos outros;
- subir no ranking;
- mostrar visão de mercado;
- acompanhar debates coletivos sobre o futuro.

---

## Proposta de Valor

Para o usuário:

- prever eventos rapidamente;
- acompanhar o consenso do mercado;
- ganhar moeda interna e reputação;
- construir histórico público de acertos e convicção;
- confiar que mercados, resoluções e reputação são tratados com rigor e consistência.

Para o produto:

- gerar dados de previsão;
- medir qualidade de perguntas e categorias;
- testar loops sociais de retenção;
- construir reputação de plataforma confiável e segura.

---

## Internacionalização e Alcance Global

O produto deve nascer preparado para operação multilíngue, mesmo que a primeira operação pública seja focada em um idioma principal.

Diretrizes iniciais:

- toda interface textual deve ser compatível com sistema de tradução;
- textos fixos da aplicação não devem ficar hardcoded diretamente nas telas;
- o modelo deve considerar localidade e idioma preferencial do usuário;
- mercados podem exigir estratégia futura para conteúdo traduzido ou localizado;
- datas, números, moedas e formatos devem respeitar localidade;
- URLs, slugs e identificadores devem evitar depender exclusivamente de texto traduzido.

Idiomas iniciais suportados no lançamento:

- `pt-BR` como idioma base de definição atual;
- `en` como primeiro idioma adicional prioritário para expansão.

Regras de operação inicial:

- a plataforma deve obedecer o idioma preferencial cadastrado do usuário;
- componentes, mensagens, mercados, emails e dashboards devem respeitar a localidade ativa;
- quando conteúdo de mercado precisar de versão adicional de idioma, a plataforma pode usar tradução assistida por IA, desde que o conteúdo base e a revisão administrativa permaneçam rastreáveis.

Objetivo arquitetural:

- evitar retrabalho estrutural quando o produto for expandido para múltiplos países;
- permitir crescimento internacional sem reescrever frontend, admin ou contratos principais.

---

## Escopo do MVP

### Incluído

- cadastro e login;
- login social com provedores externos;
- feed de mercados;
- página de detalhe do mercado;
- mercados binários (`SIM` ou `NÃO`);
- mercados de múltipla escolha com uma única opção vencedora;
- stake com moeda interna da plataforma;
- atualização de probabilidade após cada previsão;
- compartilhamento de pergunta e resultado em redes sociais;
- envio de emails transacionais e de engajamento;
- comentários em mercados;
- perfil com histórico do usuário;
- carteira do usuário com extrato e saldos;
- solicitação de exclusão lógica da conta;
- sugestões de mercado enviadas por usuários;
- feedback recompensável;
- ranking global;
- categorias iniciais;
- painel administrativo customizado para criar, resolver e moderar usuários e mercados.

### Fora do MVP

- dinheiro real;
- blockchain;
- wallets on-chain ou financeiras reais;
- seguidores;
- chat;
- criação de mercados por usuários comuns;
- tempo real avançado;
- live betting;
- candlestick charts;
- app mobile nativo.

---

## Arquitetura do MVP

### Stack definida

| Camada | Tecnologia | Papel no MVP |
|---|---|---|
| Web app | Django | Renderização HTML, composição de páginas, formulários e integração com o backend de domínio |
| Interações UI | HTMX + Alpine.js | Atualizações parciais, fluidez de interface e pequenos estados locais |
| Backend de domínio/API | FastAPI | Autenticação principal, regras de negócio, previsões, reputação, carteira e resolução |
| Comunicações | Módulo ou serviço de communications/email | Templates, orquestração e envio de emails transacionais e de engajamento |
| Admin principal | Painel administrativo customizado em Django | Operações administrativas de negócio e dashboard operacional |
| Admin de suporte | Django Admin | Suporte interno, inspeção técnica e troubleshooting |
| Banco principal | PostgreSQL | Persistência de usuários, mercados, previsões e métricas |
| Scheduler/Daemon | Processo dedicado | Fechamento automático de mercados e tarefas temporizadas críticas |
| Cache/assíncrono | Redis | Uso futuro para cache, filas e tarefas assíncronas quando necessário |

### Responsabilidades do Django

- servir páginas públicas e autenticadas;
- renderizar feed, detalhe de mercado, perfil, ranking e fluxos de login;
- atuar como cliente interno do FastAPI para operações de domínio;
- receber ações via formulários e HTMX e encaminhá-las ao backend principal;
- oferecer painel administrativo customizado para operação principal da plataforma;
- manter Django Admin apenas como ferramenta de suporte interno e inspeção técnica;
- aplicar internacionalização na camada de interface, templates e navegação;
- não concentrar lógica crítica de negócio nem lógica de comunicações.

### Responsabilidades do FastAPI

- ser a fonte principal de verdade do domínio;
- autenticar usuários;
- emitir e validar tokens de sessão;
- centralizar regras de negócio de mercados e previsões;
- calcular probabilidades, recompensas, bloqueio de saldo e reputação;
- expor endpoints JSON do domínio para consumo da camada web;
- sustentar regras críticas com foco em segurança, integridade e auditabilidade.

### Responsabilidades do scheduler/daemon

- monitorar mercados com fechamento agendado;
- fechar automaticamente mercados na data, horário e fuso configurados;
- disparar tarefas temporizadas de reconciliação e atualização operacional;
- funcionar sem intervenção manual do admin para rotinas críticas já programadas.

### Responsabilidades do subsistema de comunicações

- receber eventos de negócio disparados pelo backend de domínio;
- escolher template, idioma e contexto de comunicação;
- registrar eventos de envio, reenvio, sucesso e falha;
- integrar com provedor externo de email;
- permanecer isolado da camada web para futura extração como serviço independente.

### Relação entre as camadas

- o Django é a camada de apresentação;
- o FastAPI é a camada de domínio e API;
- scheduler/daemon é a camada de automação temporal da plataforma;
- comunicações é uma fronteira separada da camada web e da lógica principal de interface;
- o MVP é `API-first no domínio`, mas não é `SPA-first`;
- o FastAPI não renderiza HTML nesta fase;
- a experiência web é server-rendered, enriquecida com HTMX e Alpine.js;
- o monolito web não deve conter regras centrais de reputação, resolução, previsão ou envio de comunicações.

---

## Infraestrutura Inicial em Cloud

### Objetivo desta fase

A infraestrutura inicial deve priorizar:

- simplicidade operacional;
- baixo custo;
- separação mínima entre web e domínio;
- facilidade de deploy e manutenção;
- evitar Kubernetes e componentes distribuídos desnecessários no MVP.

### Componentes mínimos sugeridos

| Componente | Papel |
|---|---|
| EC2 pública | Receber tráfego HTTPS e hospedar `Caddy`, `Django`, `FastAPI` e scheduler/daemon em containers separados |
| PostgreSQL gerenciado | Banco principal do produto, fora da EC2 |

### Topologia inicial

```text
Internet
↓
Caddy HTTPS + Docker Compose (EC2 pública)
├─ Django web
├─ FastAPI domínio
└─ daemon operacional
↓
PostgreSQL gerenciado
```

### Responsabilidade da EC2

- expor apenas `80/443` para internet;
- terminar TLS/SSL no `Caddy`, com certificado automatico;
- fazer proxy reverso para o container Django;
- hospedar Django, FastAPI e daemon em containers separados no Docker Compose;
- manter `BACKEND_API_URL` apontando para a rede interna do Compose;
- rodar apenas um container do daemon por ambiente.

### Banco de dados

- usar `PostgreSQL gerenciado`;
- evitar banco dentro da EC2 no MVP;
- habilitar backup automático desde o início;
- restringir acesso do banco ao security group da EC2.

### Segurança mínima de infraestrutura

- restringir exposição pública da EC2 a `80/443` e SSH apenas para IPs autorizados;
- usar TLS/SSL no ponto de entrada público;
- não expor portas internas de Django/FastAPI para internet;
- não versionar `.env.prod` nem segredos;
- limitar acesso administrativo ao menor conjunto possível de pessoas;
- habilitar backups automáticos e política clara de recuperação.

### O que não entra nesta fase

- Kubernetes;
- Redis;
- object storage;
- CDN;
- workers separados;
- múltiplos ambientes complexos;
- autoscaling;
- service mesh;
- observabilidade distribuída avançada.

### Diretrizes operacionais

- usar deploy simples, preferencialmente com `Docker Compose`;
- manter apenas o ambiente `local` e um ambiente `produção` enxuto;
- centralizar o ponto de entrada público no Caddy;
- construir a imagem na EC2 a partir de `git pull` da branch publicada;
- executar migrations e `collectstatic` antes de reiniciar os serviços;
- priorizar configuração simples e auditável.

### Racional da escolha

Essa estrutura entrega:

- custo menor que um ambiente orquestrado;
- separação lógica entre camada web, domínio e daemon por containers;
- menor custo e menor fricção operacional do que duas VMs no MVP;
- menor complexidade do que Kubernetes para o estágio atual do produto.

### Evolução prevista

Quando houver necessidade operacional, FastAPI e daemon podem migrar para uma EC2 privada ou serviço gerenciado, mantendo Django/Caddy como ponto público e preservando o PostgreSQL gerenciado.

---

## Fluxo Principal do Usuário

```text
Usuário abre o app
↓
Visualiza o feed de mercados
↓
Entra em um mercado
↓
Escolhe uma opção do mercado
↓
Define stake em `Orynth Coins`
↓
Confirma previsão
↓
Probabilidade do mercado é atualizada
↓
Mercado é resolvido por admin na data apropriada
↓
Saldo em `Orynth Coins` e reputação são recalculados
↓
Usuário acompanha resultado no perfil e ranking
```

---

## Estrutura de Navegação

| Página | Objetivo principal |
|---|---|
| Feed | Descobrir mercados em aberto |
| Market Detail | Ver contexto, probabilidade e enviar previsão |
| Perfil | Exibir reputação, carteira e histórico |
| Wallet | Exibir carteira, saldo disponível, saldo bloqueado e extrato |
| Rankings | Comparar desempenho entre usuários |
| Categorias | Filtrar mercados por tema |
| Feedback/Suporte | Enviar feedback ou pedido de suporte para a plataforma |
| Suggestion | Enviar sugestão de mercado para curadoria |
| Admin | Operar criação, moderação e resolução via painel customizado |

---

## Categorias Iniciais

- IA
- Games
- Creators
- Internet Trends
- Futebol
- Cultura Pop

Observação: o MVP deve começar com poucas categorias para evitar feed vazio e dispersão de volume.

### Taxonomia de classificação

Além da categoria principal, o mercado pode pertencer a uma subcategoria orientada a evento.

Exemplo:

- `Categoria = Futebol`
- `Subcategoria/Evento = Copa do Mundo 2026`

Objetivo:

- organizar melhor grandes temas com eventos recorrentes;
- facilitar navegação por contexto específico;
- permitir campanhas, rankings e badges mais contextuais no futuro.

---

## Mecânica Central do Produto

No MVP, cada mercado representa uma pergunta objetiva com um conjunto finito de resultados possíveis.

Os dois tipos iniciais de mercado são:

- `binary`: duas opções possíveis, como `SIM` e `NÃO`;
- `multiple_choice`: três ou mais opções possíveis, com uma única vencedora ao final.

O usuário participa aportando `Orynth Coins` em uma das opções disponíveis. O sistema agrega o peso das previsões e transforma isso em uma probabilidade percebida pelo mercado para cada opção.

Essa probabilidade tem três funções:

- sinalizar consenso coletivo;
- influenciar o ganho potencial;
- influenciar a variação de reputação.

No lançamento, o produto já deve suportar `binary` e `multiple_choice`, preservando a mesma lógica central de peso, probabilidade, recompensa e reputação.

---

## Regras de Mercado

### Critérios obrigatórios para criar um mercado

Toda pergunta deve:

- ser objetiva;
- ter data ou condição clara de resolução;
- possuir fonte pública verificável;
- permitir resolução inequívoca;
- ter texto simples o suficiente para leitura rápida no feed.

### Exemplos de boas perguntas

- `GTA VI será adiado para 2027?`
- `OpenAI lançará GPT-6 em 2026?`
- `TikTok será banido nos EUA?`
- `Qual empresa lançará primeiro um agente de consumo em massa?`

### Exemplos de perguntas ruins

| Pergunta | Problema |
|---|---|
| `IA dominará o mundo?` | subjetiva |
| `Bitcoin vai explodir?` | ambígua |
| `Esse creator vai cair?` | mal definida |

### Estados do mercado

- `draft`: criado, ainda não publicado;
- `open`: aceitando previsões;
- `closed`: fechado para novas previsões, aguardando resolução;
- `resolved`: resultado final publicado;
- `cancelled`: mercado invalidado por erro de formulação ou impossibilidade de resolução.

Para o MVP, `draft`, `open` e `resolved` são suficientes. `closed` e `cancelled` podem existir como estados previstos no modelo, mesmo que não sejam totalmente explorados na interface inicial.

---

## Modelo Econômico do MVP

### Moeda interna do MVP

Para evitar ambiguidade entre saldo, recompensa e extrato, o MVP deve adotar uma moeda interna explícita da plataforma.

Nome adotado nesta spec:

- `Orynth Coins`

Sugestões de naming que podem ser avaliadas depois sem impacto arquitetural:

- `Pulse`
- `Signals`
- `Orynth Credits`
- `Insight Coins`

### Saldo inicial do usuário

Todo usuário inicia com:

| Campo | Valor inicial |
|---|---:|
| `orynth_coins_available` | 1000 |
| `orynth_coins_locked` | 0 |
| `reputation` | 100 |

### Recarga controlada de moeda interna

Para evitar que o usuário fique permanentemente travado após perder todo o saldo, o sistema deve prever uma recarga controlada de `Orynth Coins`.

Diretriz recomendada para o MVP:

- se o usuário ficar abaixo de um piso mínimo de `Orynth Coins`, pode receber recarga automática;
- a recarga deve acontecer no máximo uma vez por janela de tempo;
- a recarga devolve capacidade de participar, mas não recompõe reputação;
- a recarga deve ser pequena o suficiente para preservar o valor relativo das `Orynth Coins`.

Exemplo inicial de política:

- se `orynth_coins_available < 100`, conceder `+300` `Orynth Coins`;
- limite de uma recarga por dia.

Objetivo:

- evitar abandono por falta total de saldo;
- manter `Orynth Coins` como recurso renovável, mas controlado;
- preservar reputação como sinal meritocrático separado.

### Indicação e bônus de aquisição

O sistema pode conceder `Orynth Coins` por indicação de novos usuários, desde que o bônus esteja vinculado a ativação real e não apenas ao clique ou cadastro.

Diretriz recomendada para o MVP:

- cada usuário recebe link ou código de convite;
- o convidado deve criar conta e completar uma ação mínima real;
- o bônus só é liberado após essa ativação;
- indicação concede `Orynth Coins`, mas nunca reputação.

Exemplo inicial de política:

- indicador recebe `+200` `Orynth Coins`;
- convidado recebe `+100` `Orynth Coins` extras;
- gatilho do bônus: conta criada e primeira previsão válida realizada pelo convidado.

Regras de proteção:

- impedir autoindicação;
- impedir bônus duplicado para o mesmo convidado;
- limitar bônus por período, se necessário;
- não conceder reputação por convite;
- manter o valor do bônus abaixo do saldo inicial padrão.

### Carteira, saldo disponível e saldo bloqueado

O MVP deve tratar a moeda interna com uma carteira contábil simples, auditável e compatível com histórico de movimentações.

Regras centrais:

- todo usuário possui carteira própria;
- o saldo deve ser dividido entre `available_balance` e `locked_balance`;
- quando o usuário faz uma previsão, o valor do `stake` é transferido de saldo disponível para saldo bloqueado;
- saldo bloqueado não pode ser reutilizado em outro mercado enquanto a previsão estiver ativa;
- quando o mercado é resolvido, o sistema liquida o valor bloqueado como perda, devolução ou ganho, conforme a regra final de recompensa;
- toda mudança de saldo deve gerar lançamento rastreável no extrato da carteira.

Objetivos:

- impedir que o usuário negocie mais moeda do que realmente possui;
- dar clareza sobre o que está livre, comprometido e liquidado;
- preservar auditabilidade da economia do produto.

### Liquidez sintética inicial

Para evitar oscilações extremas em mercados vazios, cada opção começa com um peso base:

```python
BASE_WEIGHT = 10_000
```

| Opção | Peso inicial |
|---|---:|
| `SIM` | 10_000 |
| `NÃO` | 10_000 |

Em `multiple_choice`, a mesma lógica se aplica a cada alternativa do mercado.

### Peso de uma previsão

Fórmula inicial:

```text
peso = reputacao_do_usuario x stake
```

Observação importante: essa fórmula tende a concentrar poder em usuários já bem posicionados. Para o MVP ela pode ser mantida como experimento inicial, mas deve ser monitorada de perto. Uma alternativa futura é usar peso amortecido, por exemplo `log`, `sqrt` ou reputação normalizada.

### Probabilidade agregada

Para mercados binários:

```text
P(SIM) = peso_total_SIM / (peso_total_SIM + peso_total_NAO)
P(NAO) = 1 - P(SIM)
```

Onde:

- `peso_total_SIM = BASE_WEIGHT + soma_dos_pesos_no_lado_SIM`
- `peso_total_NAO = BASE_WEIGHT + soma_dos_pesos_no_lado_NAO`

Para mercados de múltipla escolha:

```text
P(opcao_i) = peso_total_opcao_i / soma_de_todos_os_pesos_das_opcoes
```

Onde:

- `peso_total_opcao_i = BASE_WEIGHT + soma_dos_pesos_da_opcao_i`
- a soma de todas as probabilidades do mercado deve ser `100%`

---

## Recompensa em `Orynth Coins`

Objetivo da fórmula:

- previsões fáceis pagam menos;
- previsões contra o consenso pagam mais;
- usuários são incentivados a procurar assimetrias.

Fórmula inicial proposta:

```text
reward_bruto = stake x (1 / p)
```

Onde:

- `p` é a probabilidade do lado escolhido no momento da entrada;
- se o usuário errar, o stake é perdido;
- se acertar, recebe o `reward_bruto`.

### Exemplos

| Probabilidade de entrada | Stake | Reward bruto |
|---|---:|---:|
| 90% | 100 | 111 |
| 50% | 100 | 200 |
| 20% | 100 | 500 |

### Observação de produto

Essa fórmula é simples e boa para explicar o sistema, mas pode gerar inflação de `Orynth Coins` se não houver contrapesos. Para o MVP, isso é aceitável desde que existam métricas para acompanhar:

- distribuição de saldo entre usuários;
- velocidade de crescimento das `Orynth Coins`;
- concentração no topo do ranking.

Se necessário, uma etapa seguinte pode introduzir:

- reward líquido ao invés de bruto;
- teto por mercado;
- taxa de participação;
- reset sazonal de ranking.

---

## Sistema de Reputação

A reputação mede qualidade preditiva, não riqueza do usuário.

### Fórmula inicial

Se acertar:

```text
delta_R = K x (1 - p)
```

Se errar:

```text
delta_R = -K x p
```

Configuração inicial:

```python
K_FACTOR = 10
```

### Intuição

- acertar uma previsão óbvia gera pouco ganho reputacional;
- acertar uma previsão difícil gera ganho maior;
- errar quando o mercado já considerava algo provável gera penalidade maior.

### Exemplos de ganho reputacional ao acertar

| Probabilidade | Resultado | Delta reputacao |
|---|---|---:|
| 90% | acertou | +1 |
| 50% | acertou | +5 |
| 20% | acertou | +8 |

### Regras operacionais sugeridas

- reputação mínima: `0`;
- reputação não deve ficar negativa no MVP;
- reputação deve ser atualizada apenas na resolução do mercado;
- ranking principal pode usar reputação, não apenas saldo em `Orynth Coins`.

---

## Entidades Principais

### User

```python
class User:
    id: UUID
    username: str
    email: str
    password_hash: str
    preferred_locale: str
    account_status: str
    # active | blocked | banned | user_deactivated
    is_blocked: bool
    is_banned: bool
    banned_reason: str | None
    referral_code: str | None
    referred_by_user_id: UUID | None
    last_orynth_coins_refill_at: datetime | None
    deletion_requested_at: datetime | None
    deactivated_at: datetime | None

    reputation: float

    predictions_count: int
    correct_predictions: int

    created_at: datetime
    updated_at: datetime
```

Descrição dos campos:

- `id`: identificador único do usuário.
- `username`: nome público exibido no produto.
- `email`: credencial única de acesso e comunicação.
- `password_hash`: senha armazenada de forma segura, nunca em texto puro.
- `preferred_locale`: idioma preferencial do usuário para interface e comunicações.
- `account_status`: estado principal da conta para autenticação e governança.
- `is_blocked`: indica bloqueio operacional temporário do acesso ou de certas ações.
- `is_banned`: indica banimento do usuário por violação de regras da plataforma.
- `banned_reason`: justificativa administrativa para bloqueio ou banimento, quando houver.
- `referral_code`: código público usado para indicar novos usuários.
- `referred_by_user_id`: usuário responsável pela indicação, quando houver.
- `last_orynth_coins_refill_at`: data da última recarga automática de `Orynth Coins`.
- `deletion_requested_at`: momento em que o usuário pediu exclusão lógica da conta.
- `deactivated_at`: momento em que a conta foi efetivamente desativada sem remoção física de dados.
- `reputation`: pontuação reputacional acumulada com base no desempenho preditivo.
- `predictions_count`: total de previsões registradas pelo usuário.
- `correct_predictions`: total de previsões vencedoras ou corretas.
- `created_at`: data de criação da conta.
- `updated_at`: data da última atualização relevante do registro.

### UserAuthProvider

```python
class UserAuthProvider:
    id: UUID

    user_id: UUID
    provider: str
    provider_user_id: str
    email_from_provider: str | None

    created_at: datetime
    updated_at: datetime
```

Descrição dos campos:

- `id`: identificador único do vínculo de autenticação social.
- `user_id`: usuário local associado ao provedor externo.
- `provider`: nome do provedor, como `facebook`, `google` ou `x`.
- `provider_user_id`: identificador do usuário no provedor externo.
- `email_from_provider`: email retornado pelo provedor, quando disponível.
- `created_at`: data de criação do vínculo.
- `updated_at`: data da última atualização do vínculo.

### ReferralEvent

```python
class ReferralEvent:
    id: UUID

    referrer_user_id: UUID
    referred_user_id: UUID

    status: str
    # pending | qualified | rewarded | rejected

    referrer_orynth_coins_bonus: int
    referred_orynth_coins_bonus: int

    qualified_at: datetime | None
    rewarded_at: datetime | None
    rejection_reason: str | None

    created_at: datetime
```

Descrição dos campos:

- `id`: identificador único do evento de indicação.
- `referrer_user_id`: usuário que fez a indicação.
- `referred_user_id`: usuário convidado.
- `status`: estado do processo de indicação.
- `referrer_orynth_coins_bonus`: bônus previsto ou entregue ao indicador.
- `referred_orynth_coins_bonus`: bônus previsto ou entregue ao convidado.
- `qualified_at`: data em que a indicação cumpriu o critério de ativação.
- `rewarded_at`: data em que as `Orynth Coins` foram efetivamente creditadas.
- `rejection_reason`: motivo de invalidação da indicação, quando houver.
- `created_at`: data de criação do evento.

### Wallet

```python
class Wallet:
    id: UUID

    user_id: UUID
    currency_code: str

    available_balance: int
    locked_balance: int
    lifetime_earned: int
    lifetime_spent: int

    created_at: datetime
    updated_at: datetime
```

Descrição dos campos:

- `id`: identificador único da carteira.
- `user_id`: usuário dono da carteira.
- `currency_code`: código interno da moeda, como `ORYNTH_COINS`.
- `available_balance`: saldo livre para novas previsões ou recompensas configuradas.
- `locked_balance`: saldo comprometido em previsões ainda não liquidadas.
- `lifetime_earned`: total histórico de moeda adquirida pelo usuário.
- `lifetime_spent`: total histórico de moeda comprometida ou consumida.
- `created_at`: data de criação da carteira.
- `updated_at`: data da última atualização de saldo.

### WalletTransaction

```python
class WalletTransaction:
    id: UUID

    wallet_id: UUID
    user_id: UUID

    transaction_type: str
    # initial_grant | refill | referral_bonus | suggestion_bonus | feedback_bonus | stake_lock | stake_release | prediction_payout | prediction_loss | admin_adjustment

    amount_delta: int
    available_balance_after: int
    locked_balance_after: int

    reference_type: str | None
    reference_id: UUID | None
    notes: str | None

    created_at: datetime
```

Descrição dos campos:

- `id`: identificador único do lançamento financeiro interno.
- `wallet_id`: carteira impactada pela movimentação.
- `user_id`: usuário afetado pela movimentação.
- `transaction_type`: tipo do evento que gerou o lançamento.
- `amount_delta`: variação do saldo causada pelo evento.
- `available_balance_after`: saldo disponível após o lançamento.
- `locked_balance_after`: saldo bloqueado após o lançamento.
- `reference_type`: tipo do objeto relacionado, como `prediction`, `referral`, `feedback` ou `market_suggestion`.
- `reference_id`: identificador do objeto de origem do lançamento.
- `notes`: observação opcional para contexto administrativo ou auditoria.
- `created_at`: data de criação do lançamento.

### MarketSuggestion

```python
class MarketSuggestion:
    id: UUID

    user_id: UUID

    question: str
    description: str | None
    category: str
    event_subcategory: str | None
    suggested_resolution_date: datetime | None
    suggested_source_url: str | None
    rationale: str | None

    status: str
    # pending | approved | rejected | published

    reviewed_by_user_id: UUID | None
    linked_market_id: UUID | None
    reward_orynth_coins_granted: int | None
    rejection_reason: str | None

    created_at: datetime
    reviewed_at: datetime | None
```

Descrição dos campos:

- `id`: identificador único da sugestão de mercado.
- `user_id`: usuário que enviou a sugestão.
- `question`: pergunta sugerida pelo usuário.
- `description`: contexto opcional para ajudar a avaliação editorial.
- `category`: categoria sugerida para o mercado.
- `event_subcategory`: evento, torneio ou subcategoria sugerida dentro da categoria principal.
- `suggested_resolution_date`: data ou janela sugerida para resolução.
- `suggested_source_url`: fonte sugerida para futura validação ou contexto.
- `rationale`: justificativa curta explicando por que a pergunta é relevante.
- `status`: estado da sugestão no fluxo de curadoria.
- `reviewed_by_user_id`: administrador que revisou a sugestão.
- `linked_market_id`: mercado publicado gerado a partir da sugestão, se houver.
- `reward_orynth_coins_granted`: bônus em `Orynth Coins` concedido ao autor quando a sugestão virar mercado.
- `rejection_reason`: motivo da rejeição, quando aplicável.
- `created_at`: data de envio da sugestão.
- `reviewed_at`: data da revisão administrativa.

### Market

```python
class Market:
    id: UUID

    question: str
    description: str | None
    category: str
    event_subcategory: str | None
    base_locale: str
    market_type: str
    # binary | multiple_choice
    status: str
    icon_url: str | None
    image_url: str | None
    close_at: datetime
    close_timezone: str
    auto_close_enabled: bool
    resolution_date: datetime
    resolution_source_url: str | None
    result: str | None
    result_option_id: UUID | None
    created_by: UUID

    probability_yes: float
    probability_no: float

    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
```

Observação:

- no MVP, `market_type` já pode ser `binary` ou `multiple_choice`;
- `multiple_choice` permite mercados com várias alternativas e uma única vencedora;
- `result_option_id` permite resolução por opção em ambos os tipos.

Descrição dos campos:

- `id`: identificador único do mercado.
- `question`: pergunta principal exibida para o usuário.
- `description`: texto de contexto, critério de interpretação e detalhes de resolução.
- `category`: agrupamento temático do mercado.
- `event_subcategory`: evento, temporada, torneio ou subtema específico dentro da categoria.
- `base_locale`: idioma base em que o mercado foi originalmente definido.
- `market_type`: tipo do mercado, como `binary` ou `multiple_choice`.
- `status`: estado operacional do mercado, como `draft`, `open`, `closed`, `resolved` ou `cancelled`.
- `icon_url`: ícone pequeno opcional usado em feed, cards ou listagens.
- `image_url`: imagem opcional do mercado para destaque visual e compartilhamento.
- `close_at`: data e hora exata de encerramento para novas previsões.
- `close_timezone`: fuso oficial usado na configuração de encerramento.
- `auto_close_enabled`: indica se o mercado deve ser fechado automaticamente pelo scheduler.
- `resolution_date`: data-limite ou momento previsto para a resolução.
- `resolution_source_url`: fonte pública usada para justificar o resultado final.
- `result`: campo legado ou simplificado para binário, por exemplo `yes` ou `no`.
- `result_option_id`: identificador da opção vencedora quando o mercado for resolvido por alternativa.
- `created_by`: usuário ou administrador responsável pela criação do mercado.
- `probability_yes`: probabilidade agregada de `SIM` para mercados binários.
- `probability_no`: probabilidade agregada de `NÃO` para mercados binários.
- `created_at`: data de criação do mercado.
- `updated_at`: data da última modificação relevante.
- `resolved_at`: data efetiva da resolução do mercado, se já concluído.

### MarketOption

```python
class MarketOption:
    id: UUID

    market_id: UUID

    label: str
    slug: str | None
    description: str | None

    position: int
    is_active: bool

    created_at: datetime
```

Função da entidade:

- armazenar as opções possíveis de um mercado;
- suportar desde mercados binários até múltipla escolha;
- permitir ordenação consistente e exibição no feed e detalhe.

Decisão recomendada de modelagem:

- tratar `binary` como um mercado com duas opções internas (`SIM` e `NÃO`);
- usar `MarketOption` como base estrutural para os dois tipos de mercado.

Descrição dos campos:

- `id`: identificador único da opção.
- `market_id`: referência ao mercado ao qual a opção pertence.
- `label`: texto principal exibido como alternativa da previsão.
- `slug`: identificador textual opcional para URLs, integrações ou consumo interno.
- `description`: texto opcional explicando melhor a alternativa quando necessário.
- `position`: ordem de exibição da opção no admin e na interface pública.
- `is_active`: indica se a opção ainda é válida e visível no mercado.
- `created_at`: data de criação da opção.

### Prediction

```python
class Prediction:
    id: UUID

    user_id: UUID
    market_id: UUID
    market_option_id: UUID | None

    choice: str
    stake: int
    user_reputation_at_entry: float
    probability_at_entry: float
    weight_at_entry: float

    orynth_coins_delta: int | None
    reputation_delta: float | None
    won: bool | None

    created_at: datetime
```

Observação:

- `market_option_id` deve ser o vínculo principal entre previsão e alternativa escolhida;
- `choice` pode existir apenas como compatibilidade ou simplificação de apresentação para o caso binário;
- isso evita duplicidade de modelagem entre os dois tipos do MVP.

Descrição dos campos:

- `id`: identificador único da previsão.
- `user_id`: usuário que realizou a previsão.
- `market_id`: mercado em que a previsão foi feita.
- `market_option_id`: opção específica escolhida pelo usuário.
- `choice`: representação simplificada para mercados binários, se ainda mantida.
- `stake`: quantidade de `Orynth Coins` comprometida na previsão.
- `user_reputation_at_entry`: reputação do usuário no momento em que entrou no mercado.
- `probability_at_entry`: probabilidade da opção escolhida no momento da entrada.
- `weight_at_entry`: peso calculado da previsão no momento da entrada.
- `orynth_coins_delta`: variação final de `Orynth Coins` causada por essa previsão após a resolução.
- `reputation_delta`: variação final de reputação causada por essa previsão.
- `won`: indica se a previsão foi vencedora, perdedora ou ainda não resolvida.
- `created_at`: data de criação da previsão.

### Comment

```python
class Comment:
    id: UUID

    market_id: UUID
    user_id: UUID
    parent_comment_id: UUID | None

    body: str
    status: str
    # active | hidden | removed

    created_at: datetime
    updated_at: datetime
```

Descrição dos campos:

- `id`: identificador único do comentário.
- `market_id`: mercado ao qual o comentário pertence.
- `user_id`: autor do comentário.
- `parent_comment_id`: referência opcional para resposta a outro comentário.
- `body`: conteúdo textual do comentário.
- `status`: estado de moderação do comentário.
- `created_at`: data de criação do comentário.
- `updated_at`: data da última atualização ou moderação.

### CommentLike

```python
class CommentLike:
    id: UUID

    comment_id: UUID
    user_id: UUID

    created_at: datetime
```

Descrição dos campos:

- `id`: identificador único da curtida.
- `comment_id`: comentário que recebeu a curtida.
- `user_id`: usuário que realizou a curtida.
- `created_at`: data em que a curtida foi registrada.

Regra principal:

- um mesmo usuário pode curtir um comentário no máximo uma vez;
- o comportamento suportado no MVP é apenas `like` e `unlike`.

### FeedbackSubmission

```python
class FeedbackSubmission:
    id: UUID

    user_id: UUID
    locale: str
    subject: str | None
    body: str

    status: str
    # pending | reviewed | rewarded | rejected

    reviewed_by_user_id: UUID | None
    reward_orynth_coins_granted: int | None
    admin_notes: str | None

    created_at: datetime
    reviewed_at: datetime | None
```

Descrição dos campos:

- `id`: identificador único do feedback enviado.
- `user_id`: usuário autor do feedback.
- `locale`: idioma em que o feedback foi escrito.
- `subject`: resumo opcional do tema reportado.
- `body`: conteúdo textual principal do feedback.
- `status`: estado de revisão e eventual recompensa.
- `reviewed_by_user_id`: administrador que revisou o feedback.
- `reward_orynth_coins_granted`: quantidade de `Orynth Coins` concedida se o feedback for recompensado.
- `admin_notes`: observações internas da revisão.
- `created_at`: data do envio.
- `reviewed_at`: data da análise administrativa.

### EmailEvent

```python
class EmailEvent:
    id: UUID

    user_id: UUID
    event_type: str
    # welcome | prediction_won | prediction_lost | milestone | reminder
    status: str
    # pending | sent | failed

    related_market_id: UUID | None
    related_prediction_id: UUID | None

    payload_snapshot: dict

    created_at: datetime
    sent_at: datetime | None
```

Descrição dos campos:

- `id`: identificador do evento de email.
- `user_id`: usuário destinatário da comunicação.
- `event_type`: tipo de email disparado pela plataforma.
- `status`: estado de envio do email.
- `related_market_id`: mercado relacionado ao evento, quando aplicável.
- `related_prediction_id`: previsão relacionada ao evento, quando aplicável.
- `payload_snapshot`: contexto mínimo usado para compor a mensagem.
- `created_at`: data de geração do evento.
- `sent_at`: data efetiva do envio, quando ocorrer.

### Badge

```python
class Badge:
    id: UUID
    code: str
    name: str
    description: str

    badge_type: str
    # global | category | performance

    category: str | None
    is_active: bool

    created_at: datetime
    updated_at: datetime
```

Descrição dos campos:

- `id`: identificador único da badge.
- `code`: identificador técnico estável da badge.
- `name`: nome público exibido ao usuário.
- `description`: descrição curta do significado da badge.
- `badge_type`: tipo da badge, como global, por categoria ou performance.
- `category`: categoria associada quando a badge for temática.
- `is_active`: indica se a badge está ativa para concessão e exibição.
- `created_at`: data de criação da badge.
- `updated_at`: data da última atualização da definição.

### UserBadge

```python
class UserBadge:
    id: UUID

    user_id: UUID
    badge_id: UUID

    awarded_at: datetime
    reason_snapshot: str | None
```

Descrição dos campos:

- `id`: identificador único da conquista de badge.
- `user_id`: usuário que recebeu a badge.
- `badge_id`: badge conquistada.
- `awarded_at`: data da concessão.
- `reason_snapshot`: contexto resumido do motivo da conquista.

### BadgeRule

```python
class BadgeRule:
    id: UUID

    badge_id: UUID
    rule_type: str
    # prediction_count | accuracy | category_accuracy | streak | ranking | contrarian_win

    threshold_value: float
    min_predictions: int | None
    category: str | None

    is_active: bool
```

Descrição dos campos:

- `id`: identificador único da regra.
- `badge_id`: badge governada pela regra.
- `rule_type`: tipo de critério de desbloqueio.
- `threshold_value`: valor principal usado na condição.
- `min_predictions`: volume mínimo exigido, quando necessário.
- `category`: categoria vinculada à regra, quando aplicável.
- `is_active`: indica se a regra está em vigor.

---

## Sistema de Badges

### Objetivo

Badges funcionam como camada complementar de reconhecimento e incentivo. Elas não substituem reputação nem ranking, mas ajudam a reforçar progressão, especialização temática e desempenho diferenciado.

### Tipos de badge

#### Badges globais

Reconhecem trajetória geral do usuário na plataforma.

Exemplos iniciais:

- `Primeira Previsão`
- `10 Previsões`
- `5 Acertos`
- `Top 10 do Mês`

#### Badges por categoria

Reconhecem especialização em categorias do produto.

Exemplos iniciais:

- `Especialista em IA`
- `Especialista em Games`
- `Especialista em Futebol`

Critério recomendado:

- volume mínimo de previsões na categoria;
- combinado com taxa de acerto mínima ou reputação mínima naquela categoria.

#### Badges de performance

Reconhecem feitos de maior dificuldade ou consistência.

Exemplos iniciais:

- `Contra o Consenso`
- `Sequência de 5`
- `Alta Precisão`

### Critérios de desbloqueio

Regras gerais:

- evitar badges fáceis de farmar;
- privilegiar consistência, qualidade e especialização;
- não usar compartilhamento ou atividade superficial como critério principal.

Exemplos iniciais:

- `Primeira Previsão`: desbloqueia ao registrar a primeira previsão.
- `10 Previsões`: desbloqueia ao atingir dez previsões totais.
- `5 Acertos`: desbloqueia ao atingir cinco previsões vencedoras.
- `Especialista em IA`: exige volume mínimo em `IA` e desempenho mínimo nessa categoria.
- `Contra o Consenso`: exige acerto em previsão feita com baixa probabilidade de entrada.
- `Sequência de 5`: exige cinco acertos consecutivos.

### Exibição no produto

No perfil:

- exibir badges conquistadas pelo usuário;
- destacar badges mais recentes, raras ou relevantes;
- separar visualmente badges globais, de categoria e de performance.

No ranking:

- exibir de forma resumida uma ou duas badges de destaque;
- evitar poluição visual excessiva.

### Compartilhamento de badge

O usuário deve poder compartilhar a badge conquistada nas redes sociais.

Regras iniciais:

- o sistema deve gerar link compartilhável da badge recebida;
- o compartilhamento deve incluir nome da badge, descrição curta e contexto mínimo;
- o conteúdo compartilhado deve respeitar idioma e identidade visual da plataforma;
- compartilhar badge não altera reputação, `Orynth Coins` nem ranking.

### Diretriz de produto

- badges complementam o sistema reputacional;
- reputação continua sendo o principal sinal de qualidade preditiva;
- badges devem premiar mérito real, não comportamento trivial.

---

## Mercados de Múltipla Escolha

### Conceito

Em mercados `multiple_choice`, o usuário escolhe uma entre várias alternativas possíveis, e apenas uma delas é vencedora ao final.

Exemplos:

- `Quem vencerá a eleição?`
- `Qual empresa lançará primeiro um agente de consumo em massa?`
- `Qual jogo será o mais vendido do ano?`

### Quando usar

Esse tipo funciona bem quando:

- existem poucas alternativas plausíveis;
- as opções são mutuamente exclusivas;
- a resolução final aponta claramente para uma única opção vencedora.

Não é recomendado quando:

- várias opções podem acontecer ao mesmo tempo;
- a pergunta exige interpretação subjetiva;
- há opções demais para o usuário entender rapidamente.

### Regras sugeridas

- limitar a quantidade inicial de opções, idealmente entre `3` e `5`;
- exigir que uma única opção seja vencedora;
- manter a resolução apoiada em fonte pública verificável;
- evitar mercados com excesso de alternativas no feed inicial.

### Probabilidade em múltipla escolha

Cada opção acumula peso próprio:

```text
peso = reputacao_do_usuario x stake
```

Para cada alternativa:

```text
peso_total_opcao_i = BASE_WEIGHT_OPCAO + soma_dos_pesos_da_opcao_i
```

E a probabilidade de cada opção é:

```text
P(opcao_i) = peso_total_opcao_i / soma_de_todos_os_pesos_das_opcoes
```

Observações:

- a soma de todas as probabilidades deve ser `100%`;
- a lógica preserva a ideia de consenso coletivo já usada no binário;
- mercados com muitas opções podem exigir ajuste no peso base sintético.

### Recompensa em múltipla escolha

A lógica permanece equivalente ao mercado binário:

```text
reward_bruto = stake x (1 / p)
```

Onde:

- `p` é a probabilidade da opção escolhida no momento da entrada.

Consequência esperada:

- opções menos prováveis pagam mais se estiverem corretas;
- opções mais consensuais pagam menos.

### Reputação em múltipla escolha

Também pode seguir a mesma fórmula base:

Se acertar:

```text
delta_R = K x (1 - p)
```

Se errar:

```text
delta_R = -K x p
```

Isso mantém coerência entre tipos de mercado:

- acertos difíceis aumentam mais a reputação;
- erros em previsões tidas como prováveis penalizam mais.

### Recomendação de produto

- lançar `binary` e `multiple_choice` já no MVP;
- limitar múltipla escolha a mercados com poucas alternativas;
- preservar a mesma lógica de cálculo entre os dois tipos para reduzir complexidade operacional.

### Observação sobre múltiplas entradas

Decisão recomendada para o MVP:

- permitir múltiplas previsões do mesmo usuário no mesmo mercado, desde que o mercado esteja `open`.

Vantagens:

- simplifica engajamento;
- permite que o usuário reforce convicção;
- gera comportamento mais próximo de mercado.

Risco:

- aumenta a complexidade de cálculo e leitura do histórico.

Se quisermos simplificar ao máximo a primeira release, outra opção é:

- permitir apenas uma previsão por usuário por mercado.

Esta é uma decisão em aberto e deve ser fechada antes da implementação do backend.

---

## Requisitos Funcionais

### Autenticação

- autenticação principal é executada no FastAPI;
- login deve gerar cookie seguro com token compartilhado entre as camadas;
- Django deve reutilizar o contexto autenticado para páginas e ações protegidas;
- não deve existir sistema duplo e concorrente de autenticação;
- usuário pode criar conta;
- criação de conta pode exigir reCAPTCHA v2 checkbox quando a proteção anti-abuso estiver configurada;
- usuário pode fazer login;
- usuário pode se registrar e autenticar com provedores sociais suportados;
- usuário autenticado pode ver sua carteira, reputação e histórico.

Provedores iniciais desejados:

- `Facebook`
- `X/Twitter`

Observação: a arquitetura deve permitir adicionar outros provedores no futuro sem reescrever o fluxo principal de autenticação.

### Internacionalização

- o usuário deve poder consumir a interface em idiomas suportados pela plataforma;
- a aplicação deve suportar mudança de idioma sem alterar a lógica de negócio;
- conteúdos estáticos e mensagens do sistema devem ser traduzíveis;
- o admin deve ser capaz de identificar idioma principal e conteúdo base do mercado;
- a modelagem deve prever evolução para mercados com conteúdo localizado.

### Feed

- listar mercados abertos;
- permitir ordenação por tendência, encerrando em breve, volume, mais recentes e favoritos editoriais;
- exibir pergunta, categoria, subcategoria/evento quando houver, probabilidade atual e volume básico;
- exibir contador simples de curtidas no card do mercado como sinal social;
- permitir destaque editorial de até dois mercados no card principal do feed;
- preencher destaque principal com mercados publicados não cancelados mais visualizados, excluindo `draft` e `cancelled`, usando mercado mais novo como desempate;
- exibir tipo de mercado quando isso ajudar a leitura;
- ser renderizado no Django com possibilidade de atualização parcial via HTMX.

### Sugestão de mercados

- usuários autenticados ou visitantes identificados por nome/email podem enviar sugestão de pergunta para análise editorial;
- visitantes precisam concluir reCAPTCHA v2 checkbox quando a proteção anti-abuso estiver configurada;
- a sugestão não cria mercado automaticamente;
- a sugestão deve entrar em fila de revisão administrativa;
- o admin pode aprovar, editar, rejeitar ou transformar a sugestão em mercado publicado;
- se a sugestão virar mercado publicado, o autor pode receber bônus em `Orynth Coins`;
- bônus por sugestão aprovada nunca concede reputação.

### Detalhe do mercado

- exibir pergunta completa;
- mostrar explicação curta e data de resolução;
- exibir ícone e imagem do mercado quando configurados;
- mostrar probabilidade atual de cada opção do mercado;
- permitir enviar previsão com stake;
- permitir comentar no mercado;
- permitir compartilhar a pergunta e o resultado do mercado;
- mostrar resultado quando resolvido;
- submeter ações ao Django, que encaminha a operação de domínio ao FastAPI.

### Perfil

- exibir carteira com saldo disponível, saldo bloqueado, ganhos, cargas de `Orynth Coins` e extrato;
- exibir reputação;
- permitir edição privada e opcional, na própria tela de perfil, de email, idioma, bio, data de nascimento (`birth_date`, formato `YYYY-MM-DD`) e sexo (`male`, `female`, `other`, `prefer_not_to_say`);
- não expor email, data de nascimento, sexo nem metadados privados no perfil público;
- exibir total de previsões;
- exibir taxa de acerto;
- listar mercados previstos e resultados;
- exibir badges conquistadas pelo usuário;
- exibir, se desejado, código ou link de indicação do usuário.

### Exclusão lógica da conta

- o usuário deve poder solicitar exclusão lógica da própria conta;
- a exclusão lógica deve impedir novo login e uso normal da plataforma;
- a conta não deve ser removida fisicamente do banco;
- previsões, comentários, transações de carteira e trilhas de auditoria devem ser preservados;
- o admin deve conseguir identificar contas desativadas pelo próprio usuário.

### Comentários

- usuários autenticados podem comentar em mercados;
- usuários autenticados podem responder a comentários, se esse recurso for mantido no MVP;
- usuários autenticados podem curtir e descurtir comentários;
- comentários devem estar sujeitos a moderação administrativa;
- comentários removidos ou ocultados não devem desaparecer sem estado claro para a plataforma.

Regras iniciais de curtida:

- cada usuário pode manter no máximo uma curtida por comentário;
- não haverá reactions múltiplas nesta fase;
- a interface deve exibir contador simples de curtidas;
- curtidas não substituem moderação nem relevância editorial da plataforma.

### Compartilhamento social

- o usuário pode compartilhar a pergunta de um mercado em redes sociais;
- o usuário pode compartilhar o resultado de um mercado após a resolução;
- o usuário pode compartilhar badges conquistadas;
- a plataforma deve gerar links compartilháveis consistentes;
- compartilhamento deve respeitar idioma e contexto mínimo da página;
- páginas de compartilhamento devem expor metadados Open Graph/Twitter com imagem social gerada em formato amplo para pergunta, resultado e badge;
- cards sociais de mercado devem trazer contexto curto para aquisição de novos usuários e chamada competitiva, sem linguagem de aposta real;
- cards sociais de resultado devem dar protagonismo à pergunta e exibir o resultado imediatamente abaixo;
- links públicos de badge conquistada não devem expor identificadores diretos do usuário na URL; quando necessário, devem usar token opaco.

### Emails e comunicações

- o sistema deve enviar email de boas-vindas ou onboarding inicial, se esse fluxo for adotado;
- o sistema deve enviar email quando o usuário ganhar uma previsão;
- o sistema deve enviar email quando o usuário perder uma previsão, com tom de incentivo e competitividade;
- o sistema deve permitir outros emails transacionais ou motivacionais em momentos específicos;
- o sistema pode enviar comunicação relacionada a indicação ou bônus liberado;
- comunicações devem respeitar idioma preferencial do usuário quando disponível.

### Carteira, recarga e indicação

- o sistema deve prever recarga controlada de `Orynth Coins` para usuários com saldo muito baixo;
- recarga de `Orynth Coins` não deve alterar reputação;
- o sistema deve permitir indicação com bônus em `Orynth Coins` condicionado a ativação real do convidado;
- bônus de indicação não deve conceder reputação;
- a ativação mínima do convidado deve incluir ao menos a primeira previsão válida;
- o sistema deve prevenir autoindicação e bônus duplicado;
- o sistema pode conceder `Orynth Coins` por sugestão de mercado publicada;
- a recompensa por sugestão deve ser menor e mais controlada do que o saldo inicial padrão.
- o sistema deve manter carteira com saldo disponível e saldo bloqueado;
- o `stake` de uma previsão deve ser bloqueado imediatamente após a confirmação;
- o usuário não pode comprometer mais saldo do que possui disponível;
- o histórico de movimentações da carteira deve ser visível ao usuário.

### Feedback recompensável

- usuários autenticados ou visitantes identificados por nome/email podem enviar feedback para a plataforma;
- visitantes precisam concluir reCAPTCHA v2 checkbox quando a proteção anti-abuso estiver configurada;
- feedback deve entrar em fila de revisão administrativa;
- o admin decide se o feedback é válido, se será recompensado e qual valor de `Orynth Coins` será concedido;
- recompensa por feedback nunca concede reputação;
- toda recompensa de feedback deve gerar lançamento rastreável na carteira;
- o produto deve permitir exposição simples do histórico de feedback do usuário.

### Ranking

- ranking global por reputação;
- alternativa secundária por saldo ou desempenho em `Orynth Coins`;
- exibir posição do usuário atual;
- permitir exibição resumida de badges de destaque.

### Admin

- usar painel administrativo customizado como interface principal de operação;
- criar mercado;
- definir `market_type`;
- definir categoria e subcategoria/evento;
- configurar data, horário e fuso de encerramento automático;
- incluir ícone e imagem do mercado;
- cadastrar opções de mercado;
- editar mercado antes de publicação;
- resolver mercado pela opção vencedora;
- bloquear usuários;
- banir usuários;
- revisar sugestões de mercados enviadas por usuários;
- revisar feedbacks enviados por usuários;
- conceder ajustes e recompensas em `Orynth Coins` quando permitido;
- registrar fonte pública da resolução.

### Interface administrativa do MVP

A interface administrativa precisa ser tratada como parte essencial do produto, porque a qualidade dos mercados depende diretamente da criação, revisão e resolução corretas das perguntas.

Diretriz arquitetural:

- o painel principal deve ser customizado para os fluxos reais do negócio;
- Django Admin deve permanecer disponível apenas como suporte interno, inspeção técnica e troubleshooting;
- regras operacionais críticas não devem depender da UX padrão do Django Admin.

Capacidades mínimas esperadas:

- criar mercado em estado `draft`;
- editar pergunta, descrição, categoria, subcategoria/evento, tipo e data de resolução;
- editar ícone, imagem e configuração de encerramento;
- definir idioma base do mercado;
- cadastrar, ordenar, ativar e desativar opções do mercado;
- validar se mercados `binary` possuem exatamente duas opções válidas;
- validar se mercados `multiple_choice` possuem quantidade mínima e máxima de opções;
- publicar mercado quando estiver pronto para abrir previsões;
- fechar mercado para novas entradas quando necessário;
- permitir fechamento automático por data, horário e fuso sem intervenção manual;
- resolver mercado escolhendo a opção vencedora;
- registrar a fonte pública da resolução;
- visualizar dados essenciais do usuário para moderação;
- bloquear usuários temporariamente;
- banir usuários que descumprirem regras da plataforma;
- registrar motivo da ação administrativa aplicada ao usuário;
- moderar comentários quando necessário;
- revisar fila de sugestões de mercado;
- aprovar, editar, rejeitar ou publicar sugestões de usuários;
- vincular sugestão aprovada ao mercado publicado;
- conceder ou confirmar bônus em `Orynth Coins` ao autor da sugestão publicada;
- revisar fila de feedbacks;
- marcar feedback como recompensado, rejeitado ou apenas revisado;
- definir o valor da recompensa de feedback quando aplicável;
- cancelar mercado mal formulado ou impossível de resolver.

Visão operacional mínima esperada no painel:

- total de usuários cadastrados;
- total de usuários ativos em janela configurável;
- total de mercados criados, abertos, fechados, resolvidos e cancelados;
- total de previsões registradas;
- volume total de `Orynth Coins` negociadas;
- total de contratos ou posições negociadas;
- fila de sugestões pendentes;
- fila de feedbacks pendentes;
- visão consolidada de bloqueios, banimentos e contas desativadas;
- configurações operacionais da plataforma que afetem recompensas, recargas e moderação.

Campos esperados na tela de criação/edição:

- pergunta;
- descrição;
- categoria;
- subcategoria/evento;
- idioma base;
- `market_type`;
- ícone e imagem;
- data/hora de encerramento;
- fuso de encerramento;
- flag de encerramento automático;
- data de resolução;
- status;
- lista de opções;
- fonte de resolução, quando aplicável;
- observações administrativas internas, se decidirem incluir esse campo depois.

Regras de UX administrativa recomendadas:

- ao escolher `binary`, o admin deve ser induzido a trabalhar com duas opções fixas ou pré-preenchidas;
- ao escolher `multiple_choice`, a interface deve permitir adicionar e reordenar opções facilmente;
- a tela deve deixar explícito se o mercado ainda está em rascunho, aberto, fechado ou resolvido;
- a ação de resolver deve exigir confirmação e evidência de fonte;
- a interface deve impedir publicação de mercados inválidos;
- a interface deve deixar claro qual conteúdo é base e qual conteúdo é localizado, quando esse recurso evoluir.
- ações de bloqueio e banimento devem exigir confirmação explícita;
- o admin deve ver com clareza se a conta está ativa, bloqueada ou banida;
- o admin deve ver também se a conta foi desativada pelo próprio usuário;
- o histórico básico de moderação deve ser recuperável.
- conteúdos localizados devem ser administráveis a partir do idioma base, com rastreio de tradução assistida por IA quando esse recurso for usado.

---

## Requisitos Não Funcionais

- interface deve ser simples o suficiente para uma previsão em poucos cliques;
- a experiência deve parecer rápida mesmo sem SPA dedicada;
- páginas principais devem privilegiar navegação server-rendered com atualizações parciais;
- Alpine.js deve ser usado apenas para estados locais pequenos, sem virar framework principal da UI;
- a aplicação deve nascer compatível com internacionalização e expansão global;
- linguagem do produto deve evitar terminologia de aposta em dinheiro;
- regras de cálculo devem ser auditáveis no backend;
- regras de domínio sensíveis devem permanecer centralizadas no FastAPI;
- carteira e extrato devem ser consistentes mesmo em cenários de falha parcial;
- o fechamento automático de mercados deve ser idempotente e auditável;
- o painel administrativo principal deve ser desenhado para a operação do negócio, não apenas para CRUD técnico;
- segurança deve ser tratada como requisito de produto e reputação de plataforma, não apenas de infraestrutura;
- autenticação, autorização, integridade de dados e rastreabilidade de ações administrativas são requisitos centrais;
- ações críticas devem ser registradas de forma auditável;
- o sistema deve minimizar risco de manipulação indevida de mercado, fraude e uso administrativo incorreto;
- a confiança do usuário depende de clareza nas regras, rigor na resolução e proteção adequada da conta;
- integrações com provedores sociais devem seguir boas práticas de segurança, escopo mínimo e gestão segura de credenciais;
- envio de emails deve ser confiável, rastreável e compatível com preferências e idioma do usuário;
- resoluções devem deixar trilha mínima para revisão;
- sistema deve suportar expansão futura para social graph e tempo real.

---

## Contrato entre Web e Domínio

### Diretriz arquitetural

- Django serve HTML e orquestra interações do usuário;
- FastAPI expõe endpoints JSON de domínio;
- ações de produto não devem duplicar regra entre as duas camadas;
- Django pode adaptar resposta, navegação e mensagens de erro, mas não reimplementar a lógica central.

### Separação de responsabilidades críticas

- regras centrais de negócio devem ficar isoladas no backend de domínio;
- o monolito web não deve decidir cálculo de probabilidade, recompensa, reputação, resolução ou validações críticas;
- a camada web deve apenas coletar entrada, solicitar operações ao backend e exibir o resultado;
- comunicações por email devem seguir a mesma diretriz: a web não decide composição, disparo ou rastreamento de envio.

### Banco e fonte de verdade

- o FastAPI é o dono lógico do domínio e do banco principal;
- o Django pode ler dados para renderização e administração;
- escrita de regras sensíveis deve passar pelos contratos definidos no backend de domínio;
- evitar escrita livre e concorrente dos dois lados sobre autenticação, reputação, cálculo de mercado e resolução.

### Fronteira do subsistema de comunicações

- eventos de negócio como `prediction_won`, `prediction_lost`, `welcome` e similares devem nascer no backend de domínio;
- o backend de domínio entrega esses eventos ao subsistema de comunicações;
- o subsistema de comunicações decide template, idioma, provedores e rastreamento de envio;
- no MVP, esse subsistema pode existir como módulo isolado dentro do backend atual;
- a arquitetura deve permitir extração futura para serviço independente sem alterar a lógica de negócio principal.

### Segurança e confiabilidade

- autenticação e autorização devem ser consistentes entre web, admin e backend de domínio;
- operações críticas devem ter validação de permissão explícita;
- criação, edição, publicação, cancelamento e resolução de mercados devem gerar trilha de auditoria;
- mudanças administrativas precisam ser rastreáveis por usuário, horário e ação executada;
- a plataforma deve privilegiar integridade e confiabilidade mesmo quando isso aumentar um pouco o atrito operacional.

---

## API Inicial do FastAPI

### Auth

```http
POST /auth/register
POST /auth/login
POST /auth/logout
GET /auth/me
POST /auth/account-deletion-request
GET /auth/providers
POST /auth/social/{provider}/start
GET /auth/social/{provider}/callback
```

Responsabilidades:

- registrar usuário;
- validar reCAPTCHA no cadastro quando configurado;
- autenticar usuário;
- emitir token para cookie seguro;
- invalidar sessão quando necessário;
- registrar pedido de exclusão lógica da conta e impedir destruição física de histórico;
- iniciar e concluir autenticação com provedores sociais;
- retornar contexto do usuário autenticado.

### Users

```http
GET /users/{id}
GET /users/{id}/predictions
GET /users/{id}/comments
GET /users/{id}/referrals
GET /users/{id}/suggestions
GET /users/{id}/feedback
```

Responsabilidades:

- retornar perfil público ou autenticado;
- listar histórico de previsões do usuário;
- listar histórico público de comentários do usuário, se permitido pela política do produto;
- listar informações de indicação do usuário autenticado, quando aplicável;
- listar sugestões de mercados enviadas pelo usuário, quando aplicável;
- listar feedbacks enviados pelo usuário, quando aplicável.

### Wallet

```http
GET /wallet
GET /wallet/transactions
```

Responsabilidades:

- retornar saldo disponível, saldo bloqueado e totais históricos;
- listar extrato detalhado da carteira;
- expor referências de origem das movimentações;
- permitir leitura segura da economia individual do usuário.

### Markets

```http
GET /markets
GET /markets/{id}
POST /markets
PATCH /markets/{id}
POST /markets/{id}/resolve
```

Responsabilidades:

- listar mercados;
- retornar detalhe de mercado;
- criar e editar mercados para fluxos administrativos;
- cadastrar opções quando o mercado exigir;
- armazenar categoria, subcategoria/evento, mídia e configurações de fechamento;
- armazenar metadados necessários para idioma e futura localização;
- validar consistência estrutural entre `market_type` e opções cadastradas;
- resolver mercados com fonte pública e atualização de efeitos.

### Predictions

```http
POST /markets/{id}/predict
GET /markets/{id}/predictions
```

Request:

```json
{
  "market_option_id": "uuid-da-opcao",
  "stake": 100
}
```

Responsabilidades:

- validar mercado aberto;
- validar stake;
- validar saldo disponível suficiente;
- validar se a opção pertence ao mercado;
- registrar previsão;
- bloquear o `stake` na carteira;
- recalcular probabilidade.

### Referrals

```http
GET /referrals/me
POST /referrals/claim
```

Responsabilidades:

- retornar código, link e estado das indicações do usuário;
- registrar uso de código de convite no fluxo permitido;
- validar critérios de ativação antes de liberar bônus;
- impedir autoindicação e bônus duplicado.

### Market Suggestions

```http
GET /market-suggestions/me
POST /market-suggestions
GET /market-suggestions/{id}
POST /admin/market-suggestions/{id}/approve
POST /admin/market-suggestions/{id}/reject
POST /admin/market-suggestions/{id}/publish
```

Responsabilidades:

- permitir envio de sugestão autenticada ou guest identificado;
- validar reCAPTCHA para visitante quando configurado;
- listar sugestões do próprio usuário;
- permitir revisão administrativa;
- vincular sugestão aprovada a mercado publicado;
- controlar concessão de bônus em `Orynth Coins` quando a sugestão for publicada.

### Feedback

```http
GET /feedback/me
POST /feedback
POST /admin/feedback/{id}/review
POST /admin/feedback/{id}/reward
POST /admin/feedback/{id}/reject
```

Responsabilidades:

- permitir envio autenticado ou guest identificado de feedback;
- validar reCAPTCHA para visitante quando configurado;
- listar histórico do próprio usuário;
- permitir análise administrativa;
- permitir configuração manual de recompensa por feedback válido em `Orynth Coins`;
- registrar o crédito correspondente na carteira.

### Comments

```http
GET /markets/{id}/comments
POST /markets/{id}/comments
PATCH /comments/{id}
DELETE /comments/{id}
POST /comments/{id}/like
DELETE /comments/{id}/like
```

Responsabilidades:

- listar comentários de um mercado;
- criar comentário autenticado;
- permitir edição dentro das regras definidas;
- permitir moderação administrativa ou remoção autorizada;
- permitir `like` e `unlike` autenticados em comentários.

### Badges

```http
GET /badges
GET /users/{id}/badges
GET /badges/{id}/share
```

Responsabilidades:

- listar badges disponíveis na plataforma;
- listar badges conquistadas por um usuário;
- gerar metadados e link compartilhável para badge conquistada.

### Sharing

```http
GET /markets/{id}/share
GET /markets/{id}/result/share
GET /badges/{id}/share
```

Responsabilidades:

- gerar metadados e links compartilháveis para a pergunta;
- gerar metadados e links compartilháveis para o resultado resolvido;
- gerar metadados e links compartilháveis para badges;
- adaptar conteúdo mínimo ao idioma da página ou do usuário;
- gerar imagem social do card em URL acessível por crawler público quando houver `PUBLIC_SHARE_BASE_URL`/origem pública equivalente configurada;
- usar fallback visual legível para cards de mercado sem imagem, com iniciais derivadas de categoria/subcategoria/título.

### Email / Communications

```http
POST /communications/email/test
POST /communications/email/replay/{event_id}
```

Responsabilidades:

- não depender da camada web para lógica de envio;
- registrar e disparar eventos de comunicação;
- permitir reprocessamento administrativo controlado quando necessário;
- sustentar emails transacionais e de engajamento.

### Rankings

```http
GET /rankings
```

Responsabilidades:

- expor ranking por reputação;
- permitir variações futuras por saldo em `Orynth Coins` ou outros filtros.

### Páginas Django previstas

```http
GET  /
GET  /markets/{slug-or-id}
GET  /rankings
GET  /profile
GET  /categories/{slug}
GET  /suggestions/new
GET  /login
GET  /register
GET  /auth/{provider}
```

Observação: essas rotas servem HTML e consomem o FastAPI como backend de domínio. Interações parciais do feed, formulários e previsões devem usar HTMX sempre que fizer sentido.

---

## Fluxo de Resolução

```text
Mercado atinge condição de encerramento
↓
Scheduler/daemon fecha mercado automaticamente quando `close_at` for atingido
↓
Admin verifica fonte pública
↓
Admin resolve pela opção vencedora
↓
Sistema liquida saldo bloqueado e registra extrato
↓
Sistema calcula delta de reputação
↓
Sistema atualiza perfil dos usuários
↓
Sistema recalcula ranking
↓
Mercado passa a exibir resultado final
```

### Regras de resolução

- resolução deve usar fonte pública;
- admin deve registrar justificativa curta ou link;
- mercado mal formulado pode ser cancelado no futuro;
- previsões só são liquidadas uma vez.

---

## Métricas de Produto do MVP

### Aquisição e ativação

- usuários cadastrados;
- percentual de usuários que fazem a primeira previsão;
- tempo até primeira previsão.

### Engajamento

- previsões por usuário ativo;
- mercados vistos por sessão;
- retorno em 7 dias;
- percentual de usuários que visitam ranking e perfil.

### Qualidade do sistema

- distribuição de `Orynth Coins`;
- distribuição de reputação;
- concentração de previsões por categoria;
- taxa de mercados resolvidos no prazo;
- taxa de acerto média dos usuários;
- calibração simples entre probabilidade e resultado histórico.

---

## Testes e Cenários de Validação

### Autenticação

- registro de conta;
- registro de conta com reCAPTCHA válido quando configurado;
- login com emissão de cookie seguro;
- login social com provedores suportados;
- persistência da sessão entre navegações;
- acesso autenticado a páginas protegidas;
- bloqueio de acesso quando token expirar ou for inválido.

### Fluxo principal

- abrir feed;
- entrar em mercado;
- enviar previsão válida em mercado binário;
- enviar previsão válida em mercado de múltipla escolha;
- receber recarga de `Orynth Coins` quando elegível;
- indicar usuário e receber bônus quando a ativação for válida;
- sugerir pergunta e receber bônus se ela virar mercado publicado;
- enviar feedback e receber recompensa quando aprovado;
- enviar sugestão/feedback como visitante identificado, com reCAPTCHA quando configurado e sem recompensa até haver usuário associado;
- compartilhar pergunta ou resultado de mercado;
- receber e compartilhar badge conquistada;
- criar comentário em mercado;
- curtir e descurtir comentário;
- atualizar probabilidade após previsão;
- bloquear saldo ao registrar previsão;
- fechar mercado automaticamente na data/hora/fuso configurados;
- resolver mercado;
- refletir carteira de `Orynth Coins` e reputação no perfil e ranking.

### Integração Django ↔ FastAPI

- páginas renderizam com dados corretos vindos do backend de domínio;
- ações via HTMX disparam chamadas corretas ao FastAPI;
- erros do backend aparecem ao usuário de forma compreensível;
- falha de comunicação entre as camadas gera fallback ou mensagem clara.

### Admin

- criar mercado via painel administrativo customizado;
- cadastrar opções compatíveis com o tipo de mercado;
- configurar categoria, subcategoria, mídia e fechamento automático;
- editar mercado antes da publicação;
- publicar mercado apenas quando estiver válido;
- acompanhar visão consolidada de usuários, previsões, volumes e filas administrativas;
- resolver mercado pela opção vencedora;
- bloquear e banir usuários;
- moderar comentários;
- revisar sugestões de mercado;
- registrar fonte pública da resolução.

### Comunicações

- disparar email de ganho após previsão vencedora;
- disparar email de incentivo após previsão perdedora;
- disparar comunicação relacionada a bônus de indicação, se adotado;
- validar rastreamento de envio e falha de email;

### Falhas e bordas

- usuário sem permissão;
- mercado fechado;
- stake inválido;
- opção inválida ou não pertencente ao mercado;
- mercado publicado sem opções suficientes;
- mercado binário com estrutura inconsistente;
- inconsistência de idioma ou conteúdo administrativo incompleto;
- falha em autenticação social ou vínculo de conta externa;
- reCAPTCHA ausente, inválido, expirado ou configurado com tipo incorreto;
- falha no envio de email transacional;
- compartilhamento social com metadados incompletos;
- concessão incorreta ou duplicada de badge;
- recarga de `Orynth Coins` aplicada fora da política definida;
- tentativa de autoindicação;
- tentativa de bônus duplicado por indicação;
- sugestão duplicada, ambígua ou impossível de resolver;
- concessão incorreta de bônus por sugestão de mercado;
- concessão incorreta de bônus por feedback;
- tentativa de curtir o mesmo comentário múltiplas vezes;
- tentativa de prever sem saldo disponível suficiente;
- saldo bloqueado inconsistente com previsões em aberto;
- falha do scheduler no fechamento automático;
- conteúdo exibido em idioma divergente do `preferred_locale` do usuário;
- pedido de exclusão lógica sem bloqueio efetivo de acesso;
- token expirado;
- inconsistência ou indisponibilidade temporária do backend de domínio.

---

## Riscos do MVP

- fórmulas simples demais podem inflar `Orynth Coins` rapidamente;
- reputação multiplicando stake pode favorecer concentração excessiva;
- recarga de `Orynth Coins` ou bônus de indicação mal calibrados podem distorcer a economia do produto;
- fechamento automático mal implementado pode gerar mercados aceitando previsões após o prazo;
- carteira inconsistente compromete confiança do produto com rapidez;
- mercados mal escritos reduzem confiança no produto;
- fila de sugestões sem curadoria rígida pode degradar a qualidade editorial e gerar spam;
- poucas resoluções no começo enfraquecem o loop de recompensa;
- falta de camada social explícita pode limitar retenção, mesmo com boa mecânica;
- falhas de segurança ou resolução podem comprometer rapidamente a reputação da plataforma;
- ausência de base multilíngue desde o início pode gerar retrabalho alto na expansão internacional;
- a separação Django + FastAPI aumenta a complexidade de integração e deve ser mantida disciplinada.

---

## Decisões em Aberto

1. Um usuário pode prever várias vezes no mesmo mercado ou apenas uma?
2. O ranking principal será por reputação, saldo em `Orynth Coins` ou combinação dos dois?
3. Haverá fechamento automático antes da resolução ou o mercado aceita previsões até o limite?
4. As `Orynth Coins` retornam como `reward bruto` ou `lucro líquido + devolução de stake`?
5. Resolvido para o MVP: o feed oferece ordenações rápidas por tendência, encerramento, volume, novidade e favoritos editoriais; o destaque principal prioriza mercados publicados não cancelados por `view_count`, excluindo `draft` e `cancelled`, com desempate por data mais recente.
6. O perfil será público para todos os usuários desde o MVP?
7. Qual será o limite inicial de opções por mercado de múltipla escolha no MVP?
8. Quais serão os valores finais de recarga automática e bônus de indicação no MVP?
9. Qual será o valor final do bônus por sugestão publicada e o limite de sugestões por usuário no MVP?
11. Qual será o valor padrão e a política máxima de recompensa por feedback aprovado?

---

## Próximos Passos Recomendados

1. Fechar as decisões em aberto que afetam regra de negócio.
2. Transformar esta spec de produto em:
   - spec funcional do backend;
   - modelagem de banco;
   - fluxos de interface;
   - backlog priorizado do MVP.
3. Definir o contrato exato de autenticação entre Django e FastAPI.
4. Definir 10 a 20 mercados seed para teste manual do produto.
5. Prototipar feed, detalhe do mercado, perfil e ranking antes de implementar toda a lógica.

---

## Sugestões de Nome

- FuturePulse
- Predix
- Oraculus
- TrendCast
- Futura
- Forecastly
- PulsePredict
- HiveMind
- FutureFeed
- Clarity
