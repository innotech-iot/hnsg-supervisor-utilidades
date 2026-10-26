# Verificação da versão 0.1.0

## Diagnóstico do primeiro pipeline GitHub — 26/10/2026

- Segunda execução https://github.com/innotech-iot/hnsg-supervisor-utilidades/actions/runs/40327671906: jobs unit Python 3.11 e 3.13 aprovados. PostgreSQL interrompido no build porque o Node 24.22.1 do Alpine não aceita mais `--experimental-default-type`. Declarado `type: module` em static/package.json e removida a opção experimental dos testes; nenhum npm/build foi adicionado ao aplicativo. Regressores locais de frontend/contas/runner após isso: **20 passed, 1 warning em 15.88 s**; importação direta dos scripts .mjs sem flags e compileall aprovados.

- Logs da execução https://github.com/innotech-iot/hnsg-supervisor-utilidades/actions/runs/40322397631 consultados. Python 3.11: seis falhas JS por `node: bad option: --experimental-default-type=module`, 139 aprovados/nove skips. Setup Node ocorria depois de pytest. Python 3.13 cancelado pela matriz após a falha de 3.11.
- Job PostgreSQL falhou na sanitização de arquivo criado pelo contêiner como root: PermissionError em pg-test-artifacts/pytest-postgres.xml. Artefato original inspecionado: 145 testes, zero falhas/erros, três skips de frontend por Node ausente. Não é evidência de falha no PostgreSQL operacional.
- Runner agora define UID/GID reais, descartando variáveis HNSG_PGTEST_ herdadas. Regressão com identidade 1001:1002 e tentativa de sobrescrita por env 0:0 iniciou RED; após correção, **11 passed em 0.34 s**. Dockerfiles de testes passam a incluir Node e verificar a opção necessária; Compose deixa de excluir os testes JS de centrais/histórico. O único grupo excluído no contêiner continua sendo layout de navegador, exercitado no job unit quando disponível.
- Suíte local após correção do runner: **142 passed, 12 skipped, 1 warning em 82.30 s**. Ensaio Docker local `runtime/ci-postgres-20261026` falhou antes dos testes porque o daemon não resolve dl-cdn.alpinelinux.org; recursos descartáveis removidos, nenhum banco operacional usado. Não foi alterada rede para contornar esse erro.

## Preparação para GitHub — 26/10/2026

- Suíte local completa: **142 passed, 12 skipped, 1 warning em 61.15 s**. Skips opcionais existentes (três layouts/nove PostgreSQL); aviso Starlette/httpx. Compileall app/scripts e sintaxe dos dez módulos JS aprovados.
- Conferência do conjunto inicialmente preparado: 436 arquivos, aproximadamente 26,5 MiB. Sem paths runtime, ambientes Python, bancos, chaves privadas ou assinaturas de tokens na verificação automatizada. Incluídos código, testes, templates de implantação, documentos e evidências sintéticas existentes.
- Origem remota configurada como `https://github.com/innotech-iot/hnsg-supervisor-utilidades.git`; repositório remoto sem refs no início da preparação. Sem alteração de serviços, CLPs ou banco da Raspberry nesta tarefa.

## Minha conta e senha — 24/10/2026

- Regressão frontend iniciou RED: perfis viewer/operator não tinham rota de conta própria; confirmou nova página e ausência de link/consulta à lista de usuários. Payload da troca inclui apenas current/password e recusa confirmação divergente.
- Novos testes API executam a troca para viewer/operator/admin: senha atual incorreta e CSRF ausente rejeitados, ID de outro usuário rejeitado pelo contrato estrito, sessão antiga invalidada, senha antiga recusada e nova aceita; senha da outra conta permanece válida. Lista/edição de contas retornam 403 para perfis inferiores; administradores recebem lista sem hash.
- Suíte local completa: **142 passed, 12 skipped, 1 warning em 81.01 s**. Skips opcionais existentes (três Chromium/nove PostgreSQL) e aviso Starlette/httpx. Compileall app/scripts e sintaxe dos dez módulos JS aprovados.
- Chrome/HTTP local em banco exclusivo runtime/account-qa-20261024: três perfis, acesso à própria conta, confirmação divergente sem requisição HTTP, troca efetiva e novo login, bloqueio da rota de usuários; viewer em 390 px. Sem erros JS. Capturas em docs/screenshots/2026-10-24-account/; captura móvel inspecionada. O primeiro harness usava espera incompatível com CSP; corrigido somente o harness, sem flexibilizar CSP.
- Raspberry: **4 passed, 1 warning em 8.00 s** nos testes novos, com fixtures/temporários separados do banco em execução. Quatro arquivos da interface servidos por HTTP conferidos por SHA-256 contra a versão validada; serviço ativo, readiness true. Cópia anterior em /mnt/innotech-usb/hnsg-transfer/account-backup-20261024-121632. Não foi repetido o fluxo de troca de senha de contas reais, nem alterada qualquer senha existente durante a implantação.
- Revisão independente somente leitura e regressão JS aprovadas. Sem alteração de schema, driver Modbus, configurações de rede ou serviço; coletor não foi reiniciado.

## Simulação completa e Raspberry — 22/10/2026

