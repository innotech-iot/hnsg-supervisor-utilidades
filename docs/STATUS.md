# Matriz da entrega 0.1.0

## Preparação do repositório GitHub — 26/10/2026

- Destino informado pelo usuário: `innotech-iot/hnsg-supervisor-utilidades`, branch `main`. Histórico local iniciado a partir da versão atual, incluindo simulação completa, serviço Raspberry e conta/senha.
- Arquivos de execução, bancos, ambientes Python e credenciais excluídos do versionamento; regras adicionais de ignore para segredos, chaves e dumps. Manifesto SHA-256 atualizado para o conteúdo versionado.
- Verificação local atual: 142 testes aprovados, 12 ignorados, compilação Python e sintaxe dos dez módulos JS aprovadas. Não representa nova validação de hardware ou do acesso público sem VPN.

## Minha conta, senha e visibilidade de contas — 24/10/2026

- Configurações abre em “Minha conta e senha”, disponível para todos os perfis. Formulário pede senha atual, nova senha e confirmação; confirmação divergente bloqueia envio. Após sucesso, todas as sessões do próprio usuário são revogadas e é necessário entrar novamente.
- Abas administrativas, incluindo Usuários, não são exibidas a plantonistas/operadores. Acesso direto à rota não consulta contas. Mantida regra mais restritiva existente: somente administradores listam/criam/editam outras contas; senha própria usa identidade da sessão, nunca ID informado pelo cliente.
- Backend de autenticação/CSRF e schema preservados. Quatro arquivos de interface atualizados na Raspberry, com backup no USB e sem reiniciar coletor ou alterar contas reais. Serviço ativo e readiness true após entrega.
- Suíte local: 142 aprovados, 12 ignorados; quatro testes focados aprovados na Raspberry. Chrome: três perfis, troca de senha, reautenticação, restrição de contas e celular verificados em banco de fixture separado. Evidências em VERIFICACAO.md.

## Demonstração completa e serviço Raspberry — 22/10/2026

- Simulador opt-in `DEMO_FULL=true` cobre todos os papéis funcionais dos 16 equipamentos, incluindo CAG/CAQ e fan_speed. Cenários normal/faults; valores sintéticos plausíveis, sem equivalência com todos os registradores CAREL nem limites hospitalares.
- Script `scripts/populate_demo.py` cria histórico inicial sem apagar dados existentes; recusa LIVE e usa o lock do coletor. Nenhuma alteração de schema ou escrita Modbus.
- Código transferido para `/opt/hnsg` na Raspberry Debian 13 ARM64. `hnsg-demo.service` ativo/habilitado; Python e SQLite DEMO no USB temporário autorizado. SSD 512 GB ausente; PostgreSQL operacional não alterado.
- Tailscale Funnel configurado em HTTPS 8443 → loopback 8016, preservando publicação privada 443 e serviços preexistentes. Login/CSRF/origem/cookie seguro e histórico dos três tipos verificados por HTTPS via tailnet. **Acesso sem VPN pendente:** DNS público continua NXDOMAIN após janela inicial de dez minutos e reaplicação somente da publicação 8443. Capacidades funnel/https/porta 8443 presentes, Health Tailscale vazio; não confundir configuração aceita com disponibilidade pública.
- Suíte local e Raspberry: 138 aprovados, 12 ignorados. Evidências e limites em `VERIFICACAO.md`; operação em `DEMO_RASPBERRY.md`. Não constitui instalação LIVE nem liberação assistencial.

## Correção das extremidades do sinótico — 16/10/2026

- Removidas extensões externas que pareciam placas soltas. Bocais de entrada/saída agora coincidem com os planos laterais do gabinete, com molduras e aberturas alinhadas. Sem mudanças em leituras, animações ou gráficos.

## Tela UTA: sinótico e tendências selecionáveis — 16/10/2026

- Sinótico compacto à esquerda, tempo real à direita em telas maiores que 1200 px, histórico separado abaixo. Em telas menores os painéis empilham. Ventilador reposicionado com suporte na base interna.
- Gráficos permitem selecionar vários pontos funcionais analógicos da mesma unidade, com pausa, ampliação e período histórico; modal ampliado mantém troca de equipamento/unidade/pontos/período e reset do zoom. Estados digitais permanecem no painel de supervisão; não são interpolados como analógicos. Não representa consulta arbitrária a qualquer registrador não associado ao historiador.
- Card do ventilador em porcentagem; novo papel opcional `fan_speed` (%) disponível para vínculo validado. Sem associação/leitura válida mostra `— %`. Não converte liga/desliga, não calcula velocidade por vazão e não inventa simulação desse ponto. Nenhum endereço/escala presumido ou escrita habilitada.
- Servidor demo mantido em `0.0.0.0:8001`, com o mesmo banco e credenciais; reiniciado para carregar o catálogo adicional. Sem migração de schema.

