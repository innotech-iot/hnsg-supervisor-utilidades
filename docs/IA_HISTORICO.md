# Histórico tipado no assistente

Em Diagnóstico inteligente, selecione equipamento, período (1, 6, 24, 72 horas
ou 7 dias) e métrica. Estado atual preserva a consulta anterior. O histórico
oferece temperaturas de água para CAG/CAQ e métricas numéricas de UTA.

O servidor consulta e calcula os números antes de invocar a LLM opcional.
A tabela mostra média, mínimo, máximo e contagem de medições, independentemente
do texto gerado. A média é ponderada por **contagem da métrica**, não pelo tempo
nem pelo número de buckets. Booleanos e enumerações não recebem média.
Nulos e registros de qualidade inválida não entram nas estatísticas; em qualidade
parcial, somente métricas presentes entram. Contagens disponíveis não comprovam
cobertura temporal. Ausência de medição não significa zero nem normalidade.

API autenticada, com CSRF:

```json
{
  "asset_id": 16,
  "question": "Analise a temperatura de ida no período selecionado",
  "history": {"hours": 24, "metrics": ["supply_temperature"]}
}
```

Enviar via `POST /api/ai/explain`. `history` é opcional; `hours` deve ser inteiro
de 1 a 168, e `metrics` contém 1–6 nomes numéricos únicos compatíveis com o tipo.
Campos adicionais e SQL são rejeitados. A pergunta livre não escolhe consultas
nem altera o intervalo: o campo estruturado controla o escopo. O período termina
no relógio do servidor, com timestamps Unix `start`/`end` na evidência auditada.
A UI apresenta esses horários no fuso do navegador.

A consulta usa o histórico existente, limitado a 100 mil snapshots, com redução
em buckets quando necessário. Se começar além da retenção bruta configurada,
combina agregados horários antigos com snapshots/buckets recentes: somente
horas agregadas completas dentro do intervalo entram no resumo. A sequência
detalhada das horas antigas permanece indisponível; a hora corrente utiliza
snapshots existentes. O aviso de agregação acompanha os resultados. Partição,
limites e lacunas em HISTORICO_MISTO.md.

As evidências incluem estado atual e bloco `history` separado. A resposta
determinística histórica descreve o período solicitado, sem usar a qualidade
atual como substituto da qualidade histórica. A LLM recebe apenas o resumo
calculado e documentos aprovados, sem ferramentas, acesso SQL ou comandos.
Validação de formato/fontes não valida toda conclusão gerada pelo modelo.

Schema permanece 2; não exige migração. Testes e resultados em VERIFICACAO.md.
Modelo Ollama real, carga prolongada e comportamento no Raspberry continuam
pendentes; a consulta não libera ambientes ou comprova conformidade.
