# Histórico misto

Continuação autorizada; execução inline, sem Git nesta pasta. Schema 2 mantido.
Fronteira = início da hora do corte de retenção bruta calculado no servidor.
Consultar agregados anteriores à fronteira e snapshots desde a fronteira,
sem sobreposição. Intervalos antigos sem agregados permanecem ausentes.
Snapshots preservados por incidentes antes da fronteira continuam na rota de
evidências, não entram duplicados na consulta histórica comum.
Identificar resolução e agregação por linha. Agregados parciais cruzando bordas
do período não entram no resumo IA; snapshots/buckets recentes permanecem.
Gráficos devem interromper lacunas conforme resolução local, inclusive no misto.
Limites atuais de intervalo e 100 mil snapshots preservados.

Etapas: baseline e RED; consulta/consumidores; revisão independente;
suíte completa, PostgreSQL isolado, compilações; documentação com provas.

Baseline: 102 passed/10 skipped/1 warning, 34.01 s.
Três testes consulta/IA RED → GREEN. Teste Node de resolução RED → GREEN.
Revisão independente: P2 hora externa e P2 banda invadindo lacuna; ambos
confirmados com SQLite/desenho canvas instrumentado, RED → GREEN no fix pass.
Caso de faixa sem duração no fim inclusivo também RED → GREEN.
PostgreSQL final: 111 aprovados/zero skips, oito integrações reais;
Chrome/HTTP: 15 verificações/zero erros JS. Relatórios em diretórios
2026-10-14-historico-misto-final (PostgreSQL) e
2026-10-14-historico-misto-final-http (screenshots).
Sem achados pendentes informados pela revisão; schema preservado.
Suíte final Windows 107 passed/11 skipped/1 warning, 43.82 s;
compileall app/scripts e node --check de todos os módulos exit 0.
Documentação atualizada, projeto Docker sem containers/redes após limpeza.
