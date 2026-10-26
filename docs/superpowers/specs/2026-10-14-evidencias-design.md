# Evidências de ocorrências

Preservar snapshots existentes no banco, sem duplicação nem mudança de schema.
Janela: first_seen menos 600 segundos até closed_at mais 600 segundos,
inclusive. Ocorrência ativa ou sem fechamento protege todo o período posterior.
Os 600 segundos são uma escolha inicial de engenharia, não requisito hospitalar.
Alarme de equipamento protege suas amostras; alarme de CLP sem equipamento
protege amostras de seus equipamentos. Ambos protegem snapshots do CLP.
Não purgar evidências automaticamente; ocorrências prolongadas aumentam o uso
do SSD. Não recuperar dados anteriormente apagados nem declarar cobertura completa.

Consulta GET autenticada por ocorrência, separando samples/points, paginada por
ID, até 1000 registros. Preservar valores, nulos, qualidade, fonte e versões.
Snapshots não equivalem a todas as aquisições Modbus. Intervalos ausentes continuam
ausentes. A proteção não modifica reconhecimento nem fechamento dos alarmes.
Agregação deve avançar entre horas com amostras, apesar de lacunas antigas.

Verificar SQLite e PostgreSQL reais, retenção repetida, escopos, limites, paginação,
qualidade inválida, alarme ativo sem normalização e autenticação.
