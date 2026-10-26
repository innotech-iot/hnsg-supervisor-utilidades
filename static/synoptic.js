// Native SVG cutaway; illustrative arrangement, never an as-built or command surface.
export function utaSynoptic(){
 const coil=(x,color)=>`<g stroke="${color}"><path d="M${x} 285l64-38h56v128l-64 38h-56z" fill="${color}" fill-opacity=".09" stroke-width="3"/>${Array.from({length:14},(_,i)=>`<path d="M${x+i*4} 286l64-38v126l-64 38z" fill="${color}" fill-opacity=".09" stroke-opacity=".55"/>`).join('')}<path d="M${x+12} 283v-49h30m-16 173v25h45" fill="none" stroke-width="6"/></g>`;
 const valve=(x,color,key)=>`<g data-proportional-valve="${key}" transform="translate(${x} 223)"><path d="M-28 12h63" fill="none" stroke="${color}" stroke-width="7"/><g fill="#bc9760" stroke="#e0c89c" stroke-width="1.5"><path d="M-18 3L0 12l-18 9zM18 3L0 12l18 9z"/><path d="M-24 0v24m48-24v24" stroke-width="5"/></g><path d="M0 10v-25" stroke="#b9c8ce" stroke-width="5"/><path d="M-22-38l12-7h34l-12 7z" fill="#768b98"/><path d="M12-38l12-7v29l-12 7z" fill="#243b4a"/><rect x="-22" y="-38" width="34" height="29" rx="3" fill="#405968" stroke="#a3b8c3"/><path d="M-16-29H5" stroke="${color}" stroke-width="4"/><circle cx="-5" cy="-17" r="2" fill="${color}"/></g>`;
 const blades=Array.from({length:7},(_,i)=>`<path transform="rotate(${i*360/7})" d="M-10-17C-61-24-65-81-31-91C-8-98 12-68 14-40L6-13z"/>`).join('');
 return `<div class="synoptic uta-synoptic">
 <div class="uta-scene-scroll" tabindex="0" role="region" aria-label="Sinótico da UTA; deslize horizontalmente em telas pequenas"><div class="uta-scene">
 <svg class="uta-model" viewBox="0 0 1000 560" role="img" aria-labelledby="uta-model-title uta-model-desc">
 <title id="uta-model-title">UTA 3D em corte com válvulas proporcionais</title>
 <desc id="uta-model-desc">Dutos alinhados ao gabinete. Serpentinas de resfriamento e reaquecimento com uma válvula proporcional cada. Ventilador azul com rotor de sete pás, motor central e suportes, inspirado na referência fornecida. Cards ligados aos componentes. Disposição física ilustrativa.</desc>
 <defs>
 <linearGradient id="uta-metal" x2=".2" y2="1"><stop stop-color="#e1e9ee"/><stop offset=".45" stop-color="#9aafbc"/><stop offset="1" stop-color="#5b7485"/></linearGradient>
 <linearGradient id="uta-floor" x2="0" y2="1"><stop stop-color="#7b95a6"/><stop offset="1" stop-color="#3d5667"/></linearGradient>
 <linearGradient id="uta-blue" x2=".8" y2="1"><stop stop-color="#658ac3"/><stop offset=".35" stop-color="#325d9c"/><stop offset="1" stop-color="#122d55"/></linearGradient>
 <linearGradient id="uta-motor" x2="1" y2="1"><stop stop-color="#e0e8eb"/><stop offset=".4" stop-color="#7f909a"/><stop offset="1" stop-color="#344652"/></linearGradient>
 <radialGradient id="uta-shadow"><stop stop-color="#000" stop-opacity=".28"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
 </defs>
 <ellipse cx="498" cy="463" rx="447" ry="58" fill="url(#uta-shadow)"/>
 <!-- Flush end collars share the cabinet end planes; no detached extensions. -->
 <g class="uta-end-collars" stroke="#a9bdc9" stroke-width="1.5">
 <g data-air-port="intake"><path d="M192 292l82-48v126l-82 48z" fill="#263f50"/>
 <path d="M192 292l82-48v126l-82 48zM201 297v105l64-37V260z" fill="url(#uta-metal)" fill-rule="evenodd"/>
 <path d="M201 297l64-37v105l-64 37z" fill="none" stroke="#7894a6"/></g>
 <g data-air-port="outlet"><path d="M718 292l82-48v126l-82 48z" fill="#263f50"/>
 <path d="M718 292l82-48v126l-82 48zM727 297v105l64-37V260z" fill="url(#uta-metal)" fill-rule="evenodd"/>
 <path d="M727 297l64-37v105l-64 37z" fill="none" stroke="#7894a6"/></g>
 </g>
 <!-- Chassis, rear wall and feet. -->
 <g stroke="#9bb2c1" stroke-width="1.5"><path d="M192 418l82-48h526l-82 48z" fill="url(#uta-floor)"/><path d="M192 418v22h526v-22z" fill="url(#uta-metal)"/><path d="M718 418l82-48v22l-82 48z" fill="#476477"/><path d="M274 244h526v126H274z" fill="#405b6e"/><path d="M222 440v30h23v-30m415 0v30h23v-30m82-78v26h20v-26" fill="#425d6f"/></g>
 <path d="M285 258h503m-503 96h503" stroke="#bdd0dc" stroke-opacity=".2"/>
 ${coil(286,'#54cddd')}
 <g id="heater-device" class="uta-heater">${coil(453,'#e4a66e')}<path class="uta-heat" d="M466 296v100m12-107v100m12-107v100" fill="none" stroke="#f2ab64" stroke-width="3"/></g>
 ${valve(324,'#54cddd','cooling')}${valve(491,'#e4a66e','heating')}
 <!-- Reference-inspired plug fan: blue curved impeller, central motor,
      silver mounting plate and tubular guard. Only impeller rotates. -->
 <path d="M608 401v17h72v-17" fill="#526e80" stroke="#a2bdcd" stroke-width="2"/>
 <g id="fan-device" transform="translate(646 348) skewY(-8) scale(.47 .47)">
 <path d="M-110-117l27-16H125L98-117zM98-117l27-16v234l-27 16z" fill="#667d8e" stroke="#b1c4cf" stroke-width="2"/>
 <rect x="-110" y="-117" width="208" height="234" rx="3" fill="url(#uta-metal)" stroke="#c5d4dd" stroke-width="2"/>
 <ellipse cx="-6" cy="0" rx="94" ry="103" fill="#172a3f" stroke="#5e7284" stroke-width="8"/><ellipse cx="1" cy="0" rx="85" ry="95" fill="#14243a" stroke="#5374a4" stroke-width="6"/>
 <g class="uta-rotor" fill="url(#uta-blue)" stroke="#6085bd" stroke-width="1.3">${blades}</g>
 <g class="uta-fan-support" fill="none" stroke-linejoin="round"><path d="M-83-98h58Q-15-98-10-82l18 28h80M-83 98h58Q-15 98-10 82l18-28h80" stroke="#193d6b" stroke-width="11"/><path d="M-83-100h58Q-15-100-10-84l18 28h80M-83 96h58Q-15 96-10 80l18-28h80" stroke="#6487b8" stroke-width="4"/></g>
 <path d="M-20-75l28 24 69-14v130L8 51l-28 24z" fill="url(#uta-blue)" stroke="#5075a8" stroke-width="2"/>
 <ellipse cx="29" cy="0" rx="40" ry="48" fill="#1b2a37" stroke="#9daeb8" stroke-width="4"/><ellipse cx="35" cy="0" rx="34" ry="42" fill="url(#uta-motor)" stroke="#c6d0d5" stroke-width="2"/><ellipse cx="38" cy="0" rx="27" ry="34" fill="#244b81" stroke="#8ea9c6"/>
 <path d="M26 14h24M27 20h22" stroke="#c9d9e6" stroke-width="3"/>
 <g fill="#d7e0e5" stroke="#5a6c78"><circle cx="8" cy="-38" r="4"/><circle cx="64" cy="-27" r="4"/><circle cx="8" cy="38" r="4"/><circle cx="64" cy="27" r="4"/><circle cx="-99" cy="-106" r="3"/><circle cx="87" cy="106" r="3"/></g>
 </g>
 <!-- Hydronic connection stubs: static illustration, no water-flow inference. -->
 <g data-water-circuit="chilled" stroke="#54cddd">
 <g class="uta-water-pipe"><path d="M359 235h23v-70H214M357 432h25v65H226"/><path class="pipe-highlight" d="M359 233h21v-70H214M357 430h27v65H226"/></g>
 <g class="uta-water-label" fill="#54cddd" stroke="none"><text x="214" y="155">AG · IDA</text><text x="226" y="518">ÁGUA GELADA · RETORNO</text></g></g>
 <g data-water-circuit="hot" stroke="#e4a66e">
 <g class="uta-water-pipe"><path d="M526 235h24v-70h58M524 432h26v65h84"/><path class="pipe-highlight" d="M526 233h22v-70h60M524 430h28v65h82"/></g>
 <g class="uta-water-label" fill="#e4a66e" stroke="none"><text x="564" y="155">AQ · IDA</text><text x="550" y="518">ÁGUA QUENTE · RETORNO</text></g></g>
 <!-- Qualitative air movement, enabled only by the existing running state. -->
 <g id="uta-airflow" aria-hidden="true"><path class="uta-air-stream" d="M120 330C230 317 310 337 410 330S620 329 875 330"/><path class="uta-air-stream" d="M120 353H875"/><path class="uta-air-stream" d="M120 376C230 389 310 369 410 376S620 377 875 376"/></g>
 <!-- Cutaway rails keep all three modules visible. -->
 <path d="M192 292l82-48h526l-82 48z" fill="url(#uta-metal)" fill-opacity=".35" stroke="#a9c0cf" stroke-width="2"/>
 <path d="M192 292v126m526-126v126M274 244v126" fill="none" stroke="#c0d2de" stroke-width="6"/><path d="M192 418h526" stroke="#bfd3df" stroke-width="5"/>
 <path d="M192 303h526v102H192z" fill="#97cce7" fill-opacity=".025" stroke="#b4cfdf" stroke-opacity=".25"/>
 <g class="uta-diagram-label"><text x="74" y="459">ENTRADA DE AR</text><text x="817" y="459">SAÍDA DE AR</text></g>
 <g fill="none" stroke="#5fb7c9" stroke-width="2"><path d="M112 475h61m-9-5 9 5-9 5M838 475h61m-9-5 9 5-9 5"/></g>
 <g class="uta-leaders" fill="none" stroke-width="1.6"><path class="cool" d="M275 119v24h49v42"/><path class="heat" d="M495 119v66"/><path class="fan" d="M753 119v52h-76v155"/><circle class="cool" cx="324" cy="185" r="4"/><circle class="heat" cx="495" cy="185" r="4"/><circle class="fan" cx="677" cy="326" r="4"/></g>
 </svg>
 <div class="uta-callout uta-callout-cooling"><span class="uta-callout-kicker">01 · RESFRIAMENTO</span><h4>Válvula proporcional</h4><strong><span data-detail-value="cooling">—</span><small>%</small></strong><span class="uta-callout-note">Comando · serpentina fria</span></div>
 <div class="uta-callout uta-callout-heating"><span class="uta-callout-kicker">02 · REAQUECIMENTO</span><h4>Válvula proporcional</h4><strong><span data-detail-value="heating">—</span><small>%</small></strong><span class="uta-callout-note">Comando · serpentina quente</span></div>
 <div class="uta-callout uta-callout-fan"><span class="uta-callout-kicker">03 · VENTILADOR</span><h4>Velocidade</h4><strong><span data-detail-value="fan_speed">—</span><small>%</small></strong><span class="uta-callout-note">Ponto percentual associado</span></div>
 </div></div>
 <p class="synoptic-caption">Vista 3D ilustrativa · montagem, válvulas e tubulações sujeitas à validação em cada UTA.<br>Percentuais indicam comando, não posição confirmada. Fluxo de ar ilustrativo e rotação vinculados ao retorno, sem representar vazão medida.</p></div>`;
}
