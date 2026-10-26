# Continuação no Codex

## GitHub — 26/10/2026

Repositório: https://github.com/innotech-iot/hnsg-supervisor-utilidades
Branch principal: `main`. Pasta local inicializada como repositório Git.
Não versionar runtime, ambientes Python, bancos, segredos ou chaves privadas.

## Implantação DEMO na Raspberry — 22/10/2026

Simulador completo opt-in `DEMO_FULL=true`, cenário normal/faults, script
`scripts/populate_demo.py`. Todos os papéis funcionais dos 16 equipamentos são
sintéticos; não corresponde ao mapa CAREL real. Demo tradicional preservada.
Deploy autorizado em `/opt/hnsg`, serviço `hnsg-demo` ativo/habilitado, loopback
8016, venv/runtime SQLite DEMO em `/mnt/innotech-usb/hnsg`. USB temporário
autorizado; SSD 512 GB ausente. Não migrar PostgreSQL nem habilitar LIVE por
causa dessa instalação. Tailscale Funnel 8443 configurado, publicação privada
443 → 5000 preservada. Ver `docs/DEMO_RASPBERRY.md`, STATUS e VERIFICACAO para
evidência de DNS público, credencial inicial protegida e limites do ensaio.

## Ponto de partida
Este projeto não é apenas um layout. Há API autenticada, persistência, simulador, coletor Modbus TCP **somente leitura**, importador estrito, regras de diagnóstico, interface de operação e testes. A validação contra os CLPs CAREL físicos, TXT real, PostgreSQL/ARM64 e a infraestrutura hospitalar continua pendente.

Abra a pasta inteira `hnsg-supervisorio` no editor/ambiente do Codex. Não abra apenas index.html e não peça uma reconstrução do zero. Execute a demonstração e leia AGENTS.md antes de alterar arquivos.

## Continuação de 14/10/2026 — cadastro ampliado

Schema atual: **2**. Migração explícita 1→2 em `scripts/migrate.py`/`docs/MIGRACOES.md`; não migrar banco operacional sem autorização específica. IDs 1–14 preservados; CAG=15/CLP 2, CAQ=16/CLP 3. Bancos novos recebem 16 equipamentos e três CLPs; bancos legados exigem backup e atualização explícita. Cadastro novo não habilita conexões.

Coleta, buffers, histórico/CSV e retenção usam o cadastro. UTAs preservam demonstração e detectores; CAG/CAQ têm catálogo próprio de água, tela e navegação, sem simulação de UTA e sem perfil/detector de ventilação. Valores e operação integral da central continuam desconhecidos até comissionamento. Falta sequência real, sinótico físico e detectores específicos. Mapeamento deve confirmar unidades/escala; não inferir endereços. Próximo trabalho principal: dialeto dos três TXT reais e ensaio PostgreSQL/Raspberry.

## Prompt sugerido para começar

Etapa PostgreSQL acrescentada: harness opcional `scripts/verify_postgres.py`, rede interna sem portas publicadas, banco/role de fixture e restore em banco distinto. Migração e recuperação testadas com PostgreSQL 16.15 em Linux x86_64; ver POSTGRES_TESTES.md e VERIFICACAO.md. Senha da URI/query não entra mais no argv de pg_dump. Próximas validações de implantação: ARM64/Raspberry, armazenamento físico e carga prolongada, além dos três TXT reais. Pipeline PostgreSQL incluído, mas não executado remotamente.

```text
Continue este repositório HNSG / Innotech, preservando a implementação existente.
Leia AGENTS.md, README.md, docs/ESPECIFICACAO.md, docs/STATUS.md,
docs/VERIFICACAO.md e CODEX_HANDOFF.md. Execute os testes e a demonstração
antes de modificar o código. Não recrie o projeto nem remova proteções.

O alvo é Raspberry Pi 5 com 4 GB de RAM, SSD de 512 GB para PostgreSQL,
14 UTAs, CAG e CAQ em três CLPs CAREL via Modbus TCP. CLP 1 contém as UTAs
01,02,03,09,10,12; CLP 2 contém 04,05,06,07,08,11,13,14 e CAG; CLP 3 contém CAQ.

Primeiro faça uma revisão da base e apresente falhas concretas com testes.
Em seguida, execute o primeiro item do backlog que seja possível sem os
TXT reais. Quando eu anexar os TXT, implemente um adaptador específico,
com fixture anonimizada e testes de endereçamento, tipos, escala e acesso.
Mantenha a leitura industrial e a demonstração separadas. Não libere escrita
nos CLPs nem publique acesso remoto sem meu pedido e a validação operacional.
Preserve as telas, os temas, a navegação em modo expandido e os testes.
Atualize a matriz de implementação e registre o que foi de fato testado.
```

## Ordem de trabalho recomendada

### 1. Auditar a base e testar no alvo
Rodar a suíte e a UI com transporte HTTP normal. Repetir instalação limpa em Windows e Linux ARM64. Medir memória/CPU, latência da leitura e consultas durante 72 h em bancada com o volume real de tags. O prazo de 72 h é uma proposta de ensaio, não uma homologação. Testar PostgreSQL com psycopg e a migração transacional existente; acrescentar revisões explícitas antes de futuras alterações de schema. Nenhum pipeline remoto foi executado nesta entrega.

