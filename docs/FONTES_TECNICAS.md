# Referências técnicas e decisões

Documentação de referência consultada para arquitetura/implementação. Nenhuma página define automaticamente requisitos de sala ou autoriza uso hospitalar. A validação de normas aplicáveis e versões é atribuição do projeto técnico.

- FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
- Ollama geração/JSON e integração local: https://docs.ollama.com/api/generate e https://docs.ollama.com/capabilities/structured-outputs
- Ollama segurança da API: https://docs.ollama.com/api/authentication
- PostgreSQL pg_dump: https://www.postgresql.org/docs/current/app-pgdump.html
- PostgreSQL restore: https://www.postgresql.org/docs/current/app-pgrestore.html
- PostgreSQL backup: https://www.postgresql.org/docs/current/backup-dump.html
- NIST SP 800-82r3 (tecnologia operacional): https://csrc.nist.gov/pubs/sp/800/82/r3/final
- Codex IDE (OpenAI): https://learn.chatgpt.com/docs/codex/ide
- Visual: paleta encontrada no arquivo de referência do usuário `HNSG_supervisorio_responsivo_revisado.html` (grafite/verde/ciano, tema claro). Este projeto NÃO reutiliza o contexto de motores CAG/VIM32PL desse arquivo. Marca textual e símbolo gráfico são provisórios; substituir pelos ativos oficiais aprovados, sem incorporar fontes licenciadas sem permissão.

Dependências Python: versões instaladas e efetivamente testadas estão nos requirements. Dependências não são copiadas para o ZIP. PostgreSQL/psycopg e modelos Ollama precisam ser obtidos e homologados separadamente no destino. Nenhum arquivo real CAREL, segredo, dado clínico ou configuração de acesso remoto foi fornecido ao gerador desta base.
