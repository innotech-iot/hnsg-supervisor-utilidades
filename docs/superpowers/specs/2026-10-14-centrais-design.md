# CAG, CAQ e migração explícita

Objetivo autorizado: ampliar a base existente para 14 UTAs, CAG no CLP 2 e CAQ no CLP 3, preservando cadastros e proteções.

## Dados e atualização

Schema 2 acrescenta `assets.kind` (`uta`, `cag`, `caq`). IDs 1–14 permanecem intactos; IDs 15 e 16 identificam CAG e CAQ. Acrescentar CLP 3 desabilitado e sem IP. Não alterar configurações existentes ou confirmar conexões automaticamente. Conflitos com IDs reservados bloqueiam a migração.

Novos bancos recebem schema 2. Bancos schema 1 bloqueiam startup com instrução de migração. `scripts/migrate.py` verifica modo e versão, usa o mesmo lock da aplicação e aplica a revisão em transação; não conecta CLPs. Versão desconhecida e banco sem versão não são adotados. A revisão usa SQLAlchemy já instalado, sem dependência adicional. A operação real exige backup e autorização operacional; nesta execução apenas bancos temporários serão migrados.

## Runtime e API

Buffers, persistência, retenção e tarefas usam o cadastro, com uma tarefa independente por CLP. UTAs preservam simulação e detectores existentes. Centrais não recebem leituras de UTA nem diagnóstico de ventilação. Dados desconhecidos permanecem desconhecidos; retorno da bomba não certifica funcionamento da central inteira. Catálogo de centrais contempla temperaturas de ida/retorno e comando/retorno de bomba, sujeitos à associação explícita e confirmação de unidade/escala. Sem setpoints ou limites normativos presumidos. Comandos demo continuam restritos às UTAs.

Vínculos só aceitam semânticas compatíveis com o tipo e CLP do equipamento. Históricos, CSV, manutenção, documentos e IA aceitam as centrais; existência é validada no servidor. Readiness em live exige os três CLPs.

## Interface

Preservar 14 cartões de UTAs e adicionar seção de centrais. Filtros e seletores de CLP derivam do estado; navegação expandida inclui CAG/CAQ. Tela central mostra medições de água, retorno de bomba, qualidade, alarmes e dois gráficos; não usa o sinótico de ar nem oferece ajuste simulado. Pontos e cadastro exibem o nome real do equipamento. Temas e recursos locais são preservados.

## Aceite

Testes: migração idempotente e atômica, recusa de modo/versão/conflitos, restauração de backup v1 seguida da migração, preservação de usuário/configuração/histórico/auditoria; três workers; ausência de simulação de centrais/live; vínculos e histórico do CLP 3; limites de permissão e comandos preservados. Suíte, compileall e sintaxe JS devem passar. Ensaio visual depende de navegador e ambiente de teste disponíveis; registrar bloqueios reais.