- Teste de população iniciou RED: apenas 14 equipamentos, faltavam centrais. Após implementação: quatro testes novos verificam todos os papéis presentes, temperaturas/deltas de água, parada, histórico, faixa de percentuais em um dia, falhas nulas e recusa do script em LIVE antes de criar diretório/banco. Chamadas diretas de seed/demo_tick em LIVE também são recusadas.
- Suíte local: **138 passed, 12 skipped, 1 warning em 42.40 s**. Compileall app/scripts e sintaxe dos nove módulos JS aprovados. Skips: três layouts Chromium e nove ensaios PostgreSQL opt-in. Aviso de depreciação Starlette/httpx.
- Suíte executada por SSH na Raspberry Debian 13.5/aarch64, Python 3.13.5, com temporários de teste no USB separado do banco DEMO em execução: **138 passed, 12 skipped, 1 warning em 45.01 s**. Aviso anyio/Starlette; mesmos grupos opcionais ignorados.
- Revisão da UI detectou aviso antigo de centrais sem simulação. Teste de renderização ampliado iniciou RED; correção identifica valores sintéticos quando presentes. Três cenários frontend aprovados localmente e no alvo após correção.
- Suíte local final após o aviso: **138 passed, 12 skipped, 1 warning em 43.63 s**. O emulador TCP imprimiu uma linha de exceção de conexão durante execução, sem teste reprovado. Compileall e sintaxe dos nove módulos JS repetidos com sucesso. Revisão independente de código não encontrou problema bloqueante.
- Chrome instalado no Windows, navegando pelo HTTPS da Raspberry: login, 14 cards UTA + duas centrais, UTA com fan_speed disponível, qualidade válida CAG/CAQ e ausência de erros JS verificados. Capturas em `docs/screenshots/2026-10-22-raspberry/`; captura da CAG inspecionada visualmente. Este cliente ainda estava na tailnet.
- Reinício apenas de `hnsg-demo.service` executado; readiness voltou a true, serviço habilitado e sem reinício automático por falha. RSS observado após reinício: aproximadamente 79 MiB (medição pontual, não ensaio de carga).
- Serviço ativo/habilitado e readiness HTTP 200 (`ready: true`); Funnel persistente 8443, preservando proxy privado 443 → 5000. Teste HTTP pelo endereço HTTPS final: página 200, estado sem sessão 401, login 200, cookie Secure/HttpOnly, estado DEMO com 16 equipamentos válidos, histórico de UTA/CAG/CAQ com mais de 300 pontos, logout sem CSRF 403, origem divergente 403, logout válido 200.
- **Pendência externa confirmada:** Google 8.8.8.8, Cloudflare 1.1.1.1, DoH dos dois provedores e consulta direta a ns1.dnsimple.com retornaram NXDOMAIN. Persistiu após a janela inicial de dez minutos e reaplicação somente do Funnel 8443. Status mostra `AllowFunnel` true somente para 8443; capabilities incluem funnel, https e portas permitidas 443/8443/10000; Health do Tailscale sem avisos e relays ingress presentes. Nenhuma mudança de MagicDNS/nome da tailnet ou reinício do tailscaled foi feita. Assim, **não foi validado acesso por dispositivo sem Tailscale**. Sintoma semelhante relatado em https://github.com/tailscale/tailscale/issues/21829 (não comprova a causa desta instalação).
- Script de população executado duas vezes em fixture separada na Raspberry, com 0,05 h: 96 amostras totais (6 × 16), sem duplicação. Comparação SHA-256 dos 434 arquivos transferidos não encontrou diferenças antes das últimas atualizações de documentação.
- Não houve reboot completo, ensaio de desconexão USB, restauração ou carga prolongada. O espaço do sistema mudou de 100% para 50% durante a sessão, sem execução de limpeza pelo agente.

## Alinhamento das extremidades do sinótico — 16/10/2026

- Inspeção da captura do usuário e geometria SVG identificou extensões/superfícies sobrepostas nas extremidades. Substituídas por bocais nos próprios planos laterais da UTA; sem alteração funcional.
- Oito testes focados de frontend aprovados (0.75 s), sintaxe do módulo aprovada. `verify_uta_layout.py` repetido: oito combinações tamanho/tema e verificações de gráficos/seletores/modal aprovadas, sem erros JS. Captura desktop escura inspecionada após correção; evidências atualizadas em `docs/screenshots/2026-10-16-uta-layout/`. Suíte backend não repetida para alteração geométrica do SVG.

## Sinótico compacto e seleção de pontos — 16/10/2026

- Suíte final após revisão: **134 passed, 12 skipped, 1 warning em 37.75 s**; skips opcionais existentes (3 layouts/9 PostgreSQL), aviso Starlette/httpx. Compileall app/scripts e sintaxe de todos os módulos JS aprovados.
- Novo teste de seleção iniciou RED pela ausência de `registers.js`; seleção por unidade, pontos inexistentes, conjunto vazio e ausência de conversão do comando digital verificados. Oito testes focados aprovados.
- `scripts/verify_uta_layout.py`, Chrome/HTTP demo: oito combinações 360/768/1440/1920 × claro/escuro. Checa layout lado a lado no desktop, histórico abaixo, ausência de overflow principal, seleção de três pontos percentuais, ausência de fan_speed fictício, conjunto vazio, seleção histórica/período e modal ampliado com troca de UTA/unidade/pontos/período/reset. Sem erros JS. Evidências em `docs/screenshots/2026-10-16-uta-layout/`; capturas desktop escuro inspecionadas. No celular o desenho tem rolagem local.
- Matriz adicional de `verify_responsive.py`: 196 navegações em 14 rotas, sete tamanhos e dois temas, sem erros JS; diálogos e navegação expandida preservados. Relatório em subpasta `responsive/`. Essa matriz precedeu a revisão final do modal, posteriormente coberta pelo ensaio específico acima.
- Revisão independente encontrou perda de controles na expansão, inclusão indevida de estados digitais/enum em curvas analógicas, seletores antigos no harness e um título com codificação incorreta. Corrigidos controles do modal, seleção somente analógica, harness `verify_ui.py` (dois gráficos/novos IDs) e título. Fluxos de escrita demo/importação do harness completo não foram repetidos nesta tarefa.
- Primeira suíte encontrou falha auxiliar por falta de espaço na unidade C:. Temporários redirecionados para `runtime/ui-temp` na unidade D:, sem remover arquivos do usuário. Repetição após redirecionamento: 134 passed, 12 skipped, 1 warning em 32.50 s; verificação final pós-revisão registrada abaixo.
- Nenhuma validação física de ventilador, escala percentual, CLP, Safari ou dispositivos móveis reais. `fan_speed` exige vínculo e escala confirmados; não há valor demonstrativo criado para ele.

