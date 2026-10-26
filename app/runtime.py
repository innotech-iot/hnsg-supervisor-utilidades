from __future__ import annotations
import asyncio
import copy
import logging
import math
import time
import threading
from collections import deque
from sqlalchemy import select, func, delete, or_
from .models import Asset, Controller, Tag, Sample, PointSnapshot, Alarm, Aggregate, Meta
from .database import asdict
from .modbus import read_controller
from .analysis import analyze, coverage, CATALOG
from .equipment import ALL_CATALOG, catalog_for, equipment_coverage
from .evidence import protected
from .fan_confirmation import evaluate as evaluate_fan, CODE as FAN_CODE
from .demo_plant import plant_values

log=logging.getLogger('hnsg.collector')


def demo_values(asset_id,stamp,overrides=None):
    """Synthetic values only. They never enter a LIVE database."""
    ov=overrides or {}; i=asset_id
    mode=int(ov.get('mode',0 if i in {5,14} else 1))
    sp=ov.get('temp_sp',22.0); hsp=ov.get('humidity_sp',55.0); fsp=ov.get('airflow_sp',2200.+i*60)
    phase=stamp/170+i*.7
    temperature=sp+.32*math.sin(phase)+.08*math.cos(phase*2)
    humidity=hsp+1.5*math.sin(phase*.7)
    cooling=48+12*math.sin(phase*.5)
    if i==3 and mode: temperature=sp+3.1+.25*math.sin(phase); cooling=98.4
    if i==7 and mode: temperature=sp+1.7*math.sin(stamp/38); cooling=55+27*math.sin(stamp/38+.5)
    if i==8 and mode: humidity=hsp+10.5+.5*math.cos(phase)
    running=mode!=0
    data={'temperature':round(temperature if running else sp+1.6,2),
          'temp_sp':float(sp),'humidity':round(humidity,2),'humidity_sp':float(hsp),
          'airflow':round(fsp*(1+.015*math.sin(phase)) if running else 0,1),'airflow_sp':float(fsp),
          'pressure':round(210+15*math.sin(phase) if running else 0,1),
          'cooling':round(cooling if running else 0,1),'heating':12.0 if i==8 and running else 0.,
          'fan_command':int(running),'fan_feedback':int(running),'mode':mode,
          'dehumidifying':int(i==8 and running)}
    # Demonstrate missing data without declaring equipment off.
    if i==11:
        return {k:None for k in data},'bad'
    return data,'good'

