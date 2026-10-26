# Consulta histórica tipada do assistente

Escopo autorizado: continuação do backlog de diagnóstico. Execução inline.
Sem Git/worktree nesta pasta. Schema permanece 2.

Contrato: campo opcional history={hours: inteiro 1–168, metrics: 1–6 nomes únicos}
em AIQuestion. Validar métricas numéricas pelo tipo de equipamento no servidor;
booleanos e enumerações não recebem média. SQL e ferramentas continuam ausentes
da LLM. Intervalo relativo termina no horário do servidor, explicitado na resposta.
Usar histórico existente com seus limites, extrema/contagens e avisos de agregação.
Média ponderada por contagem da métrica, nunca por número de buckets.
Nulos/qualidade inválida não entram nas estatísticas. Ausências não viram zero.
Cobertura temporal não é certificada pela existência de snapshots. Em agregados,
não recuperar sequência detalhada nem hora corrente não consolidada.
Resposta determinística histórica descreve o período solicitado, separada do
estado atual. Contexto resumido e auditado; UI oferece período/métrica explícitos.

Etapas: testes RED; backend e UI; testes completos/compilação/JS; revisão
independente; atualização de STATUS e VERIFICACAO. Não instalar modelo nem
alterar banco/PLC/serviços operacionais.

Baseline Windows: 89 passed/9 skipped/1 warning, 26.38 s.
RED: duas consultas válidas rejeitadas por campo ausente; GREEN após implementação.
Recorte de hora cruzando início: teste RED → filtro de horas completas → GREEN.
13 testes novos: raw/hourly/bucketed, whitelist, vazio, limites, auditoria/CSRF.
Revisão independente sem achados importantes; ensaio próprio do revisor com
1203 snapshots confirmou bucketed. Esse cenário está coberto na suíte por
1300 snapshots (teste acrescentado antes da recomendação final do revisor).
Chrome/HTTP: 14 verificações aprovadas, zero erros JS; form histórico e resultado
inspecionados no screenshot. PostgreSQL/Linux: 106 aprovados, zero skips,
incluindo 7 integrações reais; recursos temporários removidos.
Suíte final Windows: 102 passed/10 skipped/1 warning, 33.33 s. Compileall e
node --check exit 0. STATUS, VERIFICACAO, README e handoff atualizados.