## Proporção, encaixe e circuitos de água — 16/10/2026

- Contrato atualizado antes da implementação: RED por ausência de fluxo/circuitos; após implementação, sete testes focados aprovados. Suíte completa: **133 passed, 12 skipped, 1 warning em 34.28 s**; skips opcionais existentes e aviso Starlette/httpx. Compileall e sintaxe JS aprovados.
- Chrome/HTTP demo em 360/768/1440/3432 px, claro/escuro: cena limitada a 1.000 × 560 px, sem overflow principal ou erros JS; dois circuitos identificados. Ensaio inicial detectou suporte/rotor além do limite direito; escala reduzida e verificação final dos quatro cantos do bounding box transformado passou em todas as oito combinações. Último ajuste de escala SVG verificado no navegador após a suíte.
- Probe CSS: fluxo sem animação quando inativo, animação com `.active`, movimento interrompido por preferência reduced-motion. Ativação produtiva usa o mesmo retorno running do ventilador; animação não representa vazão medida nem circulação de água. Tubulações são ilustrações estáticas sem inferência hidráulica.
- Evidências em `docs/screenshots/2026-10-16-uta-encaixe/`, com relatório JSON e oito capturas. Desktop escuro de 3432 px inspecionado. Dispositivos físicos/Safari e montagem real não validados. Sem mudança de backend/schema/banco ou acesso aos CLPs.

## Endereço de escuta — 16/10/2026

- `scripts/start_demo.py` compilado sem erros após trocar apenas o host Uvicorn para `0.0.0.0`. Instância local demo reiniciada com um worker, mesmo banco `runtime/demo-local`, porta 8001. `Get-NetTCPConnection` confirmou listener IPv4 `0.0.0.0:8001`; log confirmou startup completo.
- HTTP GET `/` retornou 200 por `127.0.0.1`, Ethernet `192.168.0.250` e Wi-Fi `192.168.15.4`, a partir do próprio PC. `/api/session` sem cookie retornou 401, preservando autenticação. Não foi ensaiado acesso a partir de outro dispositivo. Sem alteração de firewall, CLP ou rede; suíte completa anterior não repetida para troca do endereço de escuta.

## Válvulas, ventilador e cards flutuantes — 16/10/2026

- Contrato do sinótico atualizado antes da implementação: falhou com a versão anterior; após mudança, sete testes focados aprovados. Verifica duas válvulas, três cards, líderes e gancho de atualização de estado, além dos vínculos existentes e acessibilidade SVG.
- Chrome local/HTTP demo: 360/768/1440/1920 px × claro/escuro. Duas válvulas e três cards sem colisão; estado recebido no card; sem overflow do conteúdo principal ou erros JS. Rotação ativa somente com classe running, desativada sem a classe e com movimento reduzido. Probe CSS não envia comandos. Rolagem local verificada nos dois extremos em celular.
- Evidências em `docs/screenshots/2026-10-16-uta-valvulas/`: relatório JSON e capturas, incluindo celular com região deslocada à direita. Inspecionadas visualmente desktop escuro e celular claro à direita. Viewports emulados; dispositivos físicos/Safari não ensaiados.
- Suíte completa: **133 passed, 12 skipped, 1 warning em 32.05 s**. Skips opcionais existentes: 3 layouts/9 PostgreSQL; aviso Starlette/httpx. Compileall app/scripts e sintaxe de todos os módulos JS aprovados. Backend, schema e aquisição preservados; sem escrita industrial.

## Sinótico UTA em perspectiva 3D — 16/10/2026

- Suíte completa: **133 passed, 12 skipped, 1 warning em 38.57 s**; skips opcionais existentes (3 layouts e 9 PostgreSQL), aviso Starlette/httpx. Compileall app/scripts e sintaxe de todos os módulos JS aprovados. Banco e backend preservados.
- Teste de contrato inicialmente falhou pela ausência do módulo; após implementação, 7 testes focados (sinótico, centrais e histórico) passaram. Preservados IDs usados pela atualização e vínculos percentuais. SVG com título/descrição acessíveis e aviso de representação ilustrativa.
- Chrome normal por HTTP demo: 360/768/1440 px nos temas claro/escuro, sem overflow principal ou erros JS. Capturas inspecionadas em desktop escuro e celular claro. Probe de apresentação confirmou ausência de rotação sem `.running`, rotação com a classe e interrupção em `prefers-reduced-motion`. O probe altera apenas classe CSS em sessão privada; não envia comando nem altera estado de aquisição.
- Relatório e seis capturas em `docs/screenshots/2026-10-16-uta-3d/`. Sem validação em dispositivos físicos/Safari, sem modelo físico/as-built fornecido. Implementação em SVG com perspectiva fixa; não adiciona câmera interativa ou dependências 3D.

## Refino visual — 16/10/2026

- HTML carrega folha nativa isolada; alteração JS limitada ao agrupamento visual da identificação da UTA e ícone decorativo `aria-hidden`. Preservados hooks de atualização, estados e qualidade.
- `python -m pytest -q --basetemp runtime/validation-refino-<id>`: **132 passed, 12 skipped, 1 warning em 38.39 s**. Skips existentes: 3 layouts opcionais e 9 integrações PostgreSQL opt-in. Aviso de depreciação Starlette/httpx. `python -m compileall -q app scripts` e `node --check` de todos os módulos JS: saída sem erros. PostgreSQL não repetido para esta mudança visual.
- Matriz Chrome/HTTP demo executada por `scripts/verify_responsive.py`: 14 rotas × 7 tamanhos × 2 temas, com diálogos e modo expandido; relatório e screenshots em `docs/screenshots/2026-10-16-refino/`. Conferidos visualmente dashboards claro/escuro desktop e celular.
- Revisão independente identificou quebra excessiva do título em cartões estreitos. Corrigido flex da identificação para deslocar o badge quando necessário. Chrome após correção: 14 títulos em uma linha, sem transbordamento dos agrupamentos, em 430/1600/1920 px com compactação. Filtro CLP 1 mostra 6 UTAs; retorno a todos mostra 14. Relatório adicional `compact-report.json` e screenshot `compact-1920.png` na mesma pasta.
- Ensaio em navegador desktop com viewports emulados e dados fictícios; não valida dispositivos físicos, Safari, teclado virtual, impressão ou operação hospitalar.