class Runtime:
    def __init__(self,db,settings):
        self.db=db; self.settings=settings
        self.lock=threading.RLock()
        self.latest={}; self.points={}; self.controllers={}
        self.rings={}; self.asset_kinds={}; self.controller_ids=[]
        self.overrides={}; self.tasks=[]; self.started=time.time()
        self.last_acquisition=None; self.last_persist=None; self.persist_error=None; self.analysis_error=None
        self.last_retention=None; self.last_ai=None; self.config_epoch=0
        self.llm_lock=asyncio.Lock()
        self.stopping=False

    def initialize(self):
        self.db.initialize()
        with self.db.session() as s:
            self.asset_kinds={a.id:a.kind for a in s.scalars(select(Asset))}
            self.rings={aid:deque(maxlen=1800) for aid in self.asset_kinds}
            self.controller_ids=list(s.scalars(select(Controller.id).order_by(Controller.id)))
            saved=s.get(Meta,'demo_overrides')
            if saved and self.settings.mode=='demo':
                import json
                self.overrides={int(k):v for k,v in json.loads(saved.value).items()}
            exists=s.scalar(select(Sample.id).limit(1))
        if self.settings.mode=='demo' and not exists and self.settings.seed_hours>0:
            self.seed()
        with self.db.session() as s:
            rows=s.scalars(select(Sample).where(Sample.ts>time.time()-1800).order_by(Sample.ts)).all()
            for row in rows:
                self.rings[row.asset_id].append({'ts':row.ts,'data':row.data,'quality':row.quality,
                    'source':row.source,'versions':row.versions})
        if self.settings.mode=='demo': self.demo_tick()

    def seed(self):
        if self.settings.mode!='demo':
            raise RuntimeError('Simulação permitida somente em DEMO')
        now=time.time(); start=now-self.settings.seed_hours*3600
        with self.db.session() as s:
            for j in range(int((now-start)/30)):
                ts=start+j*30
                for i,kind in self.asset_kinds.items():
                    if kind!='uta' and not self.settings.demo_full:continue
                    data,q=self.simulated_values(i,kind,ts)
                    s.add(Sample(asset_id=i,ts=ts,data=data,quality=q,source='demo',versions={'demo':'plant-1' if self.settings.demo_full else '1'}))
            self.db.audit(s,'system','demo_seed','database',{'hours':self.settings.seed_hours,'synthetic':True})

    def simulated_values(self,i,kind,stamp):
        if self.settings.mode!='demo':
            raise RuntimeError('Simulação permitida somente em DEMO')
        if self.settings.demo_full:
            return plant_values(i,kind,stamp,self.overrides.get(i),self.settings.demo_scenario)
        return demo_values(i,stamp,self.overrides.get(i))

    def demo_tick(self):
        if self.settings.mode!='demo':
            raise RuntimeError('Simulação permitida somente em DEMO')
        now=time.time()
        with self.db.session() as s:revisions={a.id:a.revision for a in s.scalars(select(Asset))}
        with self.lock:
            for i,kind in self.asset_kinds.items():
                if kind!='uta' and not self.settings.demo_full:continue
                data,q=self.simulated_values(i,kind,now)
                self.latest[i]={'ts':now,'data':data,'quality':q,'source':'demo',
                    'versions':{'demo':'plant-1' if self.settings.demo_full else '1','asset_revision':revisions[i],'config_epoch':self.config_epoch}}
                self.rings[i].append(copy.deepcopy(self.latest[i]))
            for cid in self.controller_ids:
                self.controllers[cid]={'status':'simulated','last_ok':now,'error':None,'duration_ms':0}
            self.last_acquisition=now

    def controller_config(self,cid):
        with self.db.session() as s:
            c=s.get(Controller,cid)
            tags=s.scalars(select(Tag).where(Tag.controller_id==cid,Tag.active==True,Tag.validated==True)).all()
            return asdict(c),[asdict(t) for t in tags]

    async def live_worker(self,cid):
        due={}
        while not self.stopping:
            begin=time.monotonic()
            try:
                epoch=self.config_epoch
                c,tags=await asyncio.to_thread(self.controller_config,cid)
                if not c['enabled'] or not c['assignment_confirmed'] or not c['host'] or not tags:
                    with self.lock:
                        self.controllers[cid]={'status':'unconfigured','last_ok':None,'error':'Conexão/mapa/vínculos pendentes','duration_ms':0}
                        self.points[cid]={}
                    await asyncio.sleep(self.settings.poll_seconds); continue
                now=time.time()
                selected=[t for t in tags if now>=due.get(t['id'],0)]
                if selected:
                    result=await asyncio.to_thread(read_controller,c,selected)
                    if epoch!=self.config_epoch:
                        due.clear()
                        continue
                    for t in selected: due[t['id']]=time.time()+max(self.settings.poll_seconds,t['poll_seconds'])
                    with self.lock:
                        points=self.points.setdefault(cid,{})
                        points.update(result['points'])
                        # Reimported/inactive IDs cannot continue to feed a mapped signal.
                        valid_ids={str(t['id']) for t in tags}
                        self.points[cid]={k:v for k,v in points.items() if k in valid_ids}
                        any_good=any(p['quality']=='good' for p in result['points'].values())
                        self.controllers[cid]={'status':'partial' if result['errors'] and any_good else ('online' if any_good else 'offline'),
                            'last_ok':time.time() if any_good else self.controllers.get(cid,{}).get('last_ok'),
                            'error':'; '.join(result['errors']) or None,'duration_ms':round((time.monotonic()-begin)*1000,1)}
                        self.last_acquisition=time.time()
                await asyncio.to_thread(self.update_live_assets,cid,tags)
            except asyncio.CancelledError: raise
            except Exception as exc:
                log.exception('Falha no coletor CLP %s',cid)
                with self.lock:
                    self.controllers[cid]={'status':'offline','last_ok':self.controllers.get(cid,{}).get('last_ok'),
                                           'error':str(exc)[:300],'duration_ms':0}
            await asyncio.sleep(max(.1,self.settings.poll_seconds-(time.monotonic()-begin)))

    def update_live_assets(self,cid,tags):
        now=time.time()
        with self.db.session() as s:
            revisions={a.id:a.revision for a in s.scalars(select(Asset).where(Asset.controller_id==cid))}
            controller_revision=s.get(Controller,cid).revision
        with self.lock:
            points=self.points.get(cid,{})
            for i in revisions:
                catalog=catalog_for(self.asset_kinds[i])
                data={k:None for k in catalog}; errors=0; good=0; observed_at={};newest=None
                versions={'asset_revision':revisions[i],'controller_revision':controller_revision,'config_epoch':self.config_epoch}
                relevant=[t for t in tags if t['asset_id']==i and t['semantic']]
                for t in relevant:
                    if t['semantic'] not in catalog:continue
                    p=points.get(str(t['id'])); fresh=p and now-p['ts']<=max(self.settings.stale_seconds,t['poll_seconds']*3)
                    if fresh and p['quality']=='good':
                        data[t['semantic']]=p['value']; good+=1
                        observed_at[t['semantic']]=p['ts']
                        newest=max(newest or 0,p['ts'])
                    else: errors+=1
                    versions[str(t['id'])]=t['map_revision']
                    versions[f"tag_revision:{t['id']}"]=t.get('revision')
                q='good' if good and not errors else ('partial' if good else 'bad')
                self.latest[i]={'ts':newest or now,'data':data,'quality':q,'source':'live','versions':versions,'observed_at':observed_at}
                self.rings[i].append(copy.deepcopy(self.latest[i])|{'ts':now})

    async def start(self):
        if not self.settings.run_collector: return
        if self.settings.mode=='demo': self.tasks.append(asyncio.create_task(self.demo_loop(),name='simulator'))
        else:
            self.tasks += [asyncio.create_task(self.live_worker(i),name=f'clp-{i}') for i in self.controller_ids]
        self.tasks += [asyncio.create_task(self.history_loop(),name='historian'),
                       asyncio.create_task(self.analysis_loop(),name='detectors'),
                       asyncio.create_task(self.retention_loop(),name='retention')]

    async def demo_loop(self):
        while not self.stopping:
            self.demo_tick()
            await asyncio.sleep(self.settings.poll_seconds)

    def persist(self):
        now=time.time()
        with self.lock:
            latest=copy.deepcopy(self.latest); points=copy.deepcopy(self.points)
        with self.db.session() as s:
            for i in self.asset_kinds:
                row=latest.get(i,{'data':{},'quality':'unknown','source':self.settings.mode,'versions':{},'ts':now})
                expired=now-row['ts']>self.settings.stale_seconds and row['quality'] in {'good','partial'}
                # Persist null values for stale acquisitions, not repetitions of old numbers.
                s.add(Sample(asset_id=i,ts=now,data={} if expired else row['data'],
                    quality='stale' if expired else row['quality'],source=row['source'],versions=row['versions']))
            # Complete tag snapshots once per minute, including controller-wide points.
            if int(now)//60!=int(self.last_persist or 0)//60:
                for cid, ps in points.items():
                    s.add(PointSnapshot(controller_id=cid,ts=now,data=ps))
        self.last_persist=now; self.persist_error=None

    async def history_loop(self):
        while not self.stopping:
            try: await asyncio.to_thread(self.persist)
            except Exception as exc:
                self.persist_error=str(exc)[:300]; log.exception('Falha na persistência')
            await asyncio.sleep(self.settings.history_seconds)

    def detect(self):
        now=time.time()
        with self.lock:
            rings={i:list(v) for i,v in self.rings.items()}; controllers=copy.deepcopy(self.controllers); points=copy.deepcopy(self.points)
        with self.db.session() as s:
            for a in s.scalars(select(Asset)).all():
                if a.kind!='uta':continue
                rows=rings[a.id]
                latest=rows[-1] if rows else None
                diagnosable=latest and latest['quality']=='good' and now-latest['ts']<=self.settings.stale_seconds and a.profile.get('validated')
                if not diagnosable: continue  # Unknown never normalizes existing process alarms.
                findings=analyze(rows,a.profile)
                fan=evaluate_fan(rows,a.profile,now,self.settings.stale_seconds,a.revision,self.config_epoch)
                if fan['state']=='mismatch':
                    findings.append({'code':FAN_CODE,'priority':'warning',
                        'title':'Ventilador: divergência persistente entre comando e retorno',
                        'evidence':fan['evidence']|{'profile_revision':a.revision}})
                active={x.key:x for x in s.scalars(select(Alarm).where(Alarm.asset_id==a.id,Alarm.active==True,Alarm.source=='detector'))}
                seen=set()
                for finding in findings:
                    key=f'uta:{a.id}:{finding["code"]}'; seen.add(key)
                    if key in active:
                        active[key].last_seen=now
                        active[key].evidence=(finding['evidence']|{'initial':active[key].evidence.get('initial',active[key].evidence)}) if finding['code']==FAN_CODE else finding['evidence']
                    else:
                        s.add(Alarm(key=key,asset_id=a.id,controller_id=a.controller_id,code=finding['code'],
                            title=finding['title'],priority=finding['priority'],source='detector',
                            evidence=(finding['evidence']|{'initial':copy.deepcopy(finding['evidence'])}) if finding['code']==FAN_CODE else finding['evidence'],first_seen=now,last_seen=now))
                for key,alarm in active.items():
                    if alarm.code==FAN_CODE and fan['state']!='agreement':continue
                    if key not in seen:
                        alarm.active=False;alarm.closed_at=now
                        if alarm.code==FAN_CODE:
                            alarm.evidence=alarm.evidence|{'recovery':fan['evidence']|{'profile_revision':a.revision}}
            if self.settings.mode=='live':
                for tag in s.scalars(select(Tag).where(Tag.active==True,Tag.validated==True,Tag.is_alarm==True)):
                    p=points.get(tag.controller_id,{}).get(str(tag.id))
                    if not p or p['quality']!='good' or now-p['ts']>max(self.settings.stale_seconds,tag.poll_seconds*3): continue
                    key=f'tag:{tag.id}:alarm'
                    current=s.scalar(select(Alarm).where(Alarm.key==key,Alarm.active==True))
                    triggered=p['value']==tag.alarm_value
                    evidence={'tag_id':tag.id,'symbol':tag.symbol,'value':p['value'],'trigger_value':tag.alarm_value,'map_revision':tag.map_revision,'timestamp':p['ts']}
                    if triggered and not current:
                        s.add(Alarm(key=key,asset_id=tag.asset_id,controller_id=tag.controller_id,code='controller_alarm',
                            title=tag.label or tag.description or tag.symbol,priority=tag.alarm_priority,source='controller',
                            evidence=evidence,first_seen=now,last_seen=now))
                    elif triggered and current:current.last_seen=now;current.evidence=evidence
                    elif current:current.active=False;current.closed_at=now
            for cid, state in controllers.items():
                key=f'clp:{cid}:communication'
                current=s.scalar(select(Alarm).where(Alarm.key==key,Alarm.active==True))
                failed=state['status'] in {'offline','partial'}
                if failed and not current:
                    s.add(Alarm(key=key,controller_id=cid,code='communication',title=f'CLP {cid}: falha de comunicação',
                        priority='warning',source='system',evidence={'error':state['error']},first_seen=now,last_seen=now))
                elif failed and current: current.last_seen=now
                elif current and state['status'] in {'online','simulated'}: current.active=False; current.closed_at=now
        self.analysis_error=None

    async def analysis_loop(self):
        while not self.stopping:
            try: await asyncio.to_thread(self.detect)
            except Exception as exc:
                self.analysis_error=str(exc)[:300]; log.exception('Falha na análise')
            await asyncio.sleep(10)

    def rollup(self):
        """Roll up closed hours, preserve extrema/quality; delete raw only after aggregate exists.
        Missing intervals remain missing. No infinite catch-up in one transaction.
        """
        now=time.time(); closed_hour=int(now//3600)*3600
        with self.db.session() as s:
            for aid in self.asset_kinds:
                hour_expr=(func.floor(Sample.ts/3600)*3600).label('sample_hour')
                consolidated=select(Aggregate.id).where(Aggregate.asset_id==Sample.asset_id,
                    Aggregate.hour<=Sample.ts,Sample.ts<Aggregate.hour+3600).correlate(Sample).exists()
                pending=s.scalars(select(hour_expr).where(Sample.asset_id==aid,Sample.ts<closed_hour,
                    ~consolidated,or_(hour_expr>=now-self.settings.aggregate_days*86400,
                        ~protected(Sample))).distinct().order_by(hour_expr).limit(48)).all()
                for hour in pending:
                    rows=s.scalars(select(Sample).where(Sample.asset_id==aid,Sample.ts>=hour,Sample.ts<hour+3600)).all()
                    if not rows: continue
                    data={}
                    for key in catalog_for(self.asset_kinds[aid]):
                        values=[r.data[key] for r in rows if r.quality in {'good','partial'} and r.data.get(key) is not None]
                        if values:
                            data[key]={'mean':sum(values)/len(values),'min':min(values),'max':max(values),'count':len(values)}
                    s.add(Aggregate(asset_id=aid,hour=float(hour),data=data,count=len(rows),valid_count=sum(r.quality=='good' for r in rows)))
                s.flush()
                cutoff=now-self.settings.history_days*86400
                old_hours=s.scalars(select(Aggregate.hour).where(Aggregate.asset_id==aid,Aggregate.hour<cutoff-3600)).all()
                # Incident windows survive ordinary history retention, including invalid quality.
                for h in old_hours:
                    s.execute(delete(Sample).where(Sample.asset_id==aid,Sample.ts>=h,Sample.ts<h+3600,
                        ~protected(Sample)))
            s.execute(delete(Aggregate).where(Aggregate.hour<now-self.settings.aggregate_days*86400))
            s.execute(delete(PointSnapshot).where(PointSnapshot.ts<now-self.settings.history_days*86400,
                ~protected(PointSnapshot)))
        self.last_retention=now

    async def retention_loop(self):
        # Do not delay first screen with startup aggregation.
        await asyncio.sleep(90)
        while not self.stopping:
            try: await asyncio.to_thread(self.rollup)
            except Exception: log.exception('Falha na agregação/retenção')
            await asyncio.sleep(3600)

    def snapshot(self):
        now=time.time()
        with self.lock:
            latest=copy.deepcopy(self.latest); controllers=copy.deepcopy(self.controllers)
            trends={i:[r['data'].get('temperature' if self.asset_kinds[i]=='uta' else 'supply_temperature') for r in list(v)[-30:]] for i,v in self.rings.items()}
        with self.db.session() as s:
            assets=s.scalars(select(Asset).order_by(Asset.id)).all()
            alarms=s.scalars(select(Alarm).where(Alarm.active==True)).all()
            clps=[asdict(c)|controllers.get(c.id,{'status':'unconfigured','last_ok':None,'error':None})
                  for c in s.scalars(select(Controller).order_by(Controller.id)).all()]
            result=[]
            for a in assets:
                row=latest.get(a.id,{'ts':None,'data':{},'quality':'unknown','source':self.settings.mode})
                age=None if row['ts'] is None else max(0,now-row['ts'])
                q=row['quality']
                if age is not None and age>self.settings.stale_seconds and q in {'good','partial'}: q='stale'
                data=row['data'] if q in {'good','partial'} else {k:None for k in catalog_for(a.kind)}
                lastvals=trends.get(a.id,[])
                relevant=[x for x in alarms if x.asset_id==a.id or (x.asset_id is None and x.controller_id==a.controller_id)]
                status='unknown' if a.kind!='uta' or q not in {'good','partial'} else ('running' if data.get('fan_feedback')==1 else ('stopped' if data.get('fan_feedback')==0 else 'unknown'))
                result.append(asdict(a)|{'data':data,'quality':q,'source':row['source'],'ts':row['ts'],'age':age,
                    'status':status,'alarm_count':len(relevant),'alarms':[asdict(x) for x in relevant],
                    'coverage':equipment_coverage(a.kind,data,a.profile),'trend':lastvals})
        return {'mode':self.settings.mode,'now':now,'assets':result,'controllers':clps,
                'health':{'acquisition':self.last_acquisition,'persistence':self.last_persist,'persistence_error':self.persist_error,
                          'analysis_error':self.analysis_error,'uptime':now-self.started,'llm_enabled':self.settings.ollama_enabled,
                          'live_writes_enabled':False}}

    async def stop(self):
        self.stopping=True
        for task in self.tasks: task.cancel()
        await asyncio.gather(*self.tasks,return_exceptions=True)
