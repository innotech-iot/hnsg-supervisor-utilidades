# Comissionamento e aceite — leitura antes de escrita

Esta lista precisa ser preenchida pelos responsáveis e vinculada a evidências reais. Não equivale a autorização de uso assistencial. Os testes não devem provocar falhas em áreas ocupadas sem janela/procedimento autorizado.

## Etapa A — ambiente de bancada

- Confirmar backup do programa CAREL e procedimento de recuperação antes de conectar ferramentas.
- Identificar fisicamente os três CLPs, modelo/firmware, IP, porta, Unit ID e política de conexões.
- Conferir em campo a distribuição cadastrada: CLP 1 (UTAs 01,02,03,09,10,12), CLP 2 (UTAs 04,05,06,07,08,11,13,14 e CAG), CLP 3 (CAQ), além de setores, instrumentos e sequências de cada equipamento.
- Usar rede isolada/autorizada e verificar que o serviço não tem caminho irrestrito à rede hospitalar.
- Instalar dependências em ARM64, PostgreSQL no SSD e executar testes sem PLC físico.
- Executar script de UI por HTTP normal, nos navegadores e resoluções do hospital. Verificar foco, touch, CSS, cookies, CSRF, fullscreen e retorno após perda de sessão.

## Etapa B — protocolo e pontos

Receber TXT original de cada CLP, com identificação de projeto e exportador. Nenhum arquivo de samples pode ser usado como mapa físico.

Confirmar endereços PDU e referência 0/1, áreas, tipos signed/unsigned/float, endianness, escala, offset e unidades. Registrar exemplos conhecidos e comparar com a leitura no software oficial. Ex.: temperatura negativa deve manter sinal, não ocorrer escala duplicada. Não escrever para testar se um ponto “parece” setpoint.

Associar todos os pontos: individuais, gerais, alarmes e não classificados. Para vínculos semânticos, conferir a unidade física esperada pelo catálogo (°C, % UR, m³/h, Pa e %). A versão inicial não possui conversor genérico de unidades: kPa, °F, L/s e 0..1 precisam de normalização explícita e teste no adaptador, sem apresentar números com uma unidade incorreta.

Confirmar os códigos reais de modo. A demo usa 0=parado, 1=auto, 2=manual. Desumidificação precisa refletir o estado que a regra exige, não apenas uma habilitação permanente. Alarmes nativos nesta versão são comparação exata a um valor; palavras com bitmask e códigos complexos precisam de adaptador/testes próprios.

Para cada variável essencial, confirmar qualidade, resposta a falha e temporização. Verificar que reimportar arquivo desabilita a conexão, invalida dados em trânsito e não desloca histórico para outro ponto. Mudança de significado de uma série exige segmentação explícita, não reutilização silenciosa do mesmo gráfico.

## Etapa C — operação e alarmes

- Validar autonomia do CLP sem Raspberry, rede ou internet.
- Testar perda de um CLP sem bloquear o outro; estado da UTA deve ser desconhecido, não desligado.
- Confirmar comando versus retorno real dos atuadores no sinótico. Ajustar desenho à disposição real.
- Definir limites, prioridade, persistência e ação de cada alarme com responsáveis. Não importar limites demonstrativos como norma.
- Confirmar que reconhecer no supervisório não reseta alarme/proteção física.
- Implantar sinalização independente para criticidades definidas pelo hospital.
- Testar destinatários/escalonamento e cobertura de plantão em ferramenta aprovada; ainda não há integração instalada nesta versão.
- Implementar/integrar controle de manutenção e suspensão com prazo, sem esconder falhas críticas.

## Etapa D — dados e disponibilidade

Testar falha de internet, perda da rede local, atraso de resposta, corte controlado de energia em bancada, SSD ausente, banco indisponível, saturação do disco e recuperação. Confirmar que o serviço não grava no ponto de montagem vazio ou no microSD por fallback. Não confundir registro recebido com registro persistido.

Verificar backup externo, checksum e restauração funcional em banco separado. Definir tempo máximo de recuperação e perda de dados aceitável. Validar sincronização de relógio, fuso da apresentação e identificação de mudanças de horário. Repetir teste quando hardware, banco ou software mudar.

Ensaiar carga real de tags, usuários, importação, histórico e backup. Relatórios devem apresentar contagem/qualidade; não calcular “100% conforme” sobre períodos sem dados. Hoje não há relatório completo de conformidade por ambiente.

## Etapa E — IA consultiva

Validar regra e falsos positivos com histórico conhecido. Testar ausência de sensor, estabilidade legítima, partida/parada, manual, mudança de referência e desumidificação com reaquecimento. Revisar cada diagnóstico confirmado e controlar versões da documentação.

Ollama deve permanecer desligado até avaliar qualidade, latência e consumo. Testar falha, timeout, JSON inválido e fonte inventada. A lógica de coleta, alarmes e persistência deve continuar. O modelo não decide liberação de salas, reset, sintonia ou qualquer comando físico.

## Fora do aceite desta versão

Escrita industrial, atuação clínica, certificação, alta disponibilidade automática, redundância de controladores e conformidade normativa não estão cobertas por este pacote. Desenvolver escrita em etapa própria, com matriz de permissões, intertravamentos, comandos idempotentes e verificação de resultado. O laboratório desta entrega não substitui ensaio no HNSG.
