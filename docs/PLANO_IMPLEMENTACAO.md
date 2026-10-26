# Plano de implementação HNSG

**Objetivo:** entregar base executável para continuação no Codex, sem dependência de TXT ausente.
**Arquitetura:** API, coletor, persistência, diagnóstico e UI separados; um worker. Dados e controles separados de inferência. **Especificação:** ESPECIFICACAO.md.

- [x] Contratos e testes: parser estrito, codec Modbus, detectores, segurança, API e comportamento do navegador.
- [x] Backend: configuração, schema, sessões, catálogo, histórico e auditoria.
- [x] Coleta: simulador explicitamente separado, TCP somente leitura, qualidade e histórico.
- [x] Operação: importação e vinculação, alarmes, manutenção, ambientes, usuários.
- [x] Diagnóstico: regras persistentes, evidências, RAG lexical e Ollama opcional com limites.
- [x] Frontend: dashboard 14 UTAs, detalhe/sinótico, gráficos, fullscreen, gestão e relatórios.
- [x] Implantação: scripts Windows/Linux, serviço Pi, PostgreSQL no SSD, backups e segurança remota.
- [x] Verificação: suíte Python, socket real com CLP emulado, testes Playwright, inspeção visual, pacote limpo e handoff.

## Riscos para revisão
Endereço base ambíguo; escala aplicada duas vezes; respostas TCP incompletas; dados vencidos tratados como bons; demonstração misturada com produção; permissão aplicada só no frontend; CSV/HTML com texto injetado; inferência competindo com coleta; SSD não montado; perda de histórico em reimportação; mudança de UTA com comando pendente.

As marcações indicam a entrega da base e suas verificações locais. PostgreSQL/ARM64, CAREL físico, dialeto TXT, TLS/MFA e comissionamento não foram realizados; ver STATUS.md.