Data de entrega: 13/10/2026, horário de Brasília (execução UTC atravessou 14/10). Evidências abaixo se referem ao ambiente de desenvolvimento, não à instalação do HNSG.

## Identidade visual — 15/10/2026

- Login/responsividade: verificação inicial confirmou ausência da imagem Innotech no login e hospital fora do título principal. `verify_responsive.py` iniciou RED por logo ausente; HTML/CSS atualizados, preservando os arquivos originais e autenticação.
- Matriz final Chrome/HTTP demo: 360×800, 390×844, 768×1024, 820×1180, 844×390, 1024×768 e 1440×1000, em temas claro/escuro; **196 navegações (14 rotas × 7 tamanhos × 2 temas)**. Sem overflow horizontal nos contêineres principais, controles fora dos painéis ou fontes pequenas nos campos visíveis. Diálogos de perfil/ajuste abertos sem submissão; navegação expandida e seleção de UTA verificadas em todas as combinações. Menu e logout visíveis nas resoluções com drawer.
- Revisão independente apontou falta de teste em paisagem curta e diálogos, além de cascata de fontes. Reprodução em 820×390: menu com altura zero, logout abaixo da tela e seletor com 11 px. CSS e matriz corrigidos; versão final inclui paisagem 844×390, menu com rolagem e footer acessível, checagem interna dos controles e espera por renderização em vez de pausa fixa. Nenhuma alteração de autenticação/CSRF.
- Relatório e screenshots em docs/screenshots/2026-10-15-responsivo/. Inspecionados login desktop/celular, dashboard 360 px, menu em paisagem e diálogo tablet. Zero erros JavaScript. Chrome usa temporários em runtime/ui-temp, pois a unidade C: estava sem espaço; nenhum arquivo do usuário foi apagado. Isso não comprova funcionamento em dispositivo físico, Safari ou teclado virtual.
- Suíte após revisão responsiva: **132 passed, 12 skipped, 1 warning (33.51 s)**, com basetemp exclusivo em runtime/validation-ui-* na unidade D. Skips existentes de layouts opcionais/integrações PostgreSQL; nenhum teste removido. Compileall app/scripts e node --check de todos os módulos aprovados. Backend e banco operacional não alterados; PostgreSQL não repetido para esta alteração de HTML/CSS.

- Botão Sair da sidebar: ausência confirmada antes da implementação; Chrome validou cor vermelha, logout desktop e menu móvel, POST com CSRF e /api/session retornando 401 após encerramento. Falha de rede simulada preservou sessão/tela e apresentou erro. Zero erros JS; node --check static/app.js aprovado. Screenshot logout-sidebar.png inspecionado em docs/screenshots/2026-10-15-marcas/. Backend de autenticação não alterado.

- Ajuste posterior: clip-path arredondado remove a moldura branca externa da exibição, sem editar a imagem original. Estilo servido e renderização Chrome confirmados; recorte inspecionado em docs/screenshots/2026-10-15-marcas/logo-sem-borda.png.

- Arquivos fornecidos copiados sem edição: Logo verde.png → static/favicon-innotech.png; logo.png do HNSG → static/logo-hnsg.png. Hashes do conteúdo servido conferidos contra os originais; ambos HTTP 200/image/png.
- HTML servido em http://127.0.0.1:8001 aponta para novo favicon PNG; sidebar contém logo HNSG e não contém INNOTECH. Logo HNSG carrega com resolução natural 512×512, exibida proporcionalmente em 128×128 e com alt acessível.
- Chrome real/headless: login demo, logo carregada, temas claro/escuro e menu móvel de 390 px sem transbordamento; zero erros JavaScript. Screenshots em docs/screenshots/2026-10-15-marcas/. Desktop inspecionado visualmente.
- Alteração restrita a imagens, HTML e CSS; suíte backend não repetida. Servidor demo existente preservado, sem reinício, mudanças de schema ou conexão aos CLPs.

## Comando/retorno de ventilador UTA — 14/10/2026

- Baseline Windows: 107 passed, 11 skipped, 1 warning (42.10 s). Primeiros testes reproduziram ausência do detector em ambos os pares divergentes e ausência de ocorrência a preservar: 3 falhas esperadas → implementação → GREEN.
- **23 testes de detector/runtime/API** cobrem pares 1/0 e 0/1, recuperação persistente, valores ausentes/não binários, modos, qualidade parcial/vencida, lacunas, transições, revisões, timestamps duplicados, cache, desabilitação, capacidade do buffer e preservação de initial/recovery. Dois casos Node exercitam abertura dos formulários de tag e perfil.
- Revisão independente encontrou quatro problemas importantes: cache acumulando duração, checkbox no formulário errado, versões ausentes dos buffers/continuidade de configuração e perda do início da evidência. Cache/versões e UI foram reproduzidos RED no caminho de produção e desenho dos formulários; correções passaram nos testes. Buffers agora incluem timestamps por sinal, fonte e revisões, e updates interrompem continuidade. Teste de buffer limitado conserva a evidência inicial. Caso de aquisição escalonada também RED → duração conservadora → GREEN.
- Suíte final Windows: **132 passed, 12 skipped, 1 warning (37.34 s)**. Skips: 3 layouts opcionais e 9 PostgreSQL opt-in executados no harness. Aviso existente Starlette/httpx. Compileall app/scripts e node --check de todos os módulos concluídos com exit 0.
- PostgreSQL 16.15/Linux x86_64 final: **135 testes, zero failures/errors/skips**, incluindo abertura/recuperação via caminho real update_live_assets em banco live de fixture, sem rede industrial. Artefatos em `docs/postgres-tests/2026-10-14-comando-retorno-completo/`. Projeto `hnsg-pgtest-e017c8f5cdf6a8e2` removido. Ensaio inicial em `2026-10-14-comando-retorno/` registrou a regressão demo/revisão ainda em fase RED; execuções finais foram repetidas depois da correção. Resultados intermediários preservados.
- Chrome/HTTP normal: **15 fluxos**, zero erros JS, gravação do opt-in no perfil UTA e editor de pontos abrindo sem o campo de perfil. Relatório/screenshots em `docs/screenshots/2026-10-14-comando-retorno-final-http/`. Primeiro lançamento encontrou executável temporário do venv ausente; venv recriado com dependências existentes. Ensaio com simulador parado bloqueou confirmação demo após vencimento dos dados; repetição usou coleta **demo ativa** e concluiu, sem afrouxar validade. Servidores temporários encerrados.
- Flag permanece false por padrão, inclusive para bancos existentes. Schema 2 mantido. Nenhum limite/prioridade homologado, TXT real, PLC físico, ARM64 ou serviço operacional utilizado/alterado.

