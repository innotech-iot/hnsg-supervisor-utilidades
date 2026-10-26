/* Offline canvas time series. No external library, no network assets.
   Missing values break paths. Aggregation displays extrema as a band; SP is stepwise.
   Pointer drag = zoom; double click = reset. */
import {h,fmt,date} from './core.js';
export function historyGapLimit(previous,current,fallback){
 const resolution=current.resolution_seconds;
 if(!Number.isFinite(resolution)||resolution<=0)return fallback;
 const priorSpan=previous.aggregation==='raw'?0:Math.max(0,
  (previous.interval_end??previous.ts)-previous.ts);
 return priorSpan+(current.aggregation==='raw'?Math.max(45,resolution*3):resolution*.8);
}
export class TimeChart{
 constructor(canvas,{series=[],unit='',aggregation='raw'}={}){
  this.canvas=canvas;this.ctx=canvas.getContext('2d');this.options={series,unit,aggregation};this.rows=[];this.zoom=null;this.hover=null;this.drag=null;this.paused=false;
  this.tip=document.createElement('div');this.tip.className='plot-tooltip';this.tip.hidden=true;canvas.parentElement.append(this.tip);
  this.ro=new ResizeObserver(()=>this.draw());this.ro.observe(canvas.parentElement);
  this.move=(e)=>{const r=canvas.getBoundingClientRect();this.hover={x:e.clientX-r.left,y:e.clientY-r.top};if(this.drag)this.drag.end=this.hover.x;this.draw();};
  this.leave=()=>{if(!this.drag){this.hover=null;this.tip.hidden=true;this.draw();}};
  this.down=e=>{if(e.button!==0||!this.bounds)return;const r=canvas.getBoundingClientRect();this.drag={start:e.clientX-r.left,end:e.clientX-r.left};canvas.setPointerCapture(e.pointerId);};
  this.up=e=>{if(this.drag&&this.bounds){const {start,end}=this.drag;if(Math.abs(start-end)>15){const {left,right,xmin,xmax}=this.bounds;const convert=x=>xmin+(Math.max(left,Math.min(right,x))-left)/(right-left)*(xmax-xmin);this.zoom=[Math.min(convert(start),convert(end)),Math.max(convert(start),convert(end))];}this.drag=null;this.draw();}try{canvas.releasePointerCapture(e.pointerId);}catch(_){}};
  this.reset=()=>{this.zoom=null;this.draw();};
  canvas.addEventListener('pointermove',this.move);canvas.addEventListener('pointerleave',this.leave);canvas.addEventListener('pointerdown',this.down);canvas.addEventListener('pointerup',this.up);canvas.addEventListener('dblclick',this.reset);
  canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Gráfico temporal: '+series.map(s=>s.label).join(', ')+'. Arraste para ampliar um intervalo; dê duplo clique para restaurar.');
 }
 setData(rows,aggregation='raw'){if(this.paused)return;this.rows=rows;this.options.aggregation=aggregation;this.draw();}
 setSeries(series,unit){this.options.series=series;this.options.unit=unit;this.zoom=null;this.canvas.setAttribute('aria-label','Gráfico temporal: '+(series.map(s=>s.label).join(', ')||'nenhum registrador selecionado')+'. Arraste para ampliar um intervalo; dê duplo clique para restaurar.');this.draw();}
 draw(){
  const canvas=this.canvas,ctx=this.ctx;if(!canvas.isConnected)return;
  const rect=canvas.getBoundingClientRect();const w=rect.width,hgt=rect.height;if(w<20||hgt<20)return;
  const dpr=Math.min(window.devicePixelRatio||1,2);if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(hgt*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(hgt*dpr);}
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,hgt);
  const css=getComputedStyle(document.documentElement),color=k=>css.getPropertyValue('--'+k).trim();
  const left=w<400?48:55,right=w-16,top=22,bottom=hgt-32;
  const all=this.rows;const valid=all.filter(r=>Number.isFinite(r.ts));
  ctx.font='10px system-ui';ctx.fillStyle=color('muted');
  if(valid.length<2){ctx.textAlign='center';ctx.fillText('Sem dados suficientes no intervalo',w/2,hgt/2);this.tip.hidden=true;return;}
  let xmin=this.zoom?.[0]??valid[0].ts,xmax=this.zoom?.[1]??valid.at(-1).ts;
  if(xmax<=xmin)xmax=xmin+1;
  const selected=valid.filter(r=>r.ts>=xmin&&r.ts<=xmax);let values=[];
  for(const r of selected)for(const s of this.options.series){if(Number.isFinite(r.data?.[s.key]))values.push(r.data[s.key]);if(r.extrema?.[s.key])values.push(r.extrema[s.key].min,r.extrema[s.key].max);}
  values=values.filter(Number.isFinite);
  if(!values.length){ctx.textAlign='center';ctx.fillText('Sem medições válidas · não é indicação de normalidade',w/2,hgt/2);this.tip.hidden=true;return;}
  let ymin=Math.min(...values),ymax=Math.max(...values);const pad=Math.max((ymax-ymin)*.18,.35);ymin-=pad;ymax+=pad;
  const x=t=>left+(t-xmin)/(xmax-xmin)*(right-left),y=v=>bottom-(v-ymin)/(ymax-ymin)*(bottom-top);
  this.bounds={left,right,top,bottom,xmin,xmax,ymin,ymax};
  ctx.textAlign='right';
  for(let i=0;i<5;i++){const v=ymin+(ymax-ymin)*i/4,yy=y(v);ctx.strokeStyle=color('line');ctx.lineWidth=.7;ctx.beginPath();ctx.moveTo(left,yy);ctx.lineTo(right,yy);ctx.stroke();ctx.fillStyle=color('faint');ctx.fillText(fmt(v,Math.abs(ymax-ymin)>50?0:1),left-9,yy+3);}
  ctx.textAlign='left';ctx.fillStyle=color('faint');ctx.fillText(this.options.unit,left,11);
  const timefmt=new Intl.DateTimeFormat('pt-BR',{timeZone:'America/Sao_Paulo',hour:'2-digit',minute:'2-digit',...(xmax-xmin>86400?{day:'2-digit',month:'2-digit'}:{})});
  const nx=w<450?4:6;for(let i=0;i<nx;i++){const tt=xmin+(xmax-xmin)*i/(nx-1);ctx.textAlign=i===0?'left':i===nx-1?'right':'center';ctx.fillStyle=color('faint');ctx.fillText(timefmt.format(new Date(tt*1000)),x(tt),bottom+21);}
  const diffs=valid.slice(1,70).map((r,i)=>r.ts-valid[i].ts).filter(v=>v>0).sort((a,b)=>a-b);const step=diffs[Math.floor(diffs.length/2)]||10;
  const gap=this.options.aggregation==='raw'?Math.max(45,step*3):step*1.8;
  ctx.save();ctx.beginPath();ctx.rect(left,top,right-left,bottom-top);ctx.clip();
  for(const [idx,s] of this.options.series.entries()){
   const lineColor=color(s.color||['cyan','lime','blue','purple'][idx%4]);
   // For aggregates, draw a min/max band; no claim that the mean is a raw sample.
   if(!s.dashed){ctx.fillStyle=lineColor;ctx.globalAlpha=.09;for(const r of selected){const e=r.extrema?.[s.key];if(e&&Number.isFinite(e.min)&&Number.isFinite(e.max)&&!r.has_gap&&(!Number.isFinite(r.interval_end)||r.interval_end>r.ts)){const hasInterval=Number.isFinite(r.interval_end)&&r.interval_end>r.ts;const width=Math.max(1,(right-left)*(hasInterval?r.interval_end-r.ts:r.resolution_seconds||step)/(xmax-xmin));ctx.fillRect(hasInterval?x(r.ts):x(r.ts)-width/2,y(e.max),width,Math.max(1,y(e.min)-y(e.max)));}}ctx.globalAlpha=1;}
   ctx.strokeStyle=lineColor;ctx.lineWidth=s.dashed?1.3:1.8;ctx.setLineDash(s.dashed?[5,4]:[]);ctx.beginPath();let prev=null;
   for(const r of valid){const val=r.data?.[s.key];if(!Number.isFinite(val)||r.quality==='bad'||r.quality==='stale'||r.has_gap){prev=null;continue;}
    const xx=x(r.ts),yy=y(val);if(!prev||r.ts-prev.ts>historyGapLimit(prev,r,gap))ctx.moveTo(xx,yy);else if(s.dashed){ctx.lineTo(xx,y(prev.val));ctx.lineTo(xx,yy);}else ctx.lineTo(xx,yy);prev={...r,val};}
   ctx.stroke();ctx.setLineDash([]);
  }
  if(this.drag){ctx.fillStyle=color('cyan');ctx.globalAlpha=.13;ctx.fillRect(Math.min(this.drag.start,this.drag.end),top,Math.abs(this.drag.end-this.drag.start),bottom-top);ctx.globalAlpha=1;}
  if(this.hover&&this.hover.x>=left&&this.hover.x<=right&&this.hover.y>=top&&this.hover.y<=bottom){
   const t=xmin+(this.hover.x-left)/(right-left)*(xmax-xmin);let r=selected.reduce((best,v)=>!best||Math.abs(v.ts-t)<Math.abs(best.ts-t)?v:best,null);
   if(r){const xx=x(r.ts);ctx.strokeStyle=color('faint');ctx.setLineDash([3,3]);ctx.beginPath();ctx.moveTo(xx,top);ctx.lineTo(xx,bottom);ctx.stroke();ctx.setLineDash([]);
    this.tip.innerHTML=`<small>${h(date(r.ts,true))}</small>${this.options.series.map(s=>`<div>${h(s.label)}: <b>${fmt(r.data?.[s.key],1)}</b></div>`).join('')}${r.extrema?'<small>Agregado · faixa min/máx preservada</small>':''}`;
    this.tip.hidden=false;this.tip.style.left=Math.min(Math.max(left,this.hover.x+15),w-this.tip.offsetWidth-10)+'px';this.tip.style.top=Math.max(12,this.hover.y-this.tip.offsetHeight-10)+'px';}
  }else this.tip.hidden=true;
  ctx.restore();
 }
 destroy(){this.ro.disconnect();this.tip.remove();for(const [event,fn] of [['pointermove',this.move],['pointerleave',this.leave],['pointerdown',this.down],['pointerup',this.up],['dblclick',this.reset]])this.canvas.removeEventListener(event,fn);}
}
