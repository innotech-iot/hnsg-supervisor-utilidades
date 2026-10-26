# Evidências persistidas dos alarmes

A retenção comum de histórico não apaga snapshots dentro da janela de uma
ocorrência: **10 minutos antes do início, todo o período ativo e 10 minutos
depois do fechamento**. Os 10 minutos são uma escolha inicial de engenharia,
não um limite hospitalar aprovado. Reconhecer ou avaliar não fecha a ocorrência.
Sem fechamento válido, a proteção permanece aberta, inclusive em registros
legados incompletos. Qualidade vencida/desconhecida e valores nulos são preservados.

Alarme associado ao equipamento protege suas amostras. Alarme geral de CLP
protege as amostras dos equipamentos associados a esse CLP. Os snapshots de
pontos do CLP são preservados nos dois casos. O escopo de CLP segue o cadastro;
reassociação futura precisará preservar a associação histórica explicitamente.

São snapshots já persistidos, não todas as aquisições Modbus. Amostras seguem
o intervalo configurado de histórico; snapshots completos de pontos são gravados
uma vez por minuto. Dados previamente apagados e lacunas não são reconstruídos.
Não há declaração automática de cobertura completa. Alarmes antigos podem ter
somente resumo ou parte da janela disponível.

Na Central de alarmes, abra **Inspecionar** e escolha **Amostras do equipamento**
ou **Pontos do CLP**. A visualização apresenta 100 registros por página, incluindo
fonte, qualidade, versões e nulos existentes. O resumo do detector continua separado.

API de leitura, com sessão autenticada:

```text
GET /api/alarms/{id}/evidence?kind=samples&after=0&limit=200
GET /api/alarms/{id}/evidence?kind=points&after=0&limit=200
```

`limit`: 1–1000. Para continuar, envie `after=next_after` quando não nulo.
A ordem é por ID de persistência, não por horário; novos registros podem aparecer
em consultas posteriores de uma janela aberta. `start`/`end` descrevem a janela
solicitada; `end=null` indica proteção aberta. `coverage=not_verified` não afirma
que todas as amostras existam. A consulta histórica comum continua usando agregados
para intervalos antigos; consulte esta rota para a evidência preservada.

Não há purga automática das evidências por idade. Elas usam as tabelas existentes
e os backups comuns, sem duplicar snapshots ou alterar o schema 2. Ocorrências
prolongadas e recorrentes aumentam o consumo do SSD; uma política de descarte
auditado/exportação e limites de capacidade deve ser definida antes da operação.
Agregados continuam com retenção própria: dados brutos protegidos mais antigos
que esse prazo são consultáveis como evidência, sem recriação infinita de agregados.

Validação: testes de retenção/escopo/limites/paginação em SQLite, caso real
PostgreSQL e ensaio Chrome/HTTP com fixtures. Evidências e resultados em VERIFICACAO.md.
