# Plano e registro: evidências

Spec: ../specs/2026-10-14-evidencias-design.md.
Execução inline autorizada pelo pedido de continuação. Sem Git nesta pasta;
registro persistido aqui, sem commits/worktrees ou remoção de runtime.

1. Testes RED de proteção, avanço de agregação e consulta autenticada.
2. Predicados SQL correlacionados na retenção e consulta paginada.
3. Revisão independente, suíte Windows, PostgreSQL isolado, compilação/JS.
4. Atualizar STATUS, VERIFICACAO e handoff com resultados observados.

Interfaces: retenção e consulta compartilham definição da janela/escopo.
Baseline: 82 passed, 8 skipped, 1 warning, 23.57 s.

Concluído: testes iniciais 4 RED → 4 GREEN; casos adicionais → 7 GREEN.
Revisão independente: achado importante de recriação de agregados vencidos
bloqueando horas recentes; test_expired_protected_hours_do_not_starve_recent_rollup
RED → GREEN. Nenhum outro achado importante ou minor informado.
Verificação final: Windows 89 passed/9 skipped/1 warning, 22.77 s;
Linux harness 92 passed/zero skips, incluindo 6 integrações PostgreSQL reais;
Chrome/HTTP 14 verificações/zero erros JS. Compilação Python e sintaxe JS exit 0.
Relatórios em docs/postgres-tests/2026-10-14-evidencias-final e
docs/screenshots/2026-10-14-evidencias-http. Documentação atualizada.
Sem commits (pasta sem Git), sem alteração de schema/runtime operacional.
