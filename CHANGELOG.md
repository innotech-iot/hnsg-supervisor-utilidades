# Histórico de versões

## 0.1.0 — 2026-10-13

Base executável HNSG com demo isolada, UI local modular, autenticação, histórico, alarmes, configuração, leitura Modbus, diagnóstico, backup e roteiro de continuação. Inclui testes e screenshots renderizados com dados fictícios. Sem liberação hospitalar e sem escrita industrial.

Correções verificadas durante a construção: sobreposição de registradores de 32 bits rejeitada; amostras parciais antigas expiram; readiness não aceita último sucesso antigo; resposta de página atrasada não substitui a atual; gráficos ao vivo usam buffer de aquisição; zoom ampliado não é zerado na atualização periódica; limites de consulta/exportação são explícitos.

Correção visual adicional: coluna de trabalho explícita no grid para evitar largura zero ao ocultar sidebar em celular/tablet; testes CSS em 390, 768 e 1600 px.