## Histórico misto — 14/10/2026

- Baseline: 102 passed, 10 skipped, 1 warning (34.01 s), sem os testes novos. Três testes novos reproduziram omissão de snapshots recentes/ausência de composição (RED); backend/IA → GREEN.
- Teste Node reproduziu ausência de cálculo de lacuna por resolução local; implementação → GREEN. Revisão independente confirmou dois achados: retorno de hora inteiramente anterior ao início e bandas de extremos centradas antes do intervalo real. Testes SQLite e desenho canvas com contexto instrumentado reproduziram ambos RED → GREEN.
- Caso adicional de bucket com ponto exatamente no fim inclusivo: faixa sem duração não deve pintar intervalo fictício, RED → GREEN. Valor/contagem permanecem. Contínuo legado sem metadados mantém fallback anterior.
- Suíte final Windows: **107 passed, 11 skipped, 1 warning (43.82 s)**. Skips: 3 layouts opcionais e 8 integrações PostgreSQL executadas no harness. Aviso existente Starlette/httpx. Compileall app/scripts e node --check de todos os módulos concluídos com exit 0.
- PostgreSQL 16.15/Linux x86_64: **111 testes, zero failures/errors/skips**, incluindo **8 integrações reais**. Resultado final em `docs/postgres-tests/2026-10-14-historico-misto-final/`. Caso misto real valida fronteira, ausência de duplicação e ponderação. Testes Node/Chromium são executados no host, excluídos do contêiner backend sem esses binários. Projeto `hnsg-pgtest-0cb0755bf45f510e` removido pelo harness.
- Chrome/HTTP normal: **15 verificações**, zero erros JS, fixture demo com três horas agregadas antigas e snapshots recentes. Consulta de 30 dias confirmou linhas ordenadas, composição e renderização no mesmo gráfico. Screenshot inspecionado: bandas dentro das horas e lacuna até os snapshots recentes. Artefatos em `docs/screenshots/2026-10-14-historico-misto-final-http/`. Caso de duração zero validado pelo desenho canvas instrumentado e suíte posterior. Servidor temporário encerrado.
- Sem mudança de schema, dados operacionais ou PLC. Sem ensaio físico/ARM64, carga prolongada ou homologação hospitalar.

## Assistente com histórico tipado — 14/10/2026

- Baseline Windows: 89 passed, 9 skipped, 1 warning (26.38 s).
- Novas consultas válidas inicialmente falharam por campo ausente (RED); campo tipado, validação por equipamento e cálculo → GREEN. Teste de hora cruzando início do intervalo também RED → filtro de horas completas → GREEN.
- **13 novos testes** cobrem snapshots, agregados horários e 1300 snapshots reduzidos em buckets; média ponderada, extremos, nulos, qualidade inválida, CAQ sem dados, limites, whitelist, campos SQL rejeitados, auditoria e CSRF. Revisão independente sem achados importantes; revisor confirmou separadamente bucketed com 1203 snapshots.
- Final Windows: **102 passed, 10 skipped, 1 warning (33.33 s)**. Skips: 3 layouts opcionais e 7 integrações PostgreSQL executadas no harness. Aviso existente Starlette/httpx. Compileall app/scripts e node --check de todos os módulos concluídos com exit 0.
- PostgreSQL 16.15/Linux x86_64: **106 testes, zero failures/errors/skips**. Artefatos em `docs/postgres-tests/2026-10-14-ia-historico/`. Inclui resumo tipado sobre PostgreSQL live de fixture, retenção, migração e restore separado. Projeto `hnsg-pgtest-45767c702a447cde` removido pelo harness, sem banco operacional ou portas publicadas.
- Chrome/HTTP normal: **14 verificações**, zero erros JS. Seleção de 24 h e temperatura da UTA com dados; troca para CAQ seleciona temperatura de ida e mantém média nula na ausência de dados. Relatório/screenshots em `docs/screenshots/2026-10-14-ia-historico-http/`; form/resultado inspecionados visualmente. Servidor demo/banco temporários, credencial aleatória, processo encerrado.
- LLM real, consulta mista agregado/bruto, carga no Raspberry/ARM64 e validação hospitalar não foram exercitados. Schema 2 preservado; nenhuma escrita industrial ou alteração operacional realizada.

## Evidências de alarmes — 14/10/2026