## Encaixe, fluxo ilustrativo e tubulações — 16/10/2026

- Sinótico centralizado com largura máxima de 1.000 px para evitar crescimento excessivo em monitores grandes. Ventilador redimensionado dentro do módulo do gabinete; cards e linhas preservados.
- Trechos estáticos de ida/retorno de água gelada e quente ligados às serpentinas/válvulas. Fluxo de ar animado da entrada à saída somente com retorno em operação; ilustração qualitativa, não medição de vazão. Movimento reduzido respeitado. Sem comandos industriais ou alterações de aquisição.

## Endereço de escuta — 16/10/2026

- Inicializador demo ajustado para `0.0.0.0:8000`; instruções de acesso local/rede no README. Instância demo já aberta reiniciada em `0.0.0.0:8001`, mantendo `runtime/demo-local`, porta, usuário e banco existentes. Firewall e rede não alterados.

## Refinamento de componentes do sinótico — 16/10/2026

- Dutos de entrada/saída alinhados ao gabinete; duas válvulas proporcionais ilustrativas, uma por serpentina. Ventilador redesenhado em SVG com rotor azul de sete pás, motor central, placa e suportes tubulares inspirados nas imagens fornecidas.
- Faixa inferior substituída por três cards flutuantes com linhas apontando para válvulas/ventilador. Percentuais continuam identificados como comando; card do ventilador acompanha o estado existente, inclusive Sem dados. Não são botões de atuação.
- Em celulares o desenho preserva a legibilidade com rolagem horizontal somente na região do sinótico, acessível por teclado. Chrome: oito combinações de tamanho/tema; suíte 133 aprovados, 12 skips opcionais. Sem alteração de backend ou aquisição; montagem ilustrativa sujeita ao comissionamento.

## Sinótico UTA em perspectiva 3D — 16/10/2026

- Desenho simples substituído por SVG nativo isométrico em corte: gabinete, base, conexões, serpentina, reaquecimento e ventilador. Sem bibliotecas/CDN/WebGL, responsivo nos dois temas. Vista ilustrativa; não constitui levantamento físico de cada UTA.
- Mantidos comandos percentuais e retorno existente do ventilador; rotação somente com estado running, respeitando movimento reduzido. Sem novos comandos ou mudanças na aquisição. Evidências Chrome em `docs/screenshots/2026-10-16-uta-3d/`.

## Refino visual — 16/10/2026

- Dashboard com valores maiores, números tabulares, cartões e indicadores com melhor hierarquia. Temas claro/escuro, navegação, formulários, tabelas e diálogos refinados em CSS nativo isolado (`static/refinements.css`). Logos aprovadas preservadas.
- Identificação de UTA mantém uma linha em cartões estreitos; indicador de estado pode ocupar a linha seguinte. Sem alteração de dados, aquisição, autenticação, alarmes ou schema.
- Chrome local em modo demo: matriz de 196 navegações responsivas; compactação adicional em 430/1600/1920 px e filtro CLP 1 (6 UTAs), retorno a todos (14). Suíte: 132 aprovados, 12 skips opcionais, 1 aviso de dependência. Evidências em `docs/screenshots/2026-10-16-refino/`. Dispositivos físicos/Safari e impressão não homologados.

Status representa código entregue, não homologação de campo.

## Identidade visual — 15/10/2026

- Login usa a imagem verde original da Innotech e destaca Hospital Nossa Senhora das Graças como título principal. Layout empilhado até 960 px, campos maiores e dashboard em coluna única em celulares estreitos.
- Revisão responsiva: controles de toque de 44 px, campos de 16 px em telas menores, navegação expandida com quebra, rolagem local de tabelas/menu, logout acessível inclusive em paisagem curta. Chrome: 196 navegações em sete tamanhos/dois temas, além de diálogos e modo expandido, sem erros JS. Dispositivos físicos/Safari/teclado virtual não ensaiados.

- Botão vermelho Sair no rodapé da sidebar, com ação compartilhada com a conta. Logout usa API/CSRF; falha de rede mantém a tela autenticada e informa erro, sem afirmar encerramento.