### 2. Implementar o dialeto CAREL efetivo
Receber um TXT por CLP (três arquivos), preservar original e hash. Identificar versão da ferramenta, cabeçalhos, encoding, áreas, signedness, escala e endereçamento. Não inferir o mapa do sample. Acrescentar adaptador dedicado ao importer, fixture e testes de linhas desconhecidas. Confirmar fisicamente o cadastro informado no AGENTS.md. Caso distribuição difira, criar ferramenta administrativa auditada de reassociação: não mudar apenas a constante de seed de um banco existente.

### 3. Comissionar pontos e sinóticos
Associar medição, setpoint efetivo, comando, retorno, modo e alarmes por UTA. Confirmar enumeração dos modos (o catálogo desta base pressupõe 0=parado, 1=automático, 2=manual) e criar transformação explícita se o CAREL usar outra. Identificar pressão de sala versus pressão no duto. Validar componentes/ordem física no sinótico por equipamento. Os 14 usam hoje um desenho indicativo comum; não é representação as-built.

### 4. Confiabilidade e segurança hospitalar
Racionalizar alarmes, prioridades, tolerâncias, atraso/histerese e retorno ao normal com responsáveis. Implantar sinalização independente e monitor externo com destinatários/escalonamento reais. Implementar shelve/silêncio com expiração e auditoria apenas se aprovado. Testar nobreak, SSD ausente, queda do switch, recuperação e restauração externa. Aprovar rede segmentada, TLS e autenticação remota multifator com a TI.

### 5. Diagnóstico

Comando/retorno do ventilador UTA implementado com opt-in false por padrão,
perfil validado e aquisições binárias frescas em automático. Cache não conta
como aquisição; mudanças de revisão interrompem continuidade. Fechamento exige
concordância persistente e preserva recovery/initial. Ver COMANDO_RETORNO_VENTILADOR.md.
Não aplicar a bombas/centrais nem inferir contatos/causa sem comissionamento.

Consulta histórica tipada concluída: campo opcional history em /api/ai/explain, período 1–168 h e whitelist numérica por equipamento. Resumo calculado/auditado pelo servidor e tabela na UI; LLM recebe dados sem SQL/ferramentas. Consulta mista agregado/bruto implementada com fronteira explícita, resolução por linha e lacunas preservadas; ver IA_HISTORICO.md e HISTORICO_MISTO.md. Modelo real e avaliação no alvo permanecem pendentes.

Etapa de evidências persistidas concluída em 14/10/2026: retenção protege janela de 10 minutos antes/todo o período ativo/10 minutos após fechamento, nas tabelas existentes. API autenticada e inspeção paginada na UI; SQLite/PostgreSQL real e Chrome/HTTP testados. Ver EVIDENCIAS_ALARMES.md. Não recupera dados apagados nem armazena todas as aquisições; capacidade e descarte auditado permanecem pendentes.
Calibrar regras e medir falsos positivos por modo. Acrescentar detectores de vazão, pressão, comutação e comando/retorno com dados suficientes. Preservar janelas brutas de evidências por ocorrência antes de reduzir retenção. Implementar medições de desempenho do controle. Não usar somente ausência de alarme como indicador de saúde. Adicionar consultas históricas tipadas (sem SQL livre) para perguntas do assistente.

### 6. Ollama/RAG
Hoje: recuperação lexical de textos aprovados + estado/ocorrências, integração /api/generate opcional, desligada por padrão. Nenhum modelo foi instalado ou testado nesta entrega. Testar modelo pequeno e limites no alvo; preferir LLM em máquina separada se afetar a coleta. Futuro embedding/RAG semântico deve ser explícito, versionado e avaliado contra casos conhecidos. Criar isolamento de rede/processo e contas de menor privilégio: hoje a lógica consultiva é módulo da API, embora o servidor Ollama seja externo.

### 7. Escrita industrial: etapa separada
Não existe implementação de escrita a ser simplesmente habilitada por flag. Desenvolver somente após autorização: whitelist de pontos, limites por equipamento, autorização local/remoto, intertravamentos do CLP, confirmação, TTL, resultado verificado por leitura, idempotência e auditoria. Separar reconhecer alarme local da aplicação de reset físico no PLC. Nunca delegar esta função à LLM.

## Limitações importantes do estado atual
- Perfis não são limites hospitalares aprovados. Não há certificação/conformidade automática.
- Retenção inicial: brutos de snapshots por ~7 dias (horas consolidadas), agregados horários por 365 dias; janelas de ocorrências preservam snapshots existentes além desses prazos, sem purga automática. Lacunas e dados já apagados não são recuperados.
- SQL/JSON, migração e backup/restauração foram testados com SQLite e PostgreSQL 16.15 em contêiner Linux x86_64. Raspberry/ARM64 e instalação final continuam pendentes. Guard de worker é local ao diretório, não HA/distributed locking.
- RAG não interpreta PDF automaticamente: cadastrar textos aprovados, ou adicionar ingestão controlada.
- Visual de alarmes sem entrega externa, som garantido, escalonamento ou monitor de falha independente instalado.
- Rotina de backup faz checksum e estrutura; restauração integral deve ser testada separadamente.
- Não há relatórios de conformidade por sala, renovação/hora ou pressão sem sensores e referências aprovadas.
- Biblioteca mínima própria de gráficos: zoom, pausa, série e min/máx; cursores sincronizados, anotações em pontos e comparativo multi-UTA são melhorias futuras.
