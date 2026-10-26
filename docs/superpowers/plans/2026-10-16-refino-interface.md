# Refino da interface atual

Pedido autorizado: melhorar apresentação preservando frontend nativo e funções.
Escopo: dashboard e componentes compartilhados (hierarquia, contraste, medidas,
cartões, estados, navegação, formulários/tabelas). Sem alterar backend, aquisição,
alarmística, login ou schema; sem framework/CDN. Logos aprovadas preservadas.

Direção: grafite/azul profundo e superfícies claras mais neutras, verde Innotech
como ação/destaque, amarelo para ocorrências e neutro para falta de dados.
Valores maiores com números tabulares; identificação visual de equipamento;
menos ornamentos nos KPIs, cabeçalhos mais legíveis e grid com respiro.
CSS isolado em refinements.css, respeitando responsividade, print e movimento
reduzido. Não inferir normalidade por ausência de alarme nem adicionar dados.

Verificar comportamento existente, 14 UTAs/duas centrais, filtros/compactação,
196 navegações responsivas nos dois temas, modo expandido e diálogos. Revisão
independente, sintaxe/compilação e documentação de evidências reais.

Execução concluída em 16/10/2026. Revisão independente corrigida com identificação
em uma linha e badge flexível. Suíte: 132 passed/12 skipped/1 warning; compileall
e sintaxe JS sem erros. Matriz responsiva e compactação registradas em
docs/screenshots/2026-10-16-refino/. Backend e dados operacionais preservados.