- Borda branca externa da logo HNSG ocultada por recorte CSS arredondado, preservando símbolo/textos internos e arquivo original; conferida no Chrome.

- Favicon usa a imagem verde original da Innotech fornecida pelo usuário. Sidebar substitui a marca Innotech pela logo original do HNSG, com texto alternativo e proporção preservada; identidade da tela de login mantida.
- HTTP 200 e conteúdo PNG idêntico aos originais verificados. Chrome: logo carregada, sidebar sem Innotech, temas claro/escuro e menu móvel de 390 px sem transbordamento; zero erros JS. Evidências em VERIFICACAO.md.

## Etapa comando/retorno do ventilador — 14/10/2026

- Detector consultivo UTA para par divergente persistente, inclusive quando retorno está desligado. Opt-in no perfil, desabilitado por padrão; exige perfil validado, modo automático, binários exatos, qualidade good, frescor por sinal, aquisições distintas e versões estáveis.
- Normalização somente por concordância persistente válida. Unknown/pending, desabilitação e mudança de modo/configuração não fecham ocorrência. Evidência inicial e prova de recuperação preservadas; sem inferência de causa física.
- Corrigida proveniência dos buffers: fonte/versões/revisões e timestamps por sinal. Leituras em cache não acumulam duração; mudança de perfil/conexão interrompe a continuidade. Capacidade nominal do buffer validada ao habilitar regra.
- Campo no formulário de perfil UTA e cobertura funcional; editor de pontos preservado. JSON/schema 2 existente, sem migração. Contrato/limitações em COMANDO_RETORNO_VENTILADOR.md.
- Verificação final: **132 passed / 12 skips** no Windows; **135 passed / zero skips** no Linux/PostgreSQL, incluindo **9 integrações reais**; **15 fluxos Chrome/HTTP**, zero erros JS. Compilação Python e sintaxe JS aprovadas. TXT/CLPs reais, ARM64, carga prolongada e racionalização dos limites continuam pendentes.

## Etapa histórico misto — 14/10/2026

- Histórico combina agregados antigos e snapshots/buckets recentes em fronteira de hora cheia, sem sobreposição. Não omite automaticamente a hora corrente por consultar período antigo.
- Resolução/intervalo identificados por linha; gráfico interrompe lacunas conforme resolução local e mostra bandas dentro do intervalo real. Estatísticas IA misturam contagens de métricas, excluindo horas antigas parcialmente externas.
- Revisão independente encontrou hora inteiramente externa retornada e banda invadindo lacuna; ambos reproduzidos RED e corrigidos GREEN. Schema 2 preservado. Contrato e limites em HISTORICO_MISTO.md.
- Final: **107 passed / 11 skips** no Windows; **111 passed / zero skips** no Linux/PostgreSQL; **15 verificações Chrome/HTTP**, zero erros JS. Compileall e sintaxe JS aprovadas. Sem mudanças operacionais.

## Etapa histórico tipado do assistente — 14/10/2026

- Consulta opcional por equipamento, 1–168 horas e métricas numéricas únicas compatíveis com UTA/CAG/CAQ. Whitelist e cálculo no servidor; sem SQL arbitrário ou ferramentas na LLM.
- Estatísticas de snapshots/agregados com contagem ponderada, extremos e avisos de qualidade/retenção. Nulos ou dados inválidos não viram zero. Agregados restritos a horas completas do período. Contagens não certificam cobertura temporal.
- Interface inclui período/métrica e tabela calculada separada do texto consultivo. Evidências históricas auditadas. Estado atual continua disponível; schema 2 preservado. Ver IA_HISTORICO.md.
- Revisão independente sem achados importantes. Testes incluem raw/hourly/bucketed, limite, rejeição por tipo, CAQ sem dados, auditoria e CSRF. Ollama real e consulta mista agregado/bruto continuam pendentes.
- Verificação final: **102 passed / 10 skips** no Windows; **106 passed / zero skips** no Linux, incluindo **7 integrações PostgreSQL reais**; **14 verificações Chrome/HTTP**, zero erros JS. Compileall e sintaxe JS aprovadas.

## Etapa evidências de alarmes — 14/10/2026

