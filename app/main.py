from __future__ import annotations
import asyncio
import csv
import hmac
import io
import json
import logging
import math
import os
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from filelock import FileLock, Timeout
from sqlalchemy import select, delete, func
from . import __version__
from .config import Settings, ROOT
from .database import Database, asdict
from .models import (User, Session, Controller, Asset, Tag, ImportBatch, Sample, Alarm, Audit,
                     Ticket, Room, Knowledge, Command, Meta)
from .security import hash_password, verify_password, token_hash, new_token, csv_safe, LoginLimiter
from .runtime import Runtime
from .importer import parse_protocol, signature
from .analysis import CATALOG
from .equipment import ALL_CATALOG, catalog_for
from .history import history
from .evidence import incident_evidence
from . import schemas as S
from .ai import explain

logger=logging.getLogger('hnsg')


def create_app(settings:Settings|None=None) -> FastAPI:
    settings=settings or Settings.from_env()
    db=Database(settings); runtime=Runtime(db,settings); limiter=LoginLimiter()
    worker_lock=FileLock(str(settings.data_dir/'collector.lock'))

    @asynccontextmanager
    async def lifespan(app):
        try: worker_lock.acquire(timeout=0)
        except Timeout: raise RuntimeError('Outra instância está usando este diretório. Use exatamente UM worker.')
        try:
            await asyncio.to_thread(runtime.initialize)
            await asyncio.to_thread(runtime.detect)
            await runtime.start()
            yield
        finally:
            await runtime.stop()
            db.close(); worker_lock.release()

    app=FastAPI(title='HNSG · Innotech',version=__version__,lifespan=lifespan,
                docs_url=None,redoc_url=None,openapi_url=None)
    app.state.runtime=runtime; app.state.db=db; app.state.settings=settings

    @app.middleware('http')
    async def boundary(request:Request,call_next):
        if request.method not in {'GET','HEAD','OPTIONS'}:
            origin=request.headers.get('origin')
            if origin and urlparse(origin).netloc != request.headers.get('host',''):
                return JSONResponse({'detail':'Origem não autorizada'},status_code=403)
            try:
                size=int(request.headers.get('content-length','0'))
            except ValueError:
                return JSONResponse({'detail':'Tamanho inválido'},status_code=400)
            if size>2_100_000: return JSONResponse({'detail':'Corpo excede 2 MB'},status_code=413)
            body=bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body)>2_100_000: return JSONResponse({'detail':'Corpo excede 2 MB'},status_code=413)
            request._body=bytes(body)
        try: response=await call_next(request)
        except Exception:
            logger.exception('Erro não tratado')
            return JSONResponse({'detail':'Falha interna. Verifique a saúde do sistema; nenhuma ação é presumida concluída.'},status_code=500)
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api') else 'no-cache'
        return response

    def auth(request:Request):
        token=request.cookies.get('hnsg_session','')
        if not token: raise HTTPException(401,'Autenticação necessária')
        with db.session() as s:
            session=s.get(Session,token_hash(token))
            if not session or session.expires<time.time(): raise HTTPException(401,'Sessão expirada')
            user=s.get(User,session.user_id)
            if not user or not user.active: raise HTTPException(401,'Conta indisponível')
            if request.method not in {'GET','HEAD','OPTIONS'}:
                supplied=request.headers.get('x-csrf-token','')
                if not supplied or not hmac.compare_digest(supplied,session.csrf): raise HTTPException(403,'Token CSRF inválido')
            return {'id':user.id,'username':user.username,'name':user.name,'role':user.role,'csrf':session.csrf,'session_id':session.id}
    def operator(u=Depends(auth)):
        if u['role'] not in {'operator','admin'}: raise HTTPException(403,'Perfil somente visualização')
        return u
    def admin(u=Depends(auth)):
        if u['role']!='admin': raise HTTPException(403,'Acesso administrativo necessário')
        return u
    def public_user(u): return {k:u[k] for k in ('id','username','name','role')}

    @app.post('/api/auth/login')
    def login(body:S.Login,request:Request,response:Response):
        key=(request.client.host if request.client else 'local')+'|'+body.username.lower()
        if not limiter.allow(key): raise HTTPException(429,'Muitas tentativas; aguarde cinco minutos')
        with db.session() as s:
            user=s.scalar(select(User).where(User.username==body.username))
            if not user or not user.active or not verify_password(body.password,user.password_hash):
                raise HTTPException(401,'Usuário ou senha inválidos')
            token=new_token(); csrf=new_token()
            s.execute(delete(Session).where(Session.expires<time.time()))
            s.add(Session(id=token_hash(token),user_id=user.id,csrf=csrf,expires=time.time()+settings.session_hours*3600))
            db.audit(s,user.username,'login','session')
            userinfo={'id':user.id,'username':user.username,'name':user.name,'role':user.role}
        limiter.clear(key)
        response.set_cookie('hnsg_session',token,httponly=True,secure=settings.secure_cookie,samesite='strict',max_age=settings.session_hours*3600,path='/')
        return {'user':userinfo,'csrf':csrf,'mode':settings.mode}

    @app.get('/api/session')
    def session(u=Depends(auth)):
        return {'user':public_user(u),'csrf':u['csrf'],'mode':settings.mode,'version':__version__}

    @app.post('/api/auth/logout')
    def logout(response:Response,u=Depends(auth)):
        with db.session() as s:
            s.execute(delete(Session).where(Session.id==u['session_id'])); db.audit(s,u['username'],'logout','session')
        response.delete_cookie('hnsg_session',path='/'); return {'ok':True}

    @app.post('/api/auth/password')
    def password(body:S.PasswordChange,response:Response,u=Depends(auth)):
        with db.session() as s:
            user=s.get(User,u['id'])
            if not verify_password(body.current,user.password_hash): raise HTTPException(403,'Senha atual inválida')
            user.password_hash=hash_password(body.password)
            s.execute(delete(Session).where(Session.user_id==user.id))
            db.audit(s,u['username'],'password_changed','user:'+str(user.id))
        response.delete_cookie('hnsg_session',path='/'); return {'ok':True,'reauthenticate':True}

    @app.get('/api/state')
    def state(u=Depends(auth)): return runtime.snapshot()

    @app.get('/api/catalog')
    def catalog(u=Depends(auth)): return {k:v|{'kinds':['uta'] if k in CATALOG else ['cag','caq']} for k,v in ALL_CATALOG.items()}

    def require_asset(asset_id,status_code=404):
        with db.session() as s:
            asset=s.get(Asset,asset_id)
            if not asset:raise HTTPException(status_code,'Equipamento não encontrado')
            return asset

    @app.get('/api/assets/{asset_id}/live')
    def live_series(asset_id:int,minutes:int=Query(15,ge=1,le=30),u=Depends(auth)):
        import copy
        require_asset(asset_id)
        now=time.time()
        with runtime.lock:
            rows=copy.deepcopy([r for r in runtime.rings[asset_id] if r['ts']>=now-minutes*60])
        if rows and now-rows[-1]['ts']>settings.stale_seconds:
            rows.append({'ts':now,'data':{},'quality':'stale'})
        return {'rows':rows,'aggregation':'raw','source':settings.mode,'buffered':True,
                'start':now-minutes*60,'end':now,'notice':'Buffer de aquisição; não é confirmação de persistência.'}

    @app.get('/api/assets/{asset_id}/history')
    def asset_history(asset_id:int,hours:float=Query(3,ge=.01,le=8784),start:float|None=None,end:float|None=None,u=Depends(auth)):
        require_asset(asset_id)
        now=time.time(); finish=end if end is not None else now; begin=start if start is not None else finish-hours*3600
        if not all(math.isfinite(x) for x in (finish,begin)): raise HTTPException(422,'Período inválido')
        try: return history(db,asset_id,begin,finish)
        except ValueError as exc: raise HTTPException(422,str(exc))

    @app.get('/api/assets/{asset_id}/export.csv')
    def export(asset_id:int,hours:float=Query(24,ge=.01,le=168),u=Depends(auth)):
        asset=require_asset(asset_id)
        import datetime
        with db.session() as s:
            rows=s.scalars(select(Sample).where(Sample.asset_id==asset_id,Sample.ts>=time.time()-hours*3600).order_by(Sample.ts).limit(100001)).all()
            if len(rows)>100000:raise HTTPException(413,'Exportação excede 100 mil linhas; reduza o intervalo')
            buf=io.StringIO(); writer=csv.writer(buf,delimiter=';')
            keys=list(catalog_for(asset.kind))
            writer.writerow(['utc','uta' if asset.kind=='uta' else 'equipamento','origem','qualidade']+[csv_safe(k) for k in keys])
            for row in rows:
                writer.writerow([datetime.datetime.fromtimestamp(row.ts,datetime.timezone.utc).isoformat(),asset_id,row.source,row.quality]+[row.data.get(k,'') for k in keys])
            db.audit(s,u['username'],'export_history',f'uta:{asset_id}',{'hours':hours,'rows':len(rows)})
        return Response('\ufeff'+buf.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="{asset.kind}-{asset_id:02}-historico.csv"'})

    @app.get('/api/alarms')
    def alarms(active:bool|None=None,asset_id:int|None=None,limit:int=Query(200,ge=1,le=1000),u=Depends(auth)):
        with db.session() as s:
            q=select(Alarm).order_by(Alarm.active.desc(),Alarm.first_seen.desc()).limit(limit)
            if active is not None: q=q.where(Alarm.active==active)
            if asset_id is not None: q=q.where(Alarm.asset_id==asset_id)
            return {'alarms':[asdict(a) for a in s.scalars(q)]}

    @app.get('/api/alarms/{alarm_id}/evidence')
    def alarm_evidence(alarm_id:int,kind:str=Query('samples',pattern='^(samples|points)$'),
                       after:int=Query(0,ge=0),limit:int=Query(200,ge=1,le=1000),u=Depends(auth)):
        with db.session() as s:
            alarm=s.get(Alarm,alarm_id)
            if not alarm:raise HTTPException(404,'Ocorrência não encontrada')
            return incident_evidence(s,alarm,kind,after,limit)

    @app.post('/api/alarms/{alarm_id}/ack')
    def ack(alarm_id:int,u=Depends(operator)):
        with db.session() as s:
            a=s.get(Alarm,alarm_id)
            if not a: raise HTTPException(404,'Ocorrência não encontrada')
            if not a.ack_at:
                a.ack_at=time.time(); a.ack_user=u['username']; db.audit(s,u['username'],'alarm_ack',alarm_id)
            return asdict(a)

    @app.post('/api/alarms/{alarm_id}/review')
    def review_alarm(alarm_id:int,body:S.Review,u=Depends(operator)):
        with db.session() as s:
            a=s.get(Alarm,alarm_id)
            if not a: raise HTTPException(404,'Ocorrência não encontrada')
            old={'review':a.review,'note':a.note}; a.review=body.review; a.note=body.note
            db.audit(s,u['username'],'alarm_review',alarm_id,{'before':old,'after':body.model_dump()})
            return asdict(a)

    @app.get('/api/audit')
    def audit(limit:int=Query(150,ge=1,le=1000),before:int|None=None,u=Depends(operator)):
        with db.session() as s:
            q=select(Audit).order_by(Audit.id.desc()).limit(limit)
            if before:q=q.where(Audit.id<before)
            return {'events':[asdict(x) for x in s.scalars(q)]}

    @app.get('/api/controllers')
    def controllers(u=Depends(auth)):return runtime.snapshot()['controllers']

    @app.put('/api/controllers/{controller_id}')
    def update_controller(controller_id:int,body:S.ControllerPatch,u=Depends(admin)):
        import ipaddress
        if body.host:
            try: addr=ipaddress.ip_address(body.host)
            except ValueError: raise HTTPException(422,'Informe IP explícito; nomes DNS não são usados para CLPs')
            if addr.is_multicast or addr.is_unspecified:raise HTTPException(422,'IP de destino inválido')
        with db.session() as s:
            c=s.get(Controller,controller_id)
            if not c: raise HTTPException(404,'CLP não encontrado')
            if c.revision!=body.expected_revision: raise HTTPException(409,'Configuração foi alterada; atualize')
            count=s.scalar(select(func.count(Tag.id)).where(Tag.controller_id==controller_id,Tag.active==True,Tag.validated==True))
            if body.enabled and (not body.assignment_confirmed or not body.host or not count):
                raise HTTPException(422,'Confirme a distribuição, IP e pelo menos um ponto validado antes de habilitar')
            old=asdict(c)
            for k in ['host','port','unit_id','enabled','assignment_confirmed']:setattr(c,k,getattr(body,k))
            c.revision+=1
            db.audit(s,u['username'],'controller_update',controller_id,{'before':old,'after':body.model_dump()})
            result=asdict(c)
            affected=list(s.scalars(select(Asset.id).where(Asset.controller_id==controller_id)))
        with runtime.lock:
            runtime.config_epoch+=1
            runtime.points.pop(controller_id,None)
            for aid in affected:
                runtime.rings[aid].clear();runtime.latest.pop(aid,None)
        return result

    @app.put('/api/assets/{asset_id}')
    def update_asset(asset_id:int,body:S.AssetPatch,u=Depends(admin)):
        with db.session() as s:
            a=s.get(Asset,asset_id)
            if not a:raise HTTPException(404,'UTA não encontrada')
            if a.kind!='uta' and body.profile.validated:
                raise HTTPException(422,'Perfil de ventilação não pode habilitar diagnóstico de central')
            if a.kind=='uta' and body.profile.validated and body.profile.fan_confirmation_validated:
                capacity=(runtime.rings[a.id].maxlen-1)*settings.poll_seconds
                if body.profile.settling_seconds+body.profile.persistence_seconds>capacity:
                    raise HTTPException(422,f'Estabilização + persistência excede a janela nominal do buffer ({capacity:g} s); revise o perfil')
            if a.revision!=body.expected_revision:raise HTTPException(409,'Outra alteração ocorreu; atualize a tela')
            old=asdict(a); a.name=body.name; a.sector=body.sector; a.criticality=body.criticality
            a.profile=(body.profile.model_dump() if a.kind=='uta' else {'validated':False})|{'demo_only':settings.mode=='demo'}; a.revision+=1
            db.audit(s,u['username'],'asset_update',asset_id,{'before':old,'after':body.model_dump()})
            result=asdict(a)
        with runtime.lock:
            runtime.config_epoch+=1;runtime.rings[asset_id].clear()
        return result

    @app.get('/api/tags')
    def tags(controller_id:int|None=None,asset_id:int|None=None,u=Depends(auth)):
        with db.session() as s:
            q=select(Tag).where(Tag.active==True).order_by(Tag.controller_id,Tag.address)
            if controller_id:q=q.where(Tag.controller_id==controller_id)
            if asset_id:q=q.where(Tag.asset_id==asset_id)
            rows=[asdict(t) for t in s.scalars(q).all()]
        with runtime.lock:
            for t in rows:
                t['write_enabled']=False
                t['reading']=runtime.points.get(t['controller_id'],{}).get(str(t['id']))
                if t['reading'] and time.time()-t['reading']['ts']>max(settings.stale_seconds,t['poll_seconds']*3):
                    t['reading']=t['reading']|{'quality':'stale','value':None}
        return {'tags':rows,'carel_dialect_verified':False}

    @app.put('/api/tags/{tag_id}')
    def update_tag(tag_id:int,body:S.TagPatch,u=Depends(admin)):
        if body.semantic and body.semantic not in ALL_CATALOG:raise HTTPException(422,'Papel funcional não reconhecido')
        if body.semantic and not body.asset_id:raise HTTPException(422,'Papel funcional requer associação à UTA')
        with db.session() as s:
            tag=s.get(Tag,tag_id)
            if not tag or not tag.active:raise HTTPException(404,'Ponto não encontrado/versão inativa')
            if tag.revision!=body.expected_revision:raise HTTPException(409,'Ponto alterado; atualize')
            if body.asset_id:
                a=s.get(Asset,body.asset_id)
                if not a:raise HTTPException(422,'Equipamento não encontrado')
                if a.controller_id!=tag.controller_id:raise HTTPException(422,'Equipamento pertence a outro CLP')
                if body.semantic and body.semantic not in catalog_for(a.kind):
                    raise HTTPException(422,'Papel funcional incompatível com o tipo de equipamento')
                if a.kind!='uta' and body.validated and body.semantic in {'supply_temperature','return_temperature'} and tag.unit.strip()!='°C':
                    raise HTTPException(422,'Temperatura de água requer unidade °C explícita no mapa; confirme unidade e escala, sem conversão automática')
                other=s.scalar(select(Tag.id).where(Tag.id!=tag.id,Tag.active==True,Tag.asset_id==body.asset_id,Tag.semantic==body.semantic)) if body.semantic else None
                if other:raise HTTPException(409,'Já existe ponto ativo com esse papel na UTA')
            old=asdict(tag)
            for k in ['asset_id','semantic','label','validated','poll_seconds','is_alarm','alarm_value','alarm_priority']:setattr(tag,k,getattr(body,k))
            tag.instrument={'location':body.sensor_location,'model':body.sensor_model,'calibration_due':body.calibration_due}
            tag.revision+=1
            db.audit(s,u['username'],'tag_mapping',tag.id,{'before':old,'after':body.model_dump()})
            result=asdict(tag)|{'write_enabled':False}
            affected={old.get('asset_id'),tag.asset_id}
        with runtime.lock:
            runtime.config_epoch+=1
            if settings.mode=='live':
                runtime.points.get(result['controller_id'],{}).pop(str(tag_id),None)
                for aid in affected:
                    if aid:runtime.latest.pop(aid,None);runtime.rings[aid].clear()
        return result

    @app.post('/api/imports/preview')
    def preview(body:S.Preview,u=Depends(admin)):
        if not body.filename.lower().endswith('.txt'):raise HTTPException(422,'Selecione um arquivo TXT')
        p=parse_protocol(body.text,body.address_base,body.delimiter)
        with db.session() as s:
            c=s.get(Controller,body.controller_id)
            if not c:raise HTTPException(404,'CLP não encontrado')
            current={t.symbol:asdict(t) for t in s.scalars(select(Tag).where(Tag.controller_id==c.id,Tag.active==True))}
            names={t['symbol'] for t in p['tags']}
            diff={'added':[t['symbol'] for t in p['tags'] if t['symbol'] not in current],
                  'changed':[t['symbol'] for t in p['tags'] if t['symbol'] in current and signature(t)!=signature(current[t['symbol']])],
                  'removed':sorted(set(current)-names),
                  'unchanged':[t['symbol'] for t in p['tags'] if t['symbol'] in current and signature(t)==signature(current[t['symbol']])]}
            p['diff']=diff;p['previous_revision']=c.map_revision
            bid=new_token()[:36]
            b=ImportBatch(id=bid,controller_id=c.id,filename=Path(body.filename).name,sha256=p['sha256'],raw_text=body.text,parsed=p)
            s.add(b);db.audit(s,u['username'],'import_preview',c.id,{'batch':bid,'sha256':p['sha256'],'errors':len(p['errors'])})
        return {'id':bid,'parsed':p}

    @app.post('/api/imports/{batch_id}/activate')
    def activate(batch_id:str,body:S.Activate,u=Depends(admin)):
        if body.confirmation!='CONFIRMO MAPA DE LEITURA':raise HTTPException(422,'Confirmação explícita necessária')
        with db.session() as s:
            b=s.get(ImportBatch,batch_id)
            if not b:raise HTTPException(404,'Prévia não encontrada')
            if b.activated:raise HTTPException(409,'Prévia já ativada')
            if not b.parsed['activatable']:raise HTTPException(422,'Arquivo contém pendências e não pode ser ativado')
            c=s.get(Controller,b.controller_id)
            if c.map_revision!=b.parsed['previous_revision']:raise HTTPException(409,'Mapa mudou após a prévia; importe novamente')
            current={t.symbol:t for t in s.scalars(select(Tag).where(Tag.controller_id==c.id,Tag.active==True))}
            revision=c.map_revision+1
            for t in current.values():t.active=False
            for record in b.parsed['tags']:
                data={k:record[k] for k in ('symbol','description','area','address','data_type','scale','offset','unit','access','word_order','byte_order')}
                old=current.get(record['symbol'])
                same=old is not None and signature(asdict(old))==signature(record)
                s.add(Tag(controller_id=c.id,map_revision=revision,**data,
                          asset_id=old.asset_id if same else None,semantic=old.semantic if same else None,
                          label=old.label if old else '',validated=old.validated if same else False,
                          poll_seconds=old.poll_seconds if same else 5,
                          is_alarm=old.is_alarm if same else False, alarm_value=old.alarm_value if same else 1,
                          alarm_priority=old.alarm_priority if same else 'warning', instrument=old.instrument if same else {}))
            c.map_revision=revision;c.revision+=1;c.enabled=False;b.activated=True
            db.audit(s,u['username'],'import_activate',c.id,{'batch':batch_id,'revision':revision,'diff':b.parsed['diff'],'connection_disabled':True})
            cid=c.id
        with db.session() as s:
            affected=list(s.scalars(select(Asset.id).where(Asset.controller_id==cid)))
        with runtime.lock:
            runtime.config_epoch+=1
            runtime.points[cid]={}
            for aid in affected:
                if settings.mode=='live':
                    runtime.latest.pop(aid,None);runtime.rings[aid].clear()
        return {'ok':True,'revision':revision,'tags':len(b.parsed['tags']),'connection_disabled':True,'writes_enabled':False}

    @app.get('/api/tickets')
    def tickets(u=Depends(auth)):
        with db.session() as s:return {'tickets':[asdict(x) for x in s.scalars(select(Ticket).order_by(Ticket.id.desc()).limit(500))]}
    @app.post('/api/tickets')
    def add_ticket(body:S.TicketCreate,u=Depends(operator)):
        if body.asset_id is not None:require_asset(body.asset_id,422)
        with db.session() as s:
            x=Ticket(**body.model_dump(),username=u['username']);s.add(x);s.flush()
            db.audit(s,u['username'],'ticket_create',x.id,body.model_dump());return asdict(x)
    @app.put('/api/tickets/{ticket_id}')
    def update_ticket(ticket_id:int,body:S.TicketPatch,u=Depends(operator)):
        with db.session() as s:
            x=s.get(Ticket,ticket_id)
            if not x:raise HTTPException(404,'Registro não encontrado')
            old=asdict(x);x.state=body.state;x.details=body.details;x.updated=time.time()
            db.audit(s,u['username'],'ticket_update',x.id,{'before':old,'after':body.model_dump()});return asdict(x)
    @app.get('/api/rooms')
    def rooms(u=Depends(auth)):
        with db.session() as s:return {'rooms':[asdict(x) for x in s.scalars(select(Room).order_by(Room.asset_id,Room.name))]}
    @app.post('/api/rooms')
    def add_room(body:S.RoomCreate,u=Depends(admin)):
        require_asset(body.asset_id,422)
        with db.session() as s:
            x=Room(**body.model_dump());s.add(x);s.flush()
            db.audit(s,u['username'],'room_create',x.id,body.model_dump());return asdict(x)
    @app.get('/api/knowledge')
    def knowledge(u=Depends(auth)):
        with db.session() as s:
            q=select(Knowledge).order_by(Knowledge.id.desc())
            if u['role']!='admin':q=q.where(Knowledge.approved==True)
            return {'documents':[asdict(x) for x in s.scalars(q)]}
    @app.post('/api/knowledge')
    def add_knowledge(body:S.KnowledgeCreate,u=Depends(admin)):
        if body.asset_id is not None:require_asset(body.asset_id,422)
        with db.session() as s:
            x=Knowledge(**body.model_dump());s.add(x);s.flush()
            db.audit(s,u['username'],'knowledge_create',x.id,{'title':x.title,'revision':x.revision,'approved':x.approved});return asdict(x)

    @app.put('/api/knowledge/{document_id}')
    def edit_knowledge(document_id:int,body:S.KnowledgeCreate,u=Depends(admin)):
        if body.asset_id is not None:require_asset(body.asset_id,422)
        with db.session() as s:
            x=s.get(Knowledge,document_id)
            if not x:raise HTTPException(404,'Documento não encontrado')
            old=asdict(x)
            for key,value in body.model_dump().items():setattr(x,key,value)
            db.audit(s,u['username'],'knowledge_revision',document_id,{'before':old,'after':body.model_dump()})
            return asdict(x)

    @app.post('/api/ai/explain')
    async def ai_explain(body:S.AIQuestion,u=Depends(auth)):
        require_asset(body.asset_id)
        try:result=await explain(runtime,body.asset_id,body.question,body.history)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc
        def record():
            with db.session() as s:
                db.audit(s,u['username'],'ai_explanation',body.asset_id,{'engine':result['engine'],
                    'question':body.question,'explanation':result['explanation'],'evidence':result['evidence'],
                    'sources':[{'id':x['id'],'revision':x['revision']} for x in result['sources']],
                    'model':result.get('model'),'warning':result['warning']})
        await asyncio.to_thread(record)
        return result

    @app.get('/api/users')
    def users(u=Depends(admin)):
        with db.session() as s:return {'users':[{k:getattr(x,k) for k in ['id','username','name','role','active']} for x in s.scalars(select(User).order_by(User.id))]}
    @app.post('/api/users')
    def add_user(body:S.UserCreate,u=Depends(admin)):
        with db.session() as s:
            if s.scalar(select(User.id).where(User.username==body.username)):raise HTTPException(409,'Usuário já existe')
            x=User(username=body.username,name=body.name,role=body.role,password_hash=hash_password(body.password))
            s.add(x);s.flush();db.audit(s,u['username'],'user_create',x.id,{'username':x.username,'role':x.role})
            return {'id':x.id,'username':x.username}
    @app.put('/api/users/{user_id}')
    def edit_user(user_id:int,body:S.UserPatch,u=Depends(admin)):
        if user_id==u['id'] and (not body.active or body.role!='admin'):raise HTTPException(422,'Não desative/rebaixe sua própria conta administrativa')
        with db.session() as s:
            x=s.get(User,user_id)
            if not x:raise HTTPException(404,'Usuário não encontrado')
            x.active=body.active;x.role=body.role
            s.execute(delete(Session).where(Session.user_id==x.id))
            db.audit(s,u['username'],'user_update',user_id,body.model_dump());return {'ok':True}

    @app.post('/api/commands/prepare')
    def prepare(body:S.Prepare,u=Depends(operator)):
        if settings.mode!='demo':raise HTTPException(403,'Escrita em CLP não implementada/liberada nesta entrega. Somente leitura até comissionamento.')
        if require_asset(body.asset_id).kind!='uta':raise HTTPException(403,'Ajustes simulados disponíveis somente para UTAs')
        ranges={'temp_sp':(16,30),'humidity_sp':(30,70),'airflow_sp':(500,8000),'mode':(0,2)}
        lo,hi=ranges[body.semantic]
        if not lo<=body.value<=hi or (body.semantic=='mode' and body.value not in {0,1,2}):raise HTTPException(422,'Valor fora da faixa demonstrativa')
        row=next(a for a in runtime.snapshot()['assets'] if a['id']==body.asset_id)
        current=row['data'].get(body.semantic)
        if row['quality']!='good' or row['age'] is None or row['age']>settings.stale_seconds:raise HTTPException(409,'Dados inválidos/desatualizados; comando bloqueado')
        if current is None or not math.isclose(current,body.expected,rel_tol=0,abs_tol=1e-6):raise HTTPException(409,'Valor atual mudou; atualize antes de confirmar')
        cid=new_token();expires=time.time()+20
        with db.session() as s:
            s.add(Command(id=cid,user_id=u['id'],asset_id=body.asset_id,semantic=body.semantic,before=current,requested=body.value,expires=expires))
            db.audit(s,u['username'],'demo_command_prepare',cid,body.model_dump())
        return {'id':cid,'expires':expires,'simulated':True,'asset_id':body.asset_id,'semantic':body.semantic,'before':current,'requested':body.value}

    @app.post('/api/commands/{command_id}/confirm')
    def confirm(command_id:str,u=Depends(operator)):
        if settings.mode!='demo':raise HTTPException(403,'Escrita industrial bloqueada')
        with db.session() as s:
            c=s.get(Command,command_id)
            if not c or c.user_id!=u['id']:raise HTTPException(404,'Comando não encontrado para este usuário')
            if c.state!='prepared' or c.expires<time.time():raise HTTPException(409,'Comando expirado/já utilizado; não será reenviado')
            with runtime.lock:
                current=runtime.latest.get(c.asset_id,{})
                value=current.get('data',{}).get(c.semantic)
                if current.get('quality')!='good' or time.time()-current.get('ts',0)>settings.stale_seconds or value is None or not math.isclose(value,c.before,abs_tol=1e-6):
                    raise HTTPException(409,'Estado mudou; solicite uma nova confirmação')
                overrides={i:dict(v) for i,v in runtime.overrides.items()}
                overrides.setdefault(c.asset_id,{})[c.semantic]=c.requested
            c.state='simulated_confirmed'
            saved=s.get(Meta,'demo_overrides')
            if saved:saved.value=json.dumps(overrides)
            else:s.add(Meta(key='demo_overrides',value=json.dumps(overrides)))
            db.audit(s,u['username'],'demo_command_confirm',command_id,{'asset_id':c.asset_id,'semantic':c.semantic,'before':c.before,'after':c.requested,'simulated':True})
        with runtime.lock:runtime.overrides=overrides
        runtime.demo_tick()
        return {'ok':True,'simulated':True,'state':'simulated_confirmed'}

    @app.get('/api/shift')
    def shift(u=Depends(auth)):
        now=time.time()
        with db.session() as s:
            return {'since':now-12*3600,
                'alarms':[asdict(x) for x in s.scalars(select(Alarm).where(Alarm.active==True).order_by(Alarm.first_seen))],
                'tickets':[asdict(x) for x in s.scalars(select(Ticket).where(Ticket.state!='resolved').order_by(Ticket.id.desc()))],
                'changes':[asdict(x) for x in s.scalars(select(Audit).where(Audit.ts>=now-12*3600,Audit.action.in_(['asset_update','tag_mapping','import_activate','controller_update','demo_command_confirm'])).order_by(Audit.id.desc()).limit(100))]}

    @app.get('/health/live')
    def liveness():return {'alive':True}
    @app.get('/health/ready')
    def readiness():
        now=time.time()
        ok=runtime.last_persist is not None and now-runtime.last_persist<max(30,settings.history_seconds*3) and not runtime.persist_error
        if settings.mode=='live':ok=ok and bool(runtime.controller_ids) and all(runtime.controllers.get(c,{}).get('status')=='online' and now-(runtime.controllers.get(c,{}).get('last_ok') or 0)<=settings.stale_seconds for c in runtime.controller_ids)
        return JSONResponse({'ready':bool(ok)},status_code=200 if ok else 503)
    @app.get('/api/health')
    def health(u=Depends(auth)):
        storage=settings.storage_mount if settings.storage_mount and Path(settings.storage_mount).exists() else str(settings.data_dir)
        disk=shutil.disk_usage(storage)
        temperature=None
        try:temperature=float(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000
        except (OSError,ValueError):pass
        memory={}
        try:
            mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if len(line.split())>=2 and line.split()[1].isdigit()}
            memory={'total':mem.get('MemTotal'),'available':mem.get('MemAvailable')}
        except OSError:pass
        with db.session() as s:
            samples=s.scalar(select(func.count(Sample.id)))
            lastbackup=s.get(Meta,'last_backup')
        return {'version':__version__,'mode':settings.mode,'uptime':time.time()-runtime.started,
            'memory':memory,'cpu_temperature':temperature,'load_average':list(os.getloadavg()) if hasattr(os,'getloadavg') else None,
            'storage':{'path':storage,'total':disk.total,'used':disk.used,'free':disk.free,'label':'Sistema de arquivos local; PostgreSQL remoto pode usar outro disco'},
            'database':{'engine':db.engine.dialect.name,'samples':samples,'last_persist':runtime.last_persist,'error':runtime.persist_error},
            'acquisition':runtime.last_acquisition,'analysis_error':runtime.analysis_error,'retention_last_run':runtime.last_retention,
            'last_backup':json.loads(lastbackup.value) if lastbackup else None,'controllers':runtime.snapshot()['controllers'],
            'llm':{'enabled':settings.ollama_enabled,'model':settings.ollama_model,'busy':runtime.llm_lock.locked(),'last_response':runtime.last_ai},
            'live_writes_enabled':False,'commissioned':False}

    @app.get('/api/openapi.json')
    def openapi(u=Depends(admin)):return app.openapi()

    app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
    @app.get('/')
    def index():return FileResponse(ROOT/'static'/'index.html')
    return app

app=create_app()
