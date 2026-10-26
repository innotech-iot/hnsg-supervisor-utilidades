# Comparação de comando e retorno do ventilador

Detector consultivo exclusivo das UTAs. CAG/CAQ não recebem essa regra.
Não é uma proteção física, indicação de causa ou prova de funcionamento integral.
Nenhum comando, reset ou ajuste de PLC é executado.

No perfil da UTA, o administrador deve revisar a relação entre os pontos e
selecionar **Comando/retorno do ventilador: relação e valores binários revisados**,
além de validar o perfil e registrar a justificativa. Campo API:
`profile.fan_confirmation_validated`. Padrão **false**, inclusive em demo;
perfis existentes sem o campo permanecem desabilitados. Os pontos live ainda
precisam de associação/validação individual e aquisição real.

Pré-condições: modo automático `1`, snapshot `good`, comando e retorno exatos
`0`/`1`, leituras frescas e sem mudança de versões. A enumeração de modo e os
sentidos dos dois pontos precisam ser comissionados; não inverter valores nem
assumir contato normal aberto/fechado automaticamente.

O mesmo par de valores deve permanecer durante **estabilização + persistência**
do perfil, com pelo menos duas aquisições distintas, lacunas até o máximo
configurado e timestamps crescentes. Leituras em cache não contam como novas
aquisições. No live, modo, comando e retorno precisam ter timestamps individuais
válidos, dentro de `STALE_SECONDS`; polling lento pode tornar a comparação
indisponível. Não ajustar esses limites automaticamente para obter diagnóstico.

Para sinais adquiridos em horários diferentes, a janela começa quando o conjunto
foi observado e termina no timestamp da aquisição mais antiga do conjunto final.
Assim a evidência não antecede a disponibilidade dos três sinais. O servidor
recusa habilitação com estabilização + persistência acima da capacidade nominal
de 1800 snapshots do buffer, calculada com `POLL_SECONDS`. Não é garantia de
capacidade/latência real: medir no alvo.

Resultados internos: `mismatch`, `agreement`, `pending`, `unknown`. Divergência
persistente `1/0` ou `0/1` abre alarme de atenção. Concordância persistente `1/1`
ou `0/0` permite fechar a ocorrência. Concordância breve, qualidade parcial/ruim,
dados vencidos/ausentes, modo parado/manual, valor não binário, configuração
alterada ou comparação desabilitada **não normalizam** o alarme.

Buffers preservam fonte, versões de pontos/mapa, equipamento e conexão, além
dos timestamps por sinal. Alterar perfil ou conexão interrompe a continuidade;
após reinício, snapshots live antigos sem timestamps individuais não bastam.
Uma nova janela válida precisa ser acumulada. Revisões são evidência de contexto,
não aprovação normativa.

Código da ocorrência: `fan_confirmation_mismatch`. Evidência inclui valores,
janela, duração, quantidade de aquisições, versões e limites. `initial` conserva
a primeira evidência da ocorrência mesmo após o buffer avançar; os demais campos
descrevem a avaliação mais recente. `recovery` conserva a concordância que
sustentou o fechamento. Reconhecimento/revisão não alteram o estado físico.
Snapshots persistidos da ocorrência continuam protegidos pela retenção existente.

Flag nova usa JSON existente: schema permanece 2, sem migração. Validado com
fixtures e PostgreSQL isolado; detalhes em VERIFICACAO.md. Limites/prioridade
continuam escolhas de engenharia, dependentes de racionalização hospitalar,
TXT reais, sequência dos CLPs e ensaios no Raspberry.
