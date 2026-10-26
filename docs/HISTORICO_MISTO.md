# Histórico atravessando a retenção bruta

Consultas que incluem dados antigos e recentes combinam agregados horários e
snapshots/buckets. A fronteira é o início da hora que contém o corte de retenção
bruta, calculado no servidor. Antes dela, a consulta utiliza agregados; a partir
dela, usa snapshots disponíveis. Um dado não entra pelas duas fontes.

Cada linha informa `aggregation` (`hourly`, `raw` ou `bucketed`) e
`resolution_seconds`. Agregados/buckets também informam `interval_end`.
O campo geral `aggregation=mixed` indica que a resposta contém as duas partes;
se somente uma tem registros, mantém sua classificação. `raw_boundary` registra
a fronteira utilizada. Fontes, qualidade e versões de snapshots são preservadas.

Horas agregadas que se sobrepõem parcialmente ao período podem ser exibidas
no gráfico com sua extensão real, mas horas inteiramente externas são excluídas.
As estatísticas do assistente usam somente horas agregadas completas dentro
do período, junto aos snapshots/buckets recentes. Uma hora parcial não é
proporcionalmente repartida, pois isso inventaria a distribuição das medições.

A resolução local determina as interrupções do gráfico. Faixas mínimo/máximo
ocupam o intervalo real do agregado; não pintam a lacuna anterior. Horas com
qualidade incompleta recebem marca de lacuna e não são desenhadas como sequência
contínua válida. Médias não representam amostras originais.

Sem agregado antigo ou snapshot recente disponível, a ausência permanece.
Não preencher zero, interpolar ou recuperar dados apagados. Snapshots antigos
preservados por incidentes continuam acessíveis pela rota de evidências; não
duplicam a consulta histórica comum. Mudanças na retenção não recuperam dados
eliminados por uma política anterior.

Mantidos: intervalo máximo de 366 dias e limite de 100 mil snapshots consultados.
A redução em buckets aplica-se à parte recente; a parte horária mantém sua
resolução. Portanto o limite de pontos recente não é um teto para a soma de
agregados e buckets. Schema permanece 2; sem migração ou gravação industrial.

Validação SQLite/PostgreSQL e Chrome/HTTP em VERIFICACAO.md.
