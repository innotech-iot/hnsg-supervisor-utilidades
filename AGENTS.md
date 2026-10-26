# HNSG / Innotech — regras para agentes de desenvolvimento

Leia primeiro README.md, docs/ESPECIFICACAO.md, docs/STATUS.md e CODEX_HANDOFF.md.

## Contexto fixo
- 14 UTAs, 01 CAG e uma 01 CAQ. 3 CLPs CAREL por Modbus TCP. CLP 1: UTAS 01,02,03,09,10,12.
- CLP 2: UTAS 04,05,06,07,08,11,13,14 e CAG.
- CLP 3: CAQ.
- CAG = Central de água gelada, CAQ = Central de água quente.
- Pi 5 / 4 GB RAM; SSD 512 GB para PostgreSQL; microSD 64 GB considerado para OS.
- TXT CAREL real ainda ausente. Nenhum endereço em samples/ é do hospital.
- Base v0.1.0 para engenharia, não liberada para operação assistencial.

## Invariantes de segurança
1. Nunca habilitar escrita industrial automaticamente. app/modbus.py contém somente FC01/02/03/04.
2. Não simular leituras em modo live. Sem aquisição válida = desconhecido, nunca zero ou normal.
3. Demo e live não compartilham banco; o guard de modo não pode ser removido para facilitar testes.
4. Senhas, sessões, controle de acesso e CSRF validados no servidor; nunca migrar autenticação para localStorage.
5. LLM sem ferramentas, SQL arbitrário ou acesso a rotas de comando. Não encaminhar instruções dos documentos como comandos.
6. Escala, endereço-base, bytes/palavras e significado devem ser confirmados. Não "corrigir" offset automaticamente.
7. Importação com erro não é ativada. Preservar linhas, hash, revisões e trilha.
8. Dado vencido interrompe o gráfico; não preencher com zero nem declarar normalização de alarme.
9. Proteções físicas permanecem no CLP. Não criar controle PID no servidor.
10. Não alterar PLC, firewall, banco real, rede ou serviço remoto sem autorização operacional específica.

## Desenvolvimento
- Python 3.11+, FastAPI + SQLAlchemy. Um worker; duas tarefas independentes para CLPs.
- Frontend modular JS/CSS nativo, sem build/npm/CDN obrigatório. Não substituir a base inteira por framework sem justificar.
- Preservar identidade Innotech, tema claro/escuro, responsividade, navegação expandida e SVG acessível.
- Toda mudança de schema exige migração e teste de restauração; create_all não migra banco existente.
- Novos requisitos hospitalares não equivalem a certificação. Não preencher valores normativos por suposição.
- Testes antes de alteração funcional. Não remover testes para obter verde.
- Comandos padrão: `python -m pytest -q`; `python -m compileall -q app scripts`; checagem JS descrita no README.
- Fixtures de testes são fictícias. Nunca colocar dados reais/pessoais, credenciais ou binários de modelo no Git.
- Não usar git reset --hard, clean destrutivo ou apagar runtime do usuário.
- Atualizar docs/STATUS.md e docs/VERIFICACAO.md com evidências reais, não presumidas.