- Retenção protege snapshots da ocorrência: 10 minutos antes, todo o período ativo e 10 minutos após fechamento. Escopo equipamento/CLP, incluindo pontos, nulos, qualidade vencida e versões. Sem duplicação ou alteração do schema 2.
- API autenticada por ocorrência, paginação limitada e consulta na inspeção da Central de alarmes. Dados anteriormente apagados não são reconstruídos; snapshots não representam todas as aquisições Modbus. Detalhes em EVIDENCIAS_ALARMES.md.
- Consolidação avança entre horas com dados; correção adicional impede que evidências anteriores à retenção de agregados bloqueiem horas recentes. Teste de 49 horas protegidas de 400 dias atrás reproduziu a falha antes da correção.
- Evidência final: **89 aprovados / 9 skips** no Windows; **92 aprovados / zero skips** no harness Linux, incluindo **6 integrações PostgreSQL reais**; **14 verificações Chrome/HTTP**, sem erros JS. Compileall e sintaxe JS aprovadas.
- Sem purga automática de evidências. Política de descarte auditado e dimensionamento do SSD para ocorrências prolongadas continuam pendentes. Nenhum PLC, banco operacional ou serviço remoto alterado.

## Etapa PostgreSQL e recuperação — 14/10/2026

- PostgreSQL real **16.15** exercitado em Docker local/Linux x86_64: schema novo, API/autenticação/CSRF/RBAC, mapa do CLP 3, JSON/histórico/retenção, migração 1→2 idempotente, rollback de DDL/dados e guard de modo.
- Backup custom via `pg_dump` e restauração via `pg_restore` em banco novo separado, seguida de migração e validação funcional. Preservação de usuário/hash, sessões, configuração, pontos/instrumentos, alarmes, histórico e auditoria verificada. Não houve restore sobre origem.
- Corrigida exposição de senha em argv de `pg_dump`: `URL.set(password=None)` não removia a senha. Helper agora remove senha da URI/query, usa ambiente do subprocesso e `--no-password`.
- Harness reproduzível `scripts/verify_postgres.py`: contexto/builder local validado, rede interna sem portas publicadas, recursos e credenciais exclusivos, runtime operacional não montado, limpeza apenas do projeto e artefatos sanitizados. Modo offline opcional preserva DNS/proxy do usuário.
- **84 testes de backend aprovados no Linux**, incluindo **5 integrações PostgreSQL reais**, sem skips. Suíte comum Windows: **82 aprovados, 8 ignorados** (3 layouts opcionais + 5 PostgreSQL opt-in). Compileall e sintaxe JS aprovadas. Evidências em `docs/postgres-tests/2026-10-14-complete/` e VERIFICACAO.md.
- Job PostgreSQL adicionado ao workflow; não enviado/executado remotamente. ARM64/Raspberry, discos físicos, carga prolongada, TXT/CLPs reais e implantação hospitalar permanecem pendentes.

## Etapa CAG/CAQ e schema 2 — 14/10/2026

- Cadastro ampliado para **14 UTAs + CAG + CAQ / três CLPs**: CAG ID 15 no CLP 2, CAQ ID 16 no CLP 3. Novo CLP sem IP e desabilitado; configurações existentes preservadas.
- Migração 1→2 explícita, transacional, auditada e idempotente; inicialização de schema antigo bloqueada com instrução de atualização. Testes SQLite incluem preservação, recusa, rollback e restauração de backup v1 em banco separado seguida da migração. Procedimento em MIGRACOES.md.
- Runtime orientado ao cadastro, com três tarefas independentes em live; buffers, persistência, histórico/CSV e retenção incluem centrais. Sem leituras fictícias de água; centrais desconhecidas em demo até aquisição válida, e detectores de UTA não são aplicados às centrais.
- Interface preserva 14 cartões e acrescenta área CAG/CAQ, telas próprias, navegação expandida e seletores para três CLPs. Semânticas incompatíveis com tipo/CLP são rejeitadas no servidor; comandos simulados restritos às UTAs.
- Sinóticos físicos e diagnósticos específicos CAG/CAQ continuam pendentes das sequências reais, sensores e referências aprovadas. PostgreSQL/ARM64 e migração no alvo ainda não exercitados. Nenhum banco existente do usuário foi migrado nesta execução.
- Evidência final: **69 testes aprovados, 3 ignorados**, compilação Python e sintaxe JS aprovadas; **13 fluxos de UI pelo Chrome/HTTP normal**, sem erros JavaScript capturados. Relatório e screenshots em `docs/screenshots/2026-10-14-centrais-http/`; detalhes e limitações em VERIFICACAO.md.

## Etapa anterior: backup — 14/10/2026

