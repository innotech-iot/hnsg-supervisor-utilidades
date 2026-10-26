# HNSG · Supervisório Innotech

**Versão 0.1.0 — base executável de desenvolvimento, demonstração e comissionamento em leitura.**

Supervisão web de **14 UTAs, uma CAG e uma CAQ**, em **3 CLPs CAREL via Modbus TCP**, com histórico, alarmes, diagnóstico e interface em português. Alvo de implantação: **Raspberry Pi 5 / 4 GB RAM + SSD de 512 GB**. Esta entrega não foi homologada em hardware hospitalar e não deve ser a única via de alarmes críticos.

**Atualização de banco existente:** schema 1 exige backup, aplicação parada e migração explícita para schema 2. Consulte `docs/MIGRACOES.md`. A inicialização não altera automaticamente um banco antigo.

> **Escrita nos CLPs não está implementada.** Os comandos disponíveis são exclusivamente simulados em DEMO. Modo LIVE não gera valores fictícios nem permite escrita. O TXT real da CAREL ainda precisa ser fornecido e validado.

## Iniciar no Windows

1. Instale Python **3.11 ou superior**, com acesso pelo terminal.
2. Extraia o ZIP, preservando a pasta inteira. Execute **`iniciar-demo.bat`**.
3. Na primeira execução, o script cria o ambiente e instala as dependências. É necessário acesso à internet somente nessa preparação, ou um repositório local de pacotes aprovado.
4. O terminal exibe o usuário `admin` e uma **senha aleatória**. Copie-a e acesse **http://127.0.0.1:8000**.
5. Mantenha o terminal aberto. **Ctrl+C** encerra o servidor. Nas próximas execuções, o banco e a senha permanecem.

O inicializador escuta em **0.0.0.0:8000** (interfaces IPv4 do computador). No próprio PC, use o endereço local acima; em outro dispositivo, use `http://<IP-DESTE-PC>:8000`. `0.0.0.0` é o endereço de escuta, não o endereço de acesso. A disponibilidade pela rede depende das regras existentes da rede e do firewall.

Não abra `static/index.html` diretamente: as telas dependem da API. Não há senha `admin/admin` nem segredo embutido. Para alterar a senha, abra o botão da conta. Para redefinir localmente:

```powershell
.venv\Scripts\python.exe scripts\manage_user.py reset admin
```

A senha é solicitada de forma interativa, não como argumento do comando.

## Iniciar no Linux / macOS

```bash
chmod +x iniciar-demo.sh
./iniciar-demo.sh
```

