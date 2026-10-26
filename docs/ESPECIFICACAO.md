# Supervisório HNSG — especificação de entrega

## Escopo confirmado
Servidor web local para 14 UTAs, uma CAG e uma CAQ em três CLPs CAREL Modbus TCP. CLP 1 atende 01, 02, 03, 09, 10 e 12; CLP 2 atende 04, 05, 06, 07, 08, 11, 13, 14 e CAG; CLP 3 atende CAQ. Alvo: Raspberry Pi 5 4 GB, SSD 512 GB para banco e microSD 64 GB. Navegação contínua em modo expandido, identidade Innotech (grafite, verde, ciano), temas claro/escuro, dashboard e tela por equipamento, dados atuais e históricos, alarmes, auditoria, manutenção, saúde do sistema e IA consultiva opcional.

## Decisões desta entrega
- Modo `demo` explicitamente sinalizado e persistido em banco separado; modo `live` nunca gera dados artificiais.
- Backend FastAPI/Python 3.11+, SQLAlchemy; SQLite no desenvolvimento, PostgreSQL no alvo. Frontend HTML/CSS/JavaScript modular, sem CDN, sem Node na Raspberry. O React anteriormente sugerido não é necessário nesta base; componentes e navegação permanecem isolados para evolução no Codex.
- Coleta independente do navegador, um processo e uma tarefa independente por CLP (três no cadastro atual). Driver TCP de leitura estrita FC01/02/03/04, com testes em servidor local emulado. Sem varredura de rede. Escrita industrial indisponível nesta entrega: exige TXT real, matriz aprovada e comissionamento. Ajustes de demonstração somente mudam simulador de UTAs.
- Schema 2 diferencia UTA, CAG e CAQ; a migração 1→2 é explícita e transacional. Centrais começam sem dados, sem perfil de ventilação e sem sequência física presumida; retorno de bomba não certifica operação da central. Dados de água dependem de associação e validação dos pontos reais.
- Importador com prévia, hash e revisão. Formato CAREL real NÃO foi fornecido. Adaptador genérico delimitado é explicitamente um contrato de desenvolvimento, não alegação de compatibilidade universal CAREL. Não interpretar silenciosamente linhas desconhecidas. Endereçamento, escala, ordem e permissões são explícitos. Ativação não envia comandos.
- Diagnóstico determinístico por malha; referências de demonstração não são limites normativos. Em live, análise só após perfil validado. LLM/Ollama recebe evidências somente leitura; RAG lexical leve com documentos aprovados e escopo. Sem modelos/credenciais no pacote.
- Sem garantia de prontidão clínica, conformidade normativa ou disponibilidade industrial. FAT/SAT, hardware, TXT reais, PostgreSQL/ARM64 e rede hospitalar precisam de validação no ambiente final.

## Critérios verificáveis
14 cards; distinção de alarme/processo/comunicação; nomes originais dos tags; gráficos com setpoint histórico e lacunas; expansão não perde rota; sessões no servidor, RBAC e CSRF; comandos vencidos/conflitantes rejeitados; nenhuma chamada de escrita ao CLP; falha não vira normal nem simulação; auditoria; histórico e CSV; recuperação/documentação de SSD e backup; testes automatizados e handoff Codex.