- Backup SQLite corrigido no Windows: conexões de origem, destino e verificação são fechadas explicitamente; o arquivo pode ser renomeado após backup/verificação.
- A proteção contra backup no mesmo dispositivo considera o arquivo SQLite efetivo de `DATABASE_URL`, inclusive fora de `data_dir`. Os cenários de volumes diferentes usam identificadores de dispositivo controlados nos testes, não discos físicos.
- Verificação local: **51 testes aprovados, 3 ignorados**, compilação Python e sintaxe JS sem erros. Demo temporária iniciou via HTTP; ensaio visual bloqueado pela ausência de Playwright e falha do `pip` local. Evidências em VERIFICACAO.md.
- Na etapa de backup, foi identificada a divergência entre o AGENTS.md (três CLPs) e o cadastro anterior (dois). A etapa CAG/CAQ acima resolve cadastro, interface e migração; comissionamento físico permanece pendente.
- PostgreSQL: a comparação local com `data_dir` não comprova independência do volume real do servidor; validar armazenamento e restauração no alvo.

| Item | Estado |
|---|---|
| Dashboard 14 UTAs + 2 centrais / temas / expansão interna / responsivo | Implementado e exercitado em Chrome por HTTP normal local; desktop e mobile 390 px |
| CAG/CAQ e CLP 3 | Cadastro, telas, aquisição e histórico somente leitura implementados; sequência física e detectores específicos pendentes |
| Tela cheia nativa | Implementada com fallback; validação nativa no PC alvo pendente |
| Sinótico | Indicativo comum; não é as-built de cada UTA |
| Gráficos tempo real | Buffer de aquisição; consulta compartilhada, pausa visual e ampliação |
| Gráficos históricos / CSV / min-máx | Implementados; retenção real e volume ainda não medidos |
| SQLite demo | Implementado e testado |
| SQLAlchemy PostgreSQL | Testado com PostgreSQL 16.15 em contêiner Linux x86_64; alvo Raspberry/ARM64 pendente |
| Modbus TCP FC01/02/03/04 | Leitura implementada e testada com TCP emulado; sem escrita |
| TXT CAREL original | Pendente dos arquivos; adaptador genérico explícito já existe |
| Mapas, revisões e vínculos | Implementados; preservação somente de assinatura técnica idêntica |
| Alarme nativo via ponto | Configurável por valor de disparo e prioridade; falta matriz CAREL real |
| Reconhecimento e revisão de ocorrência | Implementados, separados de reset físico |
| Alarme sonoro, SMS, e-mail, WhatsApp e escalonamento | Não implementados/configurados |
| Sensor/metadata local-modelo-calibração | Campos implementados; gestão completa de certificados ainda pendente |
| Ambientes / criticidade / responsáveis | Cadastro inicial; salas e requisitos reais não fornecidos |
| Chamados de manutenção / passagem de plantão | Implementados; sem integração CMMS/PMOC externa |
| Sessão, perfis, CSRF e auditoria | Implementados e testados; sem MFA nativo e sem log criptograficamente imutável |
| Anomalias temperatura/umidade/saturação/oscilação/congelamento suspeito | Implementadas; regras e qualidade dependem do comissionamento |
| Diagnóstico de vazão, pressão, filtros e tempos de atuadores | Cobertura/catalogação parcial; detectores específicos ainda pendentes |
| RAG | Busca lexical em texto aprovado e escopo UTA; não semântico/vector DB |
| Ollama | Cliente opcional com fallback; modelo/inferência real não executados |
| Consulta histórica livre por linguagem natural | Não implementada; IA utiliza estado/ocorrências atuais |
| Backup | SQLite e pg_dump/pg_restore reais testados em banco descartável separado; armazenamento independente e ensaio no alvo pendentes |
| Systemd/SSD/proxy/rede remota | Templates e roteiro; não instalados/validados no hospital |
| Monitor externo | Script de verificação fornecido, não instalado nem ligado a notificações |
| HA, redundância de banco, nobreak e alarme independente | Requisitos de implantação; não realizados por software neste pacote |
| Migrações incrementais | Schema 2; revisão explícita 1→2, rollback e restauração de backup legado testados com SQLite/PostgreSQL 16.15; instalação final pendente |
| Escrita industrial / autotuning / controle pela LLM | Não implementados; deliberadamente bloqueados |

Não apresentar “cobertura com dados disponíveis” como “todos os defeitos detectáveis”. Não chamar análise ausência-de-alarmes de certificado de normalidade. Sem referências normativas ou setpoints hospitalares fictícios.
