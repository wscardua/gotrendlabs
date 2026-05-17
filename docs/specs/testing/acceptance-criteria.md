# Critérios de Aceite

Cada feature deve explicitar:

- comportamento observável esperado
- erros relevantes e feedback esperado
- estados de domínio envolvidos
- camadas impactadas
- evidência mínima de teste

## Regras globais

- uma feature só pode ser marcada como `validada` quando seus critérios de aceite estiverem cobertos por testes ou checagens equivalentes
- uma mudança de spec pode tornar uma implementação `defasada_pela_spec` mesmo sem regressão funcional imediata
- contratos compartilhados alterados exigem revisão dos testes das features dependentes
- todo workflow concluído deve declarar se testes foram executados, atualizados ou deixados como pendência registrada
