# Login e responsividade

Pedido: imagem Innotech no login, nome completo do hospital em evidência e
uso confortável em celulares/tablets. Execução inline autorizada pelo pedido;
preservar auth/CSRF, modo demo/live, logos aprovadas e frontend sem build.

Design: imagem verde original junto à marca; hospital como h1 principal,
subtítulo de supervisão. Login empilhado até 960 px, formulário centralizado,
sem altura fixa que impeça rolagem com teclado. Controles de toque de 44 px,
campos de 16 px em telas menores, cabeçalho sem transbordamento, navegação
expandida com quebra, tabelas com rolagem local e menu com logout acessível.
Dashboard em coluna única nos celulares estreitos. Temas preservados.

Baseline Chrome: login sem imagem e título principal sem nome do hospital;
14 rotas em 360/390/768/1024 sem overflow global detectado. Melhorar ergonomia,
não substituir arquitetura ou esconder dados para mascarar largura.
Etapas: verificação RED de marca/título/toque; HTML/CSS; matriz Chrome de telas,
temas, rotas, menu e diálogo; revisão; documentação de evidências reais.

Execução: RED por imagem ausente; logo e hospital h1 implementados. Revisão
independente apontou menu cortado em pouca altura, cascata de fontes e lacunas
do harness. Reprodução 820×390: nav0, logout425 (>390), seletor11px. Fix pass:
marca compacta em paisagem, campos16px e alvos44px, matriz com renderização
confirmada, checagem de controles internos, perfil/ajuste e modo expandido.
GREEN: 196 navegações, sete tamanhos em dois temas, zero erros JS; 28 diálogos
abertos sem submissão. Screenshots inspecionados. Sem alterações de backend.
Temporários de navegador/pytest em D devido C sem espaço; sem limpeza do usuário.
Suíte final: 132 passed/12 skipped/1 warning, 33.51 s; compileall e sintaxe
JS exit 0. STATUS/VERIFICACAO atualizados; sem achados importantes pendentes.
