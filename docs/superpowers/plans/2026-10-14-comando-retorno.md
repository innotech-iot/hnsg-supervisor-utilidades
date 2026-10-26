# Divergência de comando/retorno de ventilador

Continuação autorizada do backlog. Execução inline, sem Git na pasta.
Schema 2 preservado: flag nova no JSON do perfil, padrão false inclusive demo.

Escopo: somente UTA, perfil validado e fan_confirmation_validated explícito.
Flag representa revisão da semântica/relação dos dois pontos; não valida hardware.
Pontos individuais ainda dependem de mapeamento validado para coleta live.
Somente modo automático 1, qualidade good e valores 0/1 exatos. Não inferir
retorno por comando, vazão, corrente ou estados ausentes. Flag ausente desabilita.

Resultado independente das malhas térmicas: mismatch, agreement, pending,
unknown. Exigir par constante durante settling_seconds+persistence_seconds,
duas ou mais leituras, intervalos crescentes até max_gap_seconds, mesmas versões.
Fechar alarme somente após agreement persistente válido. Unknown/pending,
dados vencidos, modo manual/parado e desabilitação não normalizam a ocorrência.
Alarme consultivo warning, sem afirmar causa física ou comandar PLC.
Preservar início da divergência, duração, contagem, valores, versões e limites.

Etapas: baseline; testes RED de regra/normalização; detector e runtime;
campo de perfil/coverage/UI; revisão independente; suíte, PostgreSQL e Chrome;
documentação de evidências e limitações.

Baseline: 107 passed/11 skipped/1 warning, 42.10 s.
Primeiro RED: 3 falhas esperadas → detector/runtime → GREEN.
Revisão independente: P1 cache falso, P1 UI, P1 proveniência/configuração,
P2 início da evidência. Correções no fix pass, com testes de coleta reais,
formulários Node, updates API e buffer limitado. Cache/versões, UI e transições
API reproduzidos RED → GREEN; recuperação mantém prova e initial permanece.
Proveniência demo/revisão e aquisições escalonadas também RED → GREEN.
Capacidade nominal do buffer testada RED → recusa 422 → GREEN.

Concluído: 23 testes novos de detector/runtime/API, dois Node, uma integração
PostgreSQL. Final Windows 132 passed/12 skipped/1 warning (37.34 s), Linux
135 passed/zero skips, nove integrações reais; Chrome/HTTP 15 fluxos/zero erros JS.
Compileall e node --check exit 0. Artefatos: comando-retorno-completo (PostgreSQL)
e comando-retorno-final-http (screenshots). Limites documentados; nenhuma
alteração de schema, PLC ou infraestrutura operacional. Sem achados pendentes
do review. Não executar rereview: regressões e suíte confirmam as correções.
