import {ctx,$,$$,h,clock,date,icon,roles,api,toast,navigate,showDialog,closeDialog,formActions,submitSafely,assetRoute,adjacentAsset} from './core.js';
import {dashboard,refreshDashboard,detail,refreshDetail,centralDetail,refreshCentral,historyView,aiView,healthView,refreshCharts} from './views.js';
import {alarmsView,maintenanceView,roomsView,auditView,shiftView} from './operations.js';
import {configView} from './configuration.js';
import {showAccount} from './account.js';
const nav=[['SUPERVISÃO'],['dashboard','Visão geral','dashboard'],['uta/1','Unidades de tratamento','fan'],['central/15','Centrais de água','server'],['history','Históricos e tendências','chart'],['alarms','Central de alarmes','alarm'],['OPERAÇÃO'],['shift','Passagem de plantão','report'],['maintenance','Manutenção','tool'],['rooms','Ambientes atendidos','rooms'],['INTELIGÊNCIA E SISTEMA'],['ai','Diagnóstico inteligente','ai'],['health','Saúde do supervisório','health'],['config/account','Configurações','settings'],['audit','Auditoria','shield']];
const viewNames={dashboard:'Visão geral',uta:'Unidade de tratamento',central:'Central de água',history:'Históricos',alarms:'Central de alarmes',shift:'Passagem de plantão',maintenance:'Manutenção',rooms:'Ambientes',ai:'Diagnóstico inteligente',health:'Saúde do supervisório',config:'Configurações',audit:'Auditoria'};
let pollTimer=null,lastSuccess=0;
function shell(){
 $('#sidebar-nav').innerHTML=nav.map(n=>n.length===1?`<div class="nav-group">${n[0]}</div>`:`<a class="nav-link" href="#${n[0]}" data-route="${n[0].split('/')[0]}">${icon(n[2])}<span>${n[1]}</span>${n[0]==='alarms'?'<span class="nav-counter" id="nav-alarms">0</span>':''}</a>`).join('');
 $('#user-name').textContent=ctx.session.user.name;$('#user-role').textContent=roles[ctx.session.user.role];$('.avatar').textContent=ctx.session.user.name[0].toUpperCase();
 $('#theme-button').innerHTML=icon('sun');$('#expand-button').innerHTML=icon('expand');$('#fullscreen-button').innerHTML=icon('fullscreen');$('#mobile-menu').innerHTML=icon('menu');
 $('#quick-nav').innerHTML='<option value="dashboard">Visão geral</option>';
 try{$('#app').classList.toggle('expanded',localStorage.getItem('hnsg.expanded')==='true');}catch(_){}
 const demo=ctx.session.mode==='demo';$('#origin-badge').textContent=demo?'DEMONSTRAÇÃO':'LEITURA REAL';$('#origin-badge').className='badge '+(demo?'warning':'cyan');$('#side-mode').textContent=demo?'SIMULADO':'LEITURA';$('#footer-source').textContent=demo?'Dados sintéticos · sem conexão aos CLPs':'Dados reais · mapa e cobertura sujeitos a validação';
}
async function enter(session){ctx.session=session;$('#login-screen').hidden=true;$('#app').hidden=false;shell();try{ctx.state=await api('/api/state');$('#quick-nav').innerHTML=`<option value="dashboard">Visão geral</option>${ctx.state.assets.map(a=>`<option value="${assetRoute(a.id)}">${h(a.name)}</option>`).join('')}<option value="history">Históricos</option><option value="alarms">Alarmes</option><option value="ai">Diagnóstico inteligente</option><option value="health">Saúde do supervisório</option>`;lastSuccess=Date.now();await renderRoute();updateStatus();}catch(e){$('#content').innerHTML=`<div class="error-view">${h(e.message)}</div>`;}clearInterval(pollTimer);pollTimer=setInterval(poll,2000);}
function leave(){ctx.epoch++;ctx.session=null;ctx.state=null;clearInterval(pollTimer);pollTimer=null;ctx.charts.forEach(x=>x.chart.destroy());ctx.charts=[];closeDialog();$('#app').hidden=true;$('#login-screen').hidden=false;if(document.fullscreenElement)document.exitFullscreen().catch(()=>{});}
async function renderRoute(){
 if(!ctx.session||!ctx.state)return;
 let route=location.hash.slice(1)||'dashboard';const [path,query='']=route.split('?');const [name,arg]=path.split('/');
 ctx.epoch++;const epoch=ctx.epoch;ctx.route=route;ctx.lastHistory=0;ctx.charts.forEach(x=>x.chart.destroy());ctx.charts=[];if(!$('#dialog-overlay').hidden)closeDialog();
 $('#app').classList.remove('menu-open');$('#content').scrollTop=0;$('#crumb').textContent=['uta','central'].includes(name)?ctx.state.assets.find(a=>a.id===Number(arg))?.name||'Equipamento':viewNames[name]||'Visão geral';
 $$('.nav-link').forEach(a=>a.classList.toggle('active',a.dataset.route===name));$('#quick-nav').value=path;
 $('#content').innerHTML='<div class="loading-view"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div>';
 try{
  if(name==='dashboard')await dashboard();else if(name==='uta')await detail(Number(arg));else if(name==='central')await centralDetail(Number(arg));else if(name==='history')await historyView();else if(name==='alarms')await alarmsView();else if(name==='maintenance')await maintenanceView();else if(name==='rooms')await roomsView();else if(name==='audit')await auditView();else if(name==='shift')await shiftView();else if(name==='ai')await aiView();else if(name==='health')await healthView();else if(name==='config')await configView(arg||'controllers',query);else {location.hash='dashboard';return;}
  if(epoch===ctx.epoch)document.title=`${$('#crumb').textContent} · HNSG / Innotech`;
 }catch(e){if(epoch===ctx.epoch)$('#content').innerHTML=`<div class="error-view"><h2>Não foi possível abrir esta tela</h2><p>${h(e.message)}</p><a class="button mt" href="#dashboard">Voltar ao dashboard</a></div>`;}
}
function updateStatus(){
 if(!ctx.state)return;const now=Date.now()/1000;$('#footer-clock').textContent=clock(now)+' · Brasília';
 const allGood=ctx.state.controllers.every(c=>['online','simulated'].includes(c.status));$('#connection-indicator').innerHTML=`<i class="status-dot ${allGood?'':'warning'}"></i><span>${ctx.state.mode==='demo'?'Servidor local':allGood?ctx.state.controllers.length+' CLPs conectados':'Verificar comunicação'}</span>`;
 const alarms=new Set(ctx.state.assets.flatMap(a=>a.alarms.map(x=>x.id)));if($('#nav-alarms'))$('#nav-alarms').textContent=alarms.size;
 const err=ctx.state.health.persistence_error;const stale=Date.now()-lastSuccess>7000;const warning=$('#system-warning');warning.hidden=!err&&!stale;if(err)warning.textContent='Falha na gravação do histórico: '+err;else if(stale)warning.textContent='Sem atualização do servidor. Dados exibidos estão desatualizados; comandos indisponíveis.';
}
async function poll(){
 if(!ctx.session||ctx.polling)return;ctx.polling=true;
 try{ctx.state=await api('/api/state');lastSuccess=Date.now();updateStatus();const [name,arg]=(ctx.route.split('?')[0]).split('/');if(name==='dashboard')refreshDashboard();if(name==='uta')refreshDetail(Number(arg));if(name==='central')refreshCentral(Number(arg));if(['uta','central','history'].includes(name))await refreshCharts();}
 catch(e){if(ctx.state&&Date.now()-lastSuccess>7000){ctx.state.assets=ctx.state.assets.map(a=>({...a,quality:'stale',status:'unknown',data:{}}));if(ctx.route==='dashboard')refreshDashboard();if(ctx.route.startsWith('uta/'))refreshDetail(Number(ctx.route.split('/')[1]));if(ctx.route.startsWith('central/'))refreshCentral(Number(ctx.route.split('/')[1]));updateStatus();}}
 finally{ctx.polling=false;}
}
function expand(){const value=!$('#app').classList.contains('expanded');$('#app').classList.toggle('expanded',value);$('#expand-button').innerHTML=icon(value?'collapse':'expand');try{localStorage.setItem('hnsg.expanded',String(value));}catch(_){};setTimeout(()=>ctx.charts.forEach(x=>x.chart.draw()),100);}
$('#login-form').onsubmit=async e=>{e.preventDefault();const form=e.target,b=$('button[type=submit]',form);b.disabled=true;$('#login-error').textContent='';try{const r=await api('/api/auth/login',{method:'POST',body:{username:form.elements.username.value,password:form.elements.password.value}});form.elements.password.value='';await enter(r);}catch(error){$('#login-error').textContent=error.message;}finally{b.disabled=false;}};
$('#theme-button').onclick=()=>{const t=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=t;try{localStorage.setItem('innotech.systemTheme',t);}catch(_){}ctx.charts.forEach(x=>x.chart.draw());window.dispatchEvent(new CustomEvent('theme-changed'));};
$('#expand-button').onclick=expand;
$('#fullscreen-button').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else {$('#app').classList.add('expanded');await $('#app').requestFullscreen();}}catch(e){$('#app').classList.add('expanded');toast('Tela cheia nativa indisponível neste navegador. A expansão interna continua ativa.');}};
$('#mobile-menu').onclick=()=>$('#app').classList.toggle('menu-open');
$('#quick-nav').onchange=e=>navigate(e.target.value);
for(const [id,direction] of [['previous-uta',-1],['next-uta',1]])$('#'+id).onclick=()=>navigate(adjacentAsset(Number(ctx.route.split('/')[1])||1,direction));
$('#dialog-close').onclick=closeDialog;$('#dialog-overlay').onclick=e=>{if(e.target.id==='dialog-overlay')closeDialog();};
document.addEventListener('click',e=>{if(e.target.closest('[data-close-dialog]'))closeDialog();});
document.addEventListener('keydown',e=>{const overlay=$('#dialog-overlay');if(!overlay.hidden){if(e.key==='Escape'){e.preventDefault();closeDialog();}if(e.key==='Tab'){const focus=$$('button:not([disabled]), input, select, textarea, a[href]',overlay).filter(x=>x.offsetParent!==null);if(focus.length){if(e.shiftKey&&document.activeElement===focus[0]){e.preventDefault();focus.at(-1).focus();}else if(!e.shiftKey&&document.activeElement===focus.at(-1)){e.preventDefault();focus[0].focus();}}}}});
async function logout(button){button.disabled=true;try{await api('/api/auth/logout',{method:'POST'});leave();}catch(error){toast('Não foi possível encerrar a sessão: '+error.message,true);}finally{button.disabled=false;}}
$('#sidebar-logout').innerHTML=icon('logout')+' Sair';
$('#sidebar-logout').onclick=e=>logout(e.currentTarget);
$('#account-button').onclick=()=>showAccount({logout,leave});
window.addEventListener('hashchange',renderRoute);window.addEventListener('session-expired',()=>{if(ctx.session){leave();$('#login-error').textContent='Sessão expirada. Entre novamente.';}});
window.addEventListener('theme-changed',()=>window.dispatchEvent(new Event('resize')));
api('/api/session').then(enter).catch(()=>{});