- Baseline: `python -m pytest -q` → 82 passed, 8 skipped, 1 warning (23.57 s).
- Novos testes iniciais: 4 falhas esperadas (amostras apagadas e rota ausente); implementação → 4 aprovados. Casos adicionais cobrem snapshots sem samples, fechamento incompleto e avanço entre lacunas.
- Revisão independente identificou bloqueio por 49 horas protegidas de 400 dias atrás. Regressão RED → seleção corrigida → GREEN, sem apagar evidências. Nenhum outro achado importante informado.
- Suíte final Windows: **89 passed, 9 skipped, 1 warning (22.77 s)**. Skips: 3 layouts opcionais e 6 PostgreSQL opt-in, executados separadamente. Aviso existente de Starlette/httpx. `compileall app scripts` e `node --check` de todos os módulos estáticos concluídos com exit 0.
- `verify_postgres.py --context desktop-linux --package-cache %TEMP%/hnsg-pg-offline-20261014 --output-dir docs/postgres-tests/2026-10-14-evidencias-final` → **92 testes, zero failures/errors/skips**, PostgreSQL 16.15/Linux x86_64. Inclui predicados reais de retenção por CLP, limites inclusivos, nulos/versões, paginação, migração e backup/restore separado. Projeto `hnsg-pgtest-14b6aed63e80198d` removido; consultas por label confirmaram ausência de containers/redes. Artefatos nesse diretório.
- Chrome instalado, navegação HTTP/cookies normais, servidor demo em loopback e banco temporário: **14 verificações**, zero erros JS. Fixture de alarme com 102 amostras validou duas páginas, nulos/stale e consulta de pontos. Relatório/screenshots em `docs/screenshots/2026-10-14-evidencias-http/`; diálogo inspecionado visualmente. Primeiro lançamento do ensaio tentou a rota autenticada `/api/health` sem sessão e foi interrompido; repetição usou `/health/live` e concluiu. Servidores temporários encerrados.
- Sem mudança de schema, banco operacional, PLC, rede ou serviço remoto. Não valida ARM64, capacidade do SSD, aquisições completas, descarte auditado, TLS ou homologação hospitalar.

## Etapa PostgreSQL real e recuperação — 14/10/2026

### Resultado final

Comando local: `python scripts/verify_postgres.py --context desktop-linux --package-cache "$env:TEMP/hnsg-pg-offline-20261014" --output-dir docs/postgres-tests/2026-10-14-complete`.

Resultado: **84 testes de backend aprovados, 0 falhas, 0 erros, 0 skips**, com cinco casos de integração PostgreSQL real. Compose saiu 0 e a limpeza foi concluída. JUnit registra aproximadamente **18,86 s** de execução de testes; o tempo total inclui inicialização e remoção dos contêineres. Consultas por label do projeto confirmaram ausência de contêineres e redes remanescentes após o ensaio.

Ambiente registrado: PostgreSQL e pg_dump **16.15**, Python **3.14.8**, SQLAlchemy **2.0.50**, psycopg **3.3.6**, Linux **x86_64**, Docker Desktop local. São as dependências declaradas da aplicação na imagem de teste, sem alteração dos pacotes Python globais do usuário.

Artefatos finais: `docs/postgres-tests/2026-10-14-complete/report.json`, `postgres-environment.json`, `pytest-postgres.xml` e `compose.log`. O relatório não contém URI ou credenciais. Código montado somente leitura, `runtime/` excluído das montagens, banco em tmpfs, rede interna sem portas publicadas e nenhuma conexão a CLP.

### Cobertura específica PostgreSQL

- Role de aplicação sem superuser; criação de schema/cadastro 16 equipamentos e três controladores, sem habilitar conexão.
- Sessões/login, CSRF, RBAC, bloqueio de escrita live, dados desconhecidos sem aquisição e readiness não aprovado sem CLPs.
- Importação/ativação/vínculo de temperatura da CAQ no CLP 3 com conexão ainda desabilitada.
- Migração v1→v2 idempotente, configuração/perfil/revisão/usuário/histórico/auditoria preservados; recusa de modo errado antes de alterar dados.
- Falha injetada após DDL demonstra rollback real da coluna e dos registros inseridos em PostgreSQL.
- `pg_dump` custom real, checksum/listagem e `pg_restore --exit-on-error --single-transaction` em banco novo vazio. Depois do restore: migração, login, estado/histórico/CSV pela API, sessões, ponto/instrumento, alarme ativo e auditoria preservados, sequência de auditoria utilizável. Origem continua schema 1 e não foi sobrescrita.
- JSON/Boolean e agregação horária da CAQ, histórico e persistência de dado vencido sem repetição de valor antigo.

Os demais casos são testes de backend comuns. Layout Chromium e renderização JS/Node foram explicitamente excluídos do contêiner; permanecem na suíte comum/ensaio visual da etapa anterior.

### Regressões e isolamento do executor

Os dois novos casos de backup reproduziram senha na authority/query do argv antes da correção (**5 aprovados, 2 falhas**), depois passaram (**7 aprovados**). O helper agora elimina ambas as formas da URI e autentica pelo ambiente, preservando parâmetros de conexão não secretos e PGPASSFILE quando não há senha explícita.

Os testes do executor verificam recusa de endpoints SSH/TCP/pipe remoto, aceitação de socket/pipe local, limpeza do projeto em sucesso/falha, sanitização de artefatos, preservação de diretório existente e recusa de cache incompleto. A revisão independente identificou seleção herdada de builder cloud/remoto por BUILDX_BUILDER: regressões observaram **3 falhas**, depois **18 testes focados de executor/backup aprovados**. O executor fixa o builder integrado ao contexto local, valida `Driver: docker` e desativa Bake/seletores externos, sem alterar preferências globais.

### Preparação e limites

A primeira tentativa de construir a imagem normal falhou no DNS/proxy do Docker, antes de executar testes: resultado conservado em `docs/postgres-tests/2026-10-14-first/`. A rede do usuário não foi modificada. Índices/APKs oficiais assinados e wheels compatíveis foram baixados pelo host para `%TEMP%/hnsg-pg-offline-20261014`; `Dockerfile.offline` instalou-os com rede desabilitada. Binários e cache não foram colocados no repositório. O caminho normal online não foi completado neste host.