Ou manualmente, em qualquer plataforma com os comandos equivalentes:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/start_demo.py
```

O inicializador usa SQLite em `runtime/demo.db`. **Não define nem modifica IP de CLP.** Rejeita `DATABASE_URL` externo para evitar apontar a demo para um banco real. A demo começa com cerca de 3 horas de dados sintéticos e continua a gerar leituras. UTA 03 demonstra desvio/saturação; UTA 07 oscilação; UTA 08 desvio de umidade; UTA 11 dados inválidos. Esses cenários não descrevem o hospital.

## Telas incluídas

- **Visão geral:** 14 cartões de UTAs e dois de centrais, filtros por CLP e situação, resumo operacional e ocorrências prioritárias.
- **CAG/CAQ:** telas de água com temperaturas de ida/retorno, comando/retorno da bomba associada, qualidade, alarmes e tendências. As centrais não recebem simulação de UTA; sem aquisição válida, permanecem desconhecidas inclusive em demo. Sinóticos físicos e detectores específicos aguardam sequência aprovada.
- **UTA individual:** sinótico indicativo, comando versus retorno, medições/referências, duas tendências em tempo real e duas históricas.
- **Históricos:** variável e UTA selecionáveis, intervalo personalizado, arrastar para ampliar, pausa visual, médias/extremos quando agregados e CSV.
- **Central de alarmes:** ocorrências de detectores, alarmes nativos mapeados e comunicação; reconhecimento, revisão e evidências.
- **Diagnóstico:** motor determinístico + documentos aprovados recuperados por busca lexical; Ollama opcional.
- **Operação:** manutenção, associação de ambientes, passagem de plantão e auditoria.
- **Configuração:** CLPs, importação TXT, mapa completo, vínculos, instrumentos, perfis, conhecimento e usuários.
- **Saúde do sistema:** recursos locais, persistência, comunicação e último backup registrado.

**Modo expandido** recolhe o menu lateral e mantém navegação por UTA/tela na barra compacta. **Tela cheia nativa** usa a API do navegador quando permitida. Mudar de tela não carrega outro documento. O gráfico ampliado tem seu próprio seletor de UTA, variável e período. Temas claro/escuro usam arquivos locais, sem CDN ou fonte externa.

## Estrutura

```text
app/                 API, dados, segurança, análise e aquisição
static/              interface modular JS/CSS/HTML + canvas/SVG
samples/             contrato TXT FICTÍCIO para teste do parser
scripts/             iniciar, usuários, backup e monitor externo
configs via env      .env.example / deploy/hnsg.env.example
deploy/              serviços systemd, timer e exemplo de proxy TLS
tests/               testes unitários, API e emulador TCP
knowledge/           reservado para documentos que serão aprovados
docs/                especificação, status, operação e evidências
AGENTS.md            invariantes de segurança para agentes
CODEX_HANDOFF.md     prompt e backlog para continuação
```

O frontend é JS modular nativo, em vez da proposta inicial de React. Foi escolhido para fornecer uma base offline sem build Node obrigatório. Node é usado apenas opcionalmente para verificar sintaxe. O processo Python atende um único worker; o coletor e as rotinas são tarefas separadas. Não existe um processo de LLM para cada UTA.

## Distribuição dos equipamentos

| CLP | UTAs | Confirmação |
|---|---|---|
| 1 | 01, 02, 03, 09, 10, 12 | Confirmada pelo usuário |
| 2 | 04, 05, 06, 07, 08, 11, 13, 14 e CAG | Escopo confirmado; conexão/mapa sujeitos a comissionamento |
| 3 | CAQ | Escopo confirmado; conexão/mapa sujeitos a comissionamento |

Uma UTA possui seu próprio estado, mas os pontos são vinculados ao controlador de origem. Endereços iguais em CLPs distintos não são confundidos.

## TXT CAREL: o que já existe e o que falta

Há um fluxo implementado de upload → prévia → validação → diferença entre versões → ativação do cadastro → associação de pontos. O adaptador atual aceita **TXT delimitado com cabeçalho explícito**, não afirma ler todos os formatos exportados pela CAREL.

O arquivo `samples/protocolo-contrato-demo.txt` é fictício e só testa esse contrato. Não é mapa do hospital. Linhas não reconhecidas impedem a ativação. O importador exige área, endereço, tipo e escala; a base 0/1 é uma escolha explícita. Tipos de 32 bits exigem ordens de palavra/byte. `40001` não é traduzido por heurística. Há validação de sobreposição de registradores.

Ativar uma prévia **não escreve valores**. O CLP fica desabilitado até nova confirmação. Vínculos são preservados somente se a assinatura técnica permanecer igual. Pontos sem vínculo/validação não alimentam a coleta. RO/RW é metadado da origem, não autorização de escrita do aplicativo.

Leia `docs/COMISSIONAMENTO.md` antes de qualquer conexão real.

## Aquisição, memória e históricos

Valores iniciais configuráveis: coleta 2 s, persistência dos snapshots por UTA 10 s, pontos completos por CLP aproximadamente 60 s, buffer de aquisição por UTA limitado a 1.800 amostras. Os gráficos em tempo real consultam o buffer; os históricos consultam o banco. Pausar gráfico não pausa aquisição.

Pontos individuais têm período configurável (mínimo 2 s). O driver agrupa apenas endereços contíguos, separa áreas, limita cada grupo e verifica respostas TCP, Unit ID, transação, tamanho e exceções. Não faz varredura de rede. Há uma rotina por CLP, com prazo de leitura e isolamento de falhas.

Retenção inicial: aproximadamente 7 dias de snapshots brutos, removidos somente após consolidar a hora; agregados horários (média, min, max e contagens) por 365 dias. Snapshots de ocorrências ficam protegidos: 10 minutos antes, todo o período ativo e 10 minutos depois do fechamento, sem purga automática por idade. Consulte pela inspeção do alarme ou API paginada; detalhes e limitações em [EVIDENCIAS_ALARMES.md](docs/EVIDENCIAS_ALARMES.md). Dimensionar armazenamento e definir descarte auditado antes da operação. Relatórios de longo período não representam amostras originais.

## Autenticação e comandos

Todos os perfis podem trocar a própria senha em **Configurações → Minha conta e
senha → Alterar minha senha**, ou pelo botão da conta na barra lateral. Informe
a senha atual e confirme a nova senha (mínimo de 12 caracteres). Após a troca,
entre novamente; as sessões anteriores são encerradas. Somente administradores
podem consultar e administrar outras contas. Os demais perfis não veem a aba
Usuários e a API também impede seu acesso à lista e à edição de contas.

Sessões opacas no servidor, cookie HttpOnly/SameSite, senhas PBKDF2 com sal, token CSRF, perfis server-side, validação de origem, limite de corpo HTTP e escaping no frontend. A aplicação não fornece MFA nativo: o acesso remoto deve ser protegido no gateway/provedor aprovado pela TI.

- `viewer`: consulta e análise, sem alterações operacionais.
- `operator`: reconhecimento, manutenção e comandos **simulados** em demo.
- `admin`: configuração, mapas, perfis e usuários.

Ajustes demonstrativos exigem motivo, valor esperado, confirmação e validade curta. Nenhuma função de escrita Modbus está presente. Todas as operações físicas dependem de futura implementação e comissionamento separado.

## Ollama opcional

Desligado por padrão. Documentos aprovados são consultados por busca lexical, não por embeddings. A resposta sem LLM é determinística e sempre disponível. Não baixa modelos automaticamente e não executa ferramentas/SQL livre.

```bash
# Exemplo de configuração; escolha e teste o modelo separadamente.
export OLLAMA_ENABLED=true
export OLLAMA_URL=http://127.0.0.1:11434
export OLLAMA_MODEL='nome-exato-do-modelo-ja-instalado'
```

O modelo recebe evidências estruturadas e até três trechos aprovados. Uma inferência por vez, timeout, resposta JSON, fontes verificadas e `keep_alive=0`. Validação de JSON/fontes não comprova correção numérica ou causal. O teste do modelo no hardware, a instalação de pesos e a avaliação do RAG semântico continuam pendentes. Nunca exponha a API do Ollama à internet.

O assistente permite selecionar período de até sete dias e métrica numérica por equipamento. O servidor calcula média ponderada por contagens, mínimo, máximo e medições disponíveis; nulos/qualidade inválida não são convertidos em zero. A tabela permanece separada da explicação. Não há SQL livre ou ferramentas na LLM. Contrato e limitações de agregação em [IA_HISTORICO.md](docs/IA_HISTORICO.md).

Períodos atravessando a retenção combinam agregados horários antigos e snapshots/buckets recentes, sem contagem duplicada. Resolução por linha preserva lacunas no gráfico. Veja [HISTORICO_MISTO.md](docs/HISTORICO_MISTO.md).

Comparação de comando/retorno do ventilador UTA é opcional, desabilitada por padrão. Exige confirmação explícita da relação dos pontos no perfil, dados binários frescos e persistência; dados desconhecidos não fecham a ocorrência. Detalhes em [COMANDO_RETORNO_VENTILADOR.md](docs/COMANDO_RETORNO_VENTILADOR.md).

## Raspberry / PostgreSQL / SSD

**Demonstração completa na Raspberry Innotech:** ver [DEMO_RASPBERRY.md](docs/DEMO_RASPBERRY.md)
para o serviço `hnsg-demo`, simulador dos 16 equipamentos, população inicial e
acesso HTTPS por Tailscale Funnel. Essa instância usa banco SQLite DEMO separado
no USB temporário autorizado; a instalação LIVE/PostgreSQL abaixo continua sendo
uma etapa própria. `DEMO_FULL=true` habilita também CAG/CAQ sintéticas e velocidade
dos ventiladores, mantendo a demo tradicional como padrão.

Consulte **`docs/RASPBERRY_DEPLOY.md`**. Há templates, mas não foi feita instalação no seu equipamento. O SSD deve conter o diretório de dados real do PostgreSQL, inclusive WAL; apontar só `HNSG_DATA_DIR` para ele não move o PostgreSQL. O serviço usa `RequiresMountsFor`, `mountpoint` e verificação da montagem. Os 4 GB continuam sendo o orçamento de RAM: LLM não tem prioridade sobre coleta e alarmes.

Arquivos `.env.example` são **referência**, não são carregados automaticamente pelo Python. Exporte variáveis no terminal ou use `EnvironmentFile` do serviço. Não versionar arquivos com segredos.

## Backup e verificação

```bash
# Destino externo deve existir e estar montado.
python scripts/backup.py /mnt/hnsg-backup
python scripts/backup.py --verify /mnt/hnsg-backup/ARQUIVO.pgdump.json
```

Para teste da demo no mesmo disco, use explicitamente `--allow-same-device`. Isso NÃO constitui backup independente. O script usa a API de backup do SQLite ou pg_dump custom, gera manifesto SHA-256 e registra o resultado. Verificação de checksum/estrutura não é restauração integral. Configurar retenção/cópia externa/criptografia conforme TI, e testar restauração em banco separado.

`python scripts/check_remote.py URL_BASE` verifica `/health/ready` a partir de outro computador e retorna código 0/2. Não há destinatário ou entrega externa configurados. Alarmes críticos independentes precisam ser implementados na instalação.

## Testes

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q app scripts
```

Opcional, sintaxe dos módulos (Bash + Node):

```bash
for f in static/*.js; do node --input-type=module --check < "$f"; done
```

Testes usam banco temporário e CLP TCP emulado. Não conectam aos IPs do hospital. Para verificação visual, veja `scripts/verify_ui.py --help` e `docs/VERIFICACAO.md`.

Ensaio PostgreSQL real descartável (Docker local, sem banco operacional ou portas publicadas):

```bash
python scripts/verify_postgres.py
```

Consulte `docs/POSTGRES_TESTES.md` para contexto Docker, cache offline, artefatos e limitações. Os cinco testes PostgreSQL são opt-in e não conectam automaticamente ao `DATABASE_URL` da instalação. Migração e backup/restauração foram exercitados com PostgreSQL 16 em Linux x86_64; Raspberry/ARM64 e armazenamento físico ainda precisam de ensaio.

## Continuação

**Abra `CODEX_HANDOFF.md` no Codex.** A próxima etapa principal é adaptar os três TXT reais, validar bindings/modos/escala e executar ensaios em Raspberry com PostgreSQL. A base não substitui proteções dos CLPs, PMOC, sinalização de emergência, procedimentos do hospital ou liberação de ambiente por profissional responsável.
