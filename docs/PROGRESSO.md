# Registro da implementação

- Requisitos consolidados a partir da conversa e execução autorizada pelo usuário.
- Decisão: usar frontend modular sem dependência de build para permitir operação offline e manutenção simples em ARM64.
- Decisão: não implementar escrita Modbus nesta base; comandos apenas no simulador. Isso evita liberar operação hospitalar sem mapeamento/validação.
- Decisão: adaptar TXT por contrato explícito e incluir linhas rejeitadas; o parser CAREL definitivo aguarda exemplos reais.
- Ambiente de construção sem saída de rede: não instalar dependências adicionais silenciosamente; usar bibliotecas presentes e testar driver TCP de leitura com emulador.

- Backend/API, simulador, importação, configuração e frontend integrados.
- Corrigidas sobreposição de registradores, expiração de estado parcial, readiness antigo e respostas de rotas atrasadas. Testes de regressão incluídos.
- Driver somente leitura verificado em socket TCP local com fragmentação, exceção e transação inválida.
- Gráficos atuais usam buffer separado do histórico persistido; requests compartilhados por UTA/janela.
- Backup SQLite consistente e checksum/estrutura testados; PostgreSQL não disponível no ambiente.
- UI executada em Chromium via DOM harness + ponte API local, sem alterar políticas de navegador. Navegação HTTP nativa/fullscreen bloqueadas pelo ambiente gerenciado; repetir ensaio normal no PC alvo.
- Implantação fornecida como templates, não instalada no hospital. A matriz de status contém pendências explícitas para o Codex.
