# Progresso — plano: docs/superpowers/plans/2026-10-14-centrais.md

Base: 51 passed, 3 skipped, 1 aviso em 15,73 s (Windows/Python 3.13).
Sem Git: nenhuma ferramenta de worktree/commit é aplicável; execução no workspace autorizado. Não usar scripts de ledger dependentes de Git; este arquivo preserva o progresso.
Interfaces verificadas: tarefa 1 produz Asset.kind/schema 2; tarefa 2 consome ambos; tarefa 3 consome estado com kind e catálogos por tipo.
Decisão: executar o plano já autorizado pelo usuário sem solicitar autorização novamente. Apenas migrações em fixtures/bancos temporários; bancos existentes do usuário permanecem intactos.

Tarefa 1: completa — testes migrations/backups: 12 passed em 1,50 s. RED: 7 testes de migration falharam; GREEN após implementação. Restauração v1→banco separado→migração verificada. CLI acrescentada, sem novas dependências.
Tarefa 2: em execução — RED reproduziu buffer ausente para ID 15, dois workers e APIs limitadas a 14. Primeiro GREEN parcial: 4 passed, 1 falha restante de bloqueio explícito de comandos centrais (corrigida em seguida).

Tarefa 2: completa — suíte 63 passed, 3 skipped em 17,95 s. Adicionados depois testes de CLI/lock e recusa de versão 2 sem coluna kind (RED→GREEN).
Tarefa 3: em execução — regressões Node de dashboard e tela central observaram RED (16 cartões UTA e função ausente), depois GREEN. Suíte com testes adicionais: 67 passed, 3 skipped em 20,02 s.
Revisão independente (review_centrals): dois achados relevantes, sem outros problemas concretos novos. Nome de equipamento sem escape na tabela de pontos e KPI contando status desconhecido em central com dado válido. Ambos reproduzidos pelos testes Node (2 failed, 1 passed) e corrigidos (3 passed em 0,41 s). Sem pendências menores reportadas.
UI: ambiente virtual temporário com Playwright 1.57/httpx 0.28 criado fora do workspace; Chromium de testes preexistente falhou por ICU. Ensaio HTTP normal com Chrome instalado em execução.

Inspeção visual: CAQ desktop escuro e mobile claro visíveis sem transbordamento; identificada legenda de referência inadequada para água, corrigida para ida/retorno com regressão RED→GREEN. Unidade °C explícita exigida ao validar temperaturas das centrais, também RED→GREEN; não converter automaticamente dados de outra unidade.
Tarefa 3: completa — suíte final 69 passed, 3 skipped, 1 aviso em 29,27 s; compileall e sintaxe JS saída 0. Chrome/HTTP normal: 13 fluxos aprovados, zero erros JS, relatório e screenshots em docs/screenshots/2026-10-14-centrais-http. Servidor/banco de demo temporários encerrados.
Conclusão: plano concluído para cadastro/supervisão de centrais e migração SQLite. Não houve aplicação em runtime do usuário. PostgreSQL, hardware, TXT real e sequência/detectores específicos continuam pendentes. Sem Git: commits não aplicáveis; documentos preservam plano/progresso/evidência.