Suíte comum final Windows/Python 3.13: `python -m pytest -q --tb=short` — **82 aprovados, 8 ignorados, 1 aviso**, em **22,31 s**. Skips: três layouts sem Chromium no PATH e cinco integrações PostgreSQL opt-in (que foram executadas no harness). Permanece o aviso Starlette TestClient/httpx do ambiente global. `python -m compileall -q app scripts` e sintaxe de todos os módulos JS com Node: saída 0.

Job de PostgreSQL incluído no workflow, mas não executado remotamente. Não houve migração de banco do usuário, instalação no Raspberry/ARM64, verificação de SSD/disco independente, carga de 72 h, CAREL/TXT real, TLS ou aceite hospitalar. Ver POSTGRES_TESTES.md para reprodução e MIGRACOES.md antes de qualquer atualização operacional.

## Etapa CAG/CAQ e schema 2 — 14/10/2026

Ambiente: Windows, Python 3.13 e Node 22.14. Todos os bancos e dados deste ensaio são temporários/fictícios. Nenhum banco existente do usuário, CLP físico, rede ou serviço remoto foi alterado.

### Verificação automatizada final

- `python -m pytest -q --tb=short`: **69 aprovados, 3 ignorados, 1 aviso**, em **29,27 s**. Os três skips são os testes opcionais de CSS que procuram Chromium no PATH; o Chrome instalado foi exercitado separadamente pelo ensaio HTTP abaixo. O aviso permanece a depreciação Starlette TestClient/httpx do ambiente instalado.
- `python -m compileall -q app scripts`: saída 0.
- Sintaxe de todos os módulos `static/*.js` com `node --input-type=module --check` via entrada padrão: saída 0.
- Migração: schema 1→2 com preservação de usuário/hash, cadastro, perfil, revisão, configuração, histórico e auditoria; idempotência; recusa de modo/versão/estrutura/ID reservado; rollback de DDL e dados com falha injetada; restauração de backup v1 em banco separado seguida da atualização; CLI de inspeção sem alteração e bloqueio pelo lock da aplicação.
- Centrais: cadastro 16 equipamentos/3 CLPs; três workers independentes; ausência de valores de UTA na demo das centrais; vínculos do CLP 3; semânticas compatíveis por tipo/CLP; unidade °C explícita para temperatura de água validada; histórico/CSV, vencimento de leitura e agregação de CAQ; diagnóstico de ventilação e comandos simulados bloqueados nas centrais; readiness live recusa falta do CLP 3.
- Três regressões JS pelo Node exercitam renderização/navegação com DOM mínimo: 14 cartões UTA + 2 centrais, tela própria com ida/retorno sem referência presumida, KPI de indisponibilidade por qualidade e escape de nome na tabela de pontos. Não são ensaios de layout de navegador.

Testes foram executados antes das respectivas alterações: a migração inicialmente teve 7 falhas; centrais reproduziram buffers e APIs limitados; testes JS reproduziram 16 cartões de UTA e tela central ausente. A revisão independente apontou nome sem escape e KPI incorreto, ambos reproduzidos em RED e corrigidos em GREEN. A inspeção posterior acrescentou regressões de unidade de água e legenda sem setpoint presumido, também RED→GREEN.

### Chrome pelo transporte HTTP normal

O `pip` global continua incompleto. Para não alterá-lo, foi criado ambiente virtual temporário fora do projeto, em `%TEMP%/hnsg-ui-validation-20261014`, com Playwright 1.57.0 e httpx 0.28.1. O Chromium de testes preexistente falhou no lançamento por erro de dados ICU; foi usado o Chrome instalado, com perfil temporário/headless.

Comando do ensaio, com servidor demo em loopback/porta temporária e senha aleatória apenas em variável de ambiente:

```powershell
& "$env:TEMP/hnsg-ui-validation-20261014/Scripts/python.exe" scripts/verify_ui.py --url URL_LOCAL_TEMPORARIA --chromium "C:/Program Files/Google/Chrome/Application/chrome.exe" --screenshots docs/screenshots/2026-10-14-centrais-http
```

Resultado: **13 verificações de fluxo aprovadas**, **zero erros JavaScript capturados**, modo `http-browser`, sem `--dom-harness`. Foram exercitados login com cookies do navegador, 14 UTAs e duas centrais, CAG/CAQ desconhecidas, navegação expandida circular, gráficos, pausa/retomada, ampliação, temas, comando demo em duas etapas, manutenção, importação/ativação do TXT fictício no CLP 3, 12 rotas adicionais, cadastro CAQ sem perfil de ventilação, diagnóstico consultivo e layout móvel de 390 px.

Relatório: `docs/screenshots/2026-10-14-centrais-http/ui-report.json`. Imagens de dashboard, UTAs, CAG/CAQ e celular estão na mesma pasta. As telas CAQ desktop escuro e celular claro foram inspecionadas visualmente. O processo demo foi encerrado ao final, com seu banco temporário separado do runtime do usuário.

### Limitações atuais

Não houve migração/restauração em PostgreSQL, ensaio ARM64/Raspberry, conexão com CAREL, TXT real, discos físicos independentes ou homologação hospitalar. TLS e fullscreen nativo não foram validados. CAG/CAQ não têm sequência física/sinótico ou detectores específicos aprovados. Bancos operacionais existentes precisam do procedimento explícito de MIGRACOES.md e autorização operacional antes de aplicação.

## Etapa anterior: backup local — 14/10/2026

Ambiente: Windows, Python 3.13. Banco temporário e dados fictícios; nenhum CLP físico ou banco do usuário foi alterado.

