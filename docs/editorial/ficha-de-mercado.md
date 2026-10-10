# Ficha editorial de mercado

Modelo v1.5 para o campo único `editorial_record.document`. O agente prepara este texto; o revisor humano o confere, corrige e registra sua decisão no Admin Ops. O sistema registra autor, data, revisão e hash separadamente. Preencher esta ficha não publica um mercado.

## CONTEXTO E DUPLICIDADE

Descrever o evento futuro e por que é relevante. Registrar onde e quando foram buscados mercados equivalentes, quais foram encontrados e as limitações da busca. Distinguir sinais internos, fontes externas e inferências do preparador.

## PERGUNTA, REGRAS E PRAZOS

Registrar a pergunta, alternativas e critério objetivo de cada resultado; indicar os horários, o fuso, a divulgação esperada e a razão do encerramento. Conferir correspondência com os campos públicos do mercado e avisos necessários.

Quando a divulgação for conhecida, usar uma linha `Anúncio esperado: AAAA-MM-DDTHH:MM:SS±HH:MM`. O fechamento do mercado precisa ser anterior a esse horário. Se não houver horário conhecido, usar `Anúncio esperado: não informado` e descrever a limitação.

## FONTES E EVIDÊNCIAS

Para cada fonte, registrar URL exata, finalidade, data/hora da consulta, informação encontrada e quem realizou a consulta. Informar se a fonte foi acessada ou permanece por verificar. Não apresentar relato do agente como conferência humana.

## CONTINGÊNCIAS E RESPONSÁVEL

Definir o tratamento de adiamento, cancelamento, divergência, dado corrigido e fonte indisponível. Identificar responsável pelo acompanhamento e apuração, agenda e substituto quando cabível.

## PENDÊNCIAS E CONCLUSÃO

Listar pendências e limites reais; concluir se recomenda aprovação, devolução ou rejeição e por quê. Devolução e rejeição devem indicar a correção ou razão dentro deste mesmo texto.

Para aprovação, resolver cada pendência e usar `Pendências para aprovação: nenhuma` como primeira linha de conteúdo desta seção, seguida da conclusão. Enquanto houver pendência, descrevê-la no lugar dessa linha; apenas acrescentar a declaração ao fim de uma lista de pendências não libera a aprovação. Essa declaração não substitui a conferência humana das fontes e evidências.

O [checklist E01–E11](checklist-de-publicacao.md) orienta a leitura do documento, sem campos ou confirmações individuais no parecer. Para aprovar, o humano confirma uma vez que revisou o conteúdo, conferiu as fontes necessárias e não encontrou pendências. A decisão e a publicação são ações distintas.
