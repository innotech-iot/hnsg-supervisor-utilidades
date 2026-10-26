export const ctx={session:null,state:null,route:'dashboard',charts:[],epoch:0,polling:false,lastHistory:0};
export const $=(q,root=document)=>root.querySelector(q);
export const $$=(q,root=document)=>[...root.querySelectorAll(q)];
export const h=(s)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmt=(v,d=1)=>v===null||v===undefined||!Number.isFinite(Number(v))?'—':Number(v).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
export const date=(ts,seconds=false)=>ts?new Date(ts*1000).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',...(seconds?{second:'2-digit'}:{})}):'—';
export const clock=(ts)=>ts?new Date(ts*1000).toLocaleTimeString('pt-BR',{timeZone:'America/Sao_Paulo',hour:'2-digit',minute:'2-digit',second:'2-digit'}):'—';
export const duration=(s)=>s==null?'—':s<60?`${Math.floor(s)} s`:s<3600?`${Math.floor(s/60)} min`:`${Math.floor(s/3600)} h ${Math.floor(s%3600/60)} min`;
export const roles={viewer:'Visualização',operator:'Eletromecânica',admin:'Administrador'};
export const canOperate=()=>['operator','admin'].includes(ctx.session?.user.role);
export const isAdmin=()=>ctx.session?.user.role==='admin';
export const utaName=(id)=>id?ctx.state?.assets.find(a=>a.id===Number(id))?.name||`Equipamento ${id}`:'Geral do CLP';
export const assetRoute=(id)=>`${ctx.state?.assets.find(a=>a.id===Number(id))?.kind==='uta'?'uta':'central'}/${id}`;
export function adjacentAsset(id,direction){const assets=ctx.state?.assets||[];if(!assets.length)return 'dashboard';const index=Math.max(0,assets.findIndex(a=>a.id===Number(id)));return assetRoute(assets[(index+direction+assets.length)%assets.length].id);}
export const controllerOptions=()=>ctx.state?.controllers.map(c=>`<option value="${c.id}">${h(c.name)}</option>`).join('')||'';
export const navigate=(route)=>{location.hash=route;};
const paths={
 dashboard:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
 fan:'M12 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0-4 0 M10 10C3 4 13-2 14 7L13 10 M14 11C23 7 25 18 17 17L14 14 M11 14C12 24 1 19 6 14L10 12',
 chart:'M3 3v18h18 M6 15l4-5 4 3 6-9',
 alarm:'M12 3a6 6 0 0 1 6 6v6l3 3H3l3-3V9a6 6 0 0 1 6-6 M9 21h6',
 shield:'M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6z M8 12l3 3 5-6',
 settings:'M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M12 2v3 M12 19v3 M2 12h3 M19 12h3 M5 5l2 2 M17 17l2 2 M5 19l2-2 M17 7l2-2',
 health:'M3 12h4l3-8 4 16 3-8h4',
 book:'M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H4z M13 7a3 3 0 0 1 3-3h5v15h-5a4 4 0 0 0-3 2',
 tool:'M14 4a6 6 0 0 0-7 7l-5 6 5 5 6-6a6 6 0 0 0 7-7l-4 4-4-4z',
 rooms:'M3 21V3h12v18 M15 8h6v13 M6 7h2 M10 7h2 M6 11h2 M10 11h2 M8 21v-5h3v5',
 ai:'M8 3v3 M16 3v3 M8 18v3 M16 18v3 M3 8h3 M3 16h3 M18 8h3 M18 16h3 M6 6h12v12H6z M10 10h4v4h-4z',
 import:'M12 3v12 M7 10l5 5 5-5 M4 16v5h16v-5',
 export:'M12 16V3 M7 8l5-5 5 5 M4 16v5h16v-5',
 arrow:'M5 12h14 M14 7l5 5-5 5',
 refresh:'M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 13 3 M18 18a8 8 0 0 1-13-3',
 expand:'M8 3H3v5 M16 3h5v5 M3 16v5h5 M21 16v5h-5',
 collapse:'M3 8h5V3 M21 8h-5V3 M8 21v-5H3 M16 21v-5h5',
 fullscreen:'M3 3h18v18H3z M8 7H7v3 M17 10V7h-3 M7 14v3h3 M14 17h3v-3',
 sun:'M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M12 2v2 M12 20v2 M2 12h2 M20 12h2 M5 5l1 1 M18 18l1 1 M5 19l1-1 M18 6l1-1',
 moon:'M20 14a8 8 0 0 1-10-10 9 9 0 1 0 10 10',
 menu:'M4 6h16 M4 12h16 M4 18h16',
 search:'M10 3a7 7 0 1 0 0 14a7 7 0 1 0 0-14 M15 15l6 6',
 check:'M5 12l4 4 10-10',
 temperature:'M10 14V5a2 2 0 1 1 4 0v9a5 5 0 1 1-4 0 M12 8v10',
 humidity:'M12 2C10 6 5 10 5 15a7 7 0 0 0 14 0c0-5-5-9-7-13 M8 15a4 4 0 0 0 4 4',
 wind:'M3 8h12a3 3 0 1 0-3-3 M3 12h16a3 3 0 1 1-3 3 M3 16h7a3 3 0 1 1-3 3',
 power:'M12 2v10 M6 5a9 9 0 1 0 12 0',
 clock:'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 7v5l4 2',
 filter:'M3 4h18l-7 8v7l-4 2v-9z',
 user:'M12 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M4 21v-3a5 5 0 0 1 5-5h6a5 5 0 0 1 5 5v3',
 edit:'M15 4l5 5 M4 15L16 3l5 5L9 20l-6 1z',
 info:'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 10v7 M12 7h.01',
 server:'M3 3h18v7H3z M3 14h18v7H3z M7 6h.01 M7 17h.01',
 pause:'M8 5v14 M16 5v14',
 play:'M7 4l14 8-14 8z',
 close:'M5 5l14 14 M19 5L5 19',
 logout:'M9 3H3v18h6 M10 12h11 M16 7l5 5-5 5',
 report:'M6 2h9l5 5v15H6z M14 2v6h6 M9 12h8 M9 16h8'
};
export const icon=(name)=>`<svg class="icon" aria-hidden="true" viewBox="0 0 24 24"><path d="${paths[name]||paths.info}"/></svg>`;
export const badge=(text,type='')=>`<span class="badge ${type}">${h(text)}</span>`;
export const empty=(title,text='',ic='info')=>`<div class="empty">${icon(ic)}<h3>${h(title)}</h3><p>${h(text)}</p></div>`;
export const pageHead=(eyebrow,title,sub='',actions='')=>`<div class="page-head"><div><span class="eyebrow">${h(eyebrow)}</span><h1>${h(title)}</h1><p>${h(sub)}</p></div><div class="toolbar">${actions}</div></div>`;
export const panel=(title,body,sub='',actions='')=>`<section class="panel"><header class="panel-head"><div><h3>${h(title)}</h3>${sub?`<p>${h(sub)}</p>`:''}</div>${actions}</header>${body}</section>`;
export const field=(label,input)=>`<label>${h(label)}${input}</label>`;
export const input=(name,value='',type='text',extra='')=>`<input name="${name}" type="${type}" value="${h(value)}" ${extra}>`;
export const assetOptions=(selected=null,all=false)=>`${all?'<option value="">Todos os equipamentos / geral</option>':''}${ctx.state?.assets.map(a=>`<option value="${a.id}" ${a.id===Number(selected)?'selected':''}>${h(a.name)} · CLP ${a.controller_id}</option>`).join('')||''}`;
export async function api(path,options={}){
 const opts={credentials:'same-origin',...options,headers:{...options.headers}};
 if(ctx.session?.csrf) opts.headers['X-CSRF-Token']=ctx.session.csrf;
 if(opts.body!==undefined && typeof opts.body!=='string'){opts.body=JSON.stringify(opts.body);opts.headers['Content-Type']='application/json';}
 const res=await fetch(path,opts); let data;
 try{data=await res.json();}catch(_){data={detail:'Resposta inválida do servidor'};}
 if(!res.ok){if(res.status===401&&!path.includes('/auth/login')) window.dispatchEvent(new CustomEvent('session-expired'));
   let message=data.detail||`Erro HTTP ${res.status}`;
   if(Array.isArray(message))message=message.map(x=>`${x.loc?.slice(1).join('.')}: ${x.msg}`).join('; ');
   const err=new Error(message);err.status=res.status;throw err;}
 return data;
}
let toastTimer;
export function toast(message,error=false){const el=$('#toast');el.textContent=message;el.hidden=false;el.classList.toggle('error',error);clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.hidden=true,6000);}
let lastFocus=null;
export function showDialog(title,body,wide=false){
 lastFocus=document.activeElement;
 $('#dialog-title').textContent=title;$('#dialog-body').innerHTML=body;$('#dialog').classList.toggle('wide',wide);$('#dialog-overlay').hidden=false;
 setTimeout(()=>$('#dialog-body input, #dialog-body select, #dialog-body button')?.focus(),20);
}
export function closeDialog(){window.dispatchEvent(new CustomEvent('dialog-closed'));$('#dialog-overlay').hidden=true;$('#dialog-body').innerHTML='';lastFocus?.focus?.();}
export function formData(form){return Object.fromEntries(new FormData(form).entries());}
export async function submitSafely(form,fn){
 const buttons=$$('button[type=submit]',form);buttons.forEach(b=>b.disabled=true);
 let err=$('.form-error',form);if(!err){err=document.createElement('div');err.className='error-text form-error';form.prepend(err);}err.textContent='';
 try{await fn(formData(form));}catch(e){err.textContent=e.message;}finally{buttons.forEach(b=>b.disabled=false);}
}
export const formActions=(text='Salvar')=>`<div class="form-actions"><button type="button" class="button ghost" data-close-dialog>Cancelar</button><button type="submit" class="button primary">${h(text)}</button></div>`;