- Antes das alterações, `python -m pytest -q`: **47 aprovados, 1 falha, 3 ignorados**, em 21,04 s. `test_sqlite_backup_checksum_integrity_and_tamper` falhou com `WinError 32` ao renomear o backup, porque os contextos de conexão SQLite não fechavam os handles.
- Regressões adicionadas antes da correção: recusa de destino no volume do SQLite externo a `data_dir`; aceitação de volume distinto do SQLite mesmo quando coincide com `data_dir`; liberação do arquivo depois da verificação. A execução anterior à correção teve 4 falhas e 1 aprovação no módulo de backup.
- Após corrigir fechamento explícito e origem da comparação de dispositivo: `python -m pytest -q tests/test_backups.py`: **5 aprovados**, em 0,97 s.
- Suíte completa final: `python -m pytest -q`: **51 aprovados, 3 ignorados, 1 aviso**, em 14,07 s. Os testes de layout foram ignorados por ausência de Chromium no PATH. O aviso é de depreciação da integração Starlette TestClient/httpx instalada no ambiente.
- `python -m compileall -q app scripts`: saída 0. Todos os módulos `static/*.js` verificados com `node --input-type=module --check` via entrada padrão: saída 0.
- Demo iniciada em subprocesso Uvicorn, loopback e porta temporária, com banco em diretório temporário: `/health/ready` respondeu HTTP 200. O processo foi encerrado ao fim da tentativa de ensaio.
- `scripts/verify_ui.py` pelo transporte HTTP normal **não executou os fluxos**: `ModuleNotFoundError: playwright`. A tentativa `python -m pip install playwright==1.57.0` também falhou: `ModuleNotFoundError: pip._vendor.rich._emoji_codes`. Nenhum screenshot novo ou resultado visual é apresentado como aprovado.

Os volumes do teste de proteção de dispositivo são simulados apenas no retorno de `Path.stat`; banco, cópia e verificação SQLite são reais e temporários. Não houve ensaio com dois discos físicos, restauração integral, PostgreSQL, Raspberry ou hardware hospitalar. A pasta entregue não contém `.git`, portanto não foi possível registrar commit ou comparar histórico Git.

As evidências abaixo preservam o registro da entrega anterior; não substituem as limitações desta execução.

## Executado

### Suíte automatizada

Comando: `python -m pytest -q`

Resultado final: **51 testes aprovados, 0 falhas** em aproximadamente 9 segundos. Ambiente Linux / Python 3.13. Os 3 testes de CSS usam Chromium de sistema e são opcionais (skip) em hosts que não tenham esse navegador.

Cobertura exercitada:
- 20 contratos: parser, base explícita, tipo/ordem, escala/NaN, duplicidade/sobreposição, área, codec, grupos sem lacunas, detectores, password e CSV.
- 13 testes de API: sessão, perfil, CSRF, origem, mapa, escrita bloqueada, confirmação simulada, conflito, histórico, fallback de IA e CSP.
- 5 de protocolo TCP em socket real local: quadros fragmentados, bits/registradores, exceção, transação inválida e ausência de funções de escrita.
- 8 de segurança operacional: live sem simulação, modo do banco, SSD ausente, RAG aprovado/escopado, sessão hash, vencimento de qualidade parcial, buffer ao vivo e readiness com último sucesso antigo.
- 2 de backup: recusa de mesmo dispositivo por padrão, cópia SQLite consistente, SHA-256/estrutura e adulteração detectada.
- 3 de layout: coluna visível em 390, 768 e 1600 px; regressão de largura zero no mobile corrigida.

Também executados: `python -m compileall -q app scripts` e verificação de sintaxe de cada módulo JS com Node 22. Sem erros nesses comandos. Não foi executado linter externo ou auditoria de vulnerabilidades de dependências.

### Interface em Chromium

Comando reproduzível (servidor DEMO já iniciado e senha de teste em HNSG_UI_PASSWORD):

```bash
python scripts/verify_ui.py --dom-harness --chromium /usr/bin/chromium
```

11 verificações de fluxo passaram; relatório JSON em `screenshots/ui-report.json`, com zero erros JavaScript capturados. Foram exercitados login, 14 cartões, troca de UTA preservando expansão, quatro gráficos, pausa/retomada, gráfico ampliado, tema, confirmação de comando simulado, manutenção, importação de TXT fictício, navegação por 12 rotas adicionais, corrida de resposta atrasada, diagnóstico e layout mobile/menu.

Screenshots reais da interface em execução (somente dados fictícios) estão em `screenshots/`. Foram inspecionados visualmente dashboard normal/expandido, detalhe/gráficos e celular. A inspeção mobile identificou a coluna de conteúdo com largura zero quando o menu era ocultado; foi corrigida e novos testes de regressão confirmaram o conteúdo visível.

**Limitação do ensaio:** o navegador gerenciado disponível bloqueia navegação por URL e fullscreen nativo. Para verificar a UI, os módulos foram executados em documento local em memória, com as chamadas fetch encaminhadas por uma ponte de teste à API HTTP real em loopback. Esse método testa JavaScript, DOM, renderização, ações e backend, mas **não valida o transporte de cookies pelo navegador, TLS, CORS/CSP em navegação normal ou fullscreen nativo**. Essas propriedades precisam de ensaio normal no alvo. Nenhuma política do navegador foi alterada.

No PC de desenvolvimento, para executar pelo caminho HTTP normal, omita `--dom-harness` (use Chromium instalado pelo Playwright ou informe --chromium). Instalar binários do Playwright é preparação separada: `python -m playwright install chromium`, quando permitido pela TI e com acesso ao repositório de pacotes.

## Não executado nesta entrega

- CAREL físico, TXT real e correspondência com programas no HNSG.
- Raspberry Pi, ARM64, SSD, nobreak, infraestrutura hospitalar ou instalação Windows real.
- PostgreSQL/psycopg real, pg_dump/pg_restore de servidor e restauração integral.
- LLM/modelos Ollama ou avaliação semântica de diagnósticos generativos.
- TLS, Tailscale, Cloudflare Access/MFA, regras de firewall e entrega externa de alarmes.
- Alta disponibilidade, ensaio prolongado 24/7, falhas elétricas reais e aceite clínico.
- Pipeline GitHub Actions: o workflow está incluído, mas não foi enviado/executado remotamente.

Essas pendências não são cobertas pelo resultado da suíte. Consulte STATUS.md, COMISSIONAMENTO.md e CODEX_HANDOFF.md antes de ativar leitura industrial.
