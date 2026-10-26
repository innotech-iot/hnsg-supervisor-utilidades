"""Opt-in: only inside the disposable PostgreSQL harness, never DATABASE_URL."""
import hmac
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

import pytest
from sqlalchemy import Column, ForeignKey, Integer, JSON, MetaData, String, Table, event, inspect, select
from sqlalchemy.engine import URL

from app.config import Settings
from app.database import Database
from app.models import Base, Meta, Controller, Asset, Sample, User, Audit, Alarm, Tag, Session
from app.security import hash_password,token_hash

ENABLED=os.getenv('HNSG_PGTEST_ENABLED')=='1' and Path('/opt/hnsg-postgres-fixture').is_file()
pytestmark=pytest.mark.skipif(not ENABLED,reason='Ensaio PostgreSQL opt-in: scripts/verify_postgres.py')
FIXTURE_PASSWORD='Fixture-Segura-2026!'


@pytest.fixture(scope='module')
def cluster():
    import psycopg
    from psycopg import sql
    import importlib.metadata
    token=os.environ['HNSG_PGTEST_TOKEN']
    # Fixed internal Compose hostname. No operational URL is consumed.
    with psycopg.connect(host='postgres',dbname='hnsg_pgtest_control',user='postgres',
            password=os.environ['HNSG_PGTEST_ADMIN_PASSWORD'],autocommit=True,connect_timeout=10) as admin:
        actual=admin.execute('SELECT token FROM hnsg_test_isolation').fetchone()[0]
        if not hmac.compare_digest(actual,token):raise RuntimeError('Cluster não pertence ao ensaio isolado')
        names=[]
        def allocate():
            name='hnsg_pgtest_'+uuid.uuid4().hex
            admin.execute(sql.SQL('CREATE DATABASE {} OWNER hnsg_fixture TEMPLATE template0').format(sql.Identifier(name)))
            names.append(name)
            return URL.create('postgresql+psycopg',username='hnsg_fixture',password=os.environ['HNSG_PGTEST_PASSWORD'],
                host='postgres',port=5432,database=name)
        info={'postgresql':admin.execute('SHOW server_version').fetchone()[0],
            'python':sys.version.split()[0],'architecture':platform.machine(),
            'sqlalchemy':importlib.metadata.version('SQLAlchemy'),'psycopg':importlib.metadata.version('psycopg'),
            'pg_dump':subprocess.run(['pg_dump','--version'],capture_output=True,text=True,check=True).stdout.strip(),
            'application_role_superuser':False,'operational_database_used':False,'plcs_connected':False}
        Path('/artifacts/postgres-environment.json').write_text(json.dumps(info,indent=2))
        try:yield allocate
        finally:
            for name in names:
                admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


@pytest.fixture
def pg_database(cluster,tmp_path):
    opened=[]
    def create(mode='demo',initialize=True,legacy=False):
        url=cluster()
        settings=Settings(mode=mode,data_dir=tmp_path/uuid.uuid4().hex,
            database_url=url.render_as_string(hide_password=False),run_collector=False,seed_hours=0,
            bootstrap_password=FIXTURE_PASSWORD)
        db=Database(settings);opened.append(db)
        if legacy:seed_legacy(db)
        elif initialize:db.initialize()
        with db.engine.connect() as conn:
            assert conn.exec_driver_sql("SELECT rolsuper FROM pg_roles WHERE rolname=current_user").scalar() is False
        return db
    try:yield create
    finally:
        for db in opened:db.close()


def seed_legacy(db):
    metadata=MetaData()
    for name,table in Base.metadata.tables.items():
        if name!='assets':table.to_metadata(metadata)
    # Frozen v1 schema: kind does not exist.
    assets=Table('assets',metadata,Column('id',Integer,primary_key=True),
        Column('controller_id',Integer,ForeignKey('controllers.id'),nullable=False),
        Column('name',String(100),nullable=False),Column('sector',String(200),nullable=False),
        Column('criticality',String(20),nullable=False),Column('profile',JSON,nullable=False),
        Column('revision',Integer,nullable=False))
    metadata.create_all(db.engine)
    with db.session() as session:
        session.add_all([Meta(key='mode',value=db.settings.mode),Meta(key='schema_version',value='1'),
            Controller(id=1,name='CLP preservado',host='127.0.0.1',enabled=False),
            Controller(id=2,name='CLP 2',assignment_confirmed=False)])
        session.flush()
        session.execute(assets.insert(),[{'id':i,'controller_id':1 if i in {1,2,3,9,10,12} else 2,
            'name':f'UTA {i:02}','sector':'Fixture preservada','criticality':'high','revision':7,
            'profile':{'validated':False}} for i in range(1,15)])
        session.add(User(username='fixture',name='Usuário fictício',role='admin',password_hash=hash_password(FIXTURE_PASSWORD)))
        session.add(Sample(asset_id=1,ts=time.time(),data={'temperature':22.7},quality='good',source=db.settings.mode,versions={'1':4}))
        session.add(Audit(username='fixture',action='fixture_preserved',target='1',data={'marker':'original'}))


def test_postgres_api_auth_mapping_and_unknown_live(pg_database):
    from fastapi.testclient import TestClient
    from app.main import create_app
    db=pg_database(mode='live')
    app=create_app(db.settings)
    with TestClient(app) as client:
        assert client.get('/api/state').status_code==401
        response=client.post('/api/auth/login',json={'username':'admin','password':FIXTURE_PASSWORD})
        assert response.status_code==200
        headers={'X-CSRF-Token':response.json()['csrf']}
        state=client.get('/api/state').json()
        assert len(state['assets'])==16 and len(state['controllers'])==3
        assert all(a['status']=='unknown' and all(v is None for v in a['data'].values()) for a in state['assets'])
        assert client.get('/health/ready').status_code==503
        assert client.post('/api/tickets',json={'title':'Fixture sem CSRF'}).status_code==403
        assert client.post('/api/commands/prepare',headers=headers,json={'asset_id':1,'semantic':'temp_sp',
            'value':23,'expected':22,'reason':'Fixture somente leitura'}).status_code==403
        protocol='symbol;description;area;address;type;scale;offset;unit;access;word_order;byte_order\n'
        protocol+='EX_TEMP;Fixture água;holding;100;int16;0.1;0;°C;RO;big;big\n'
        preview=client.post('/api/imports/preview',headers=headers,json={'controller_id':3,'filename':'fixture.txt','text':protocol,'address_base':0})
        assert preview.status_code==200
        assert client.post('/api/imports/'+preview.json()['id']+'/activate',headers=headers,
            json={'confirmation':'CONFIRMO MAPA DE LEITURA'}).status_code==200
        tag=client.get('/api/tags?controller_id=3').json()['tags'][0]
        assert client.put(f"/api/tags/{tag['id']}",headers=headers,json={'asset_id':16,'semantic':'supply_temperature',
            'validated':True,'expected_revision':1,'reason':'Fixture de vínculo explícito'}).status_code==200
        assert client.get('/api/controllers').json()[2]['enabled'] is False
        assert client.get('/api/assets/16/history').json()['rows']==[]
        assert client.post('/api/users',headers=headers,json={'username':'fixture_viewer','name':'Fixture viewer',
            'role':'viewer','password':FIXTURE_PASSWORD}).status_code==200
        client.post('/api/auth/logout',headers=headers)
        login=client.post('/api/auth/login',json={'username':'fixture_viewer','password':FIXTURE_PASSWORD}).json()
        assert client.post('/api/tickets',headers={'X-CSRF-Token':login['csrf']},json={'title':'Fixture bloqueada'}).status_code==403


def test_postgres_legacy_migration_preserves_data_and_mode_guard(pg_database):
    from app.migrations import migrate_database
    db=pg_database(legacy=True)
    assert migrate_database(db)['changed'] is True
    assert migrate_database(db)['changed'] is False
    db.initialize()
    with db.session() as session:
        assert session.get(Asset,1).revision==7
        assert session.get(Asset,1).profile=={'validated':False}
        assert session.get(Asset,15).kind=='cag' and session.get(Asset,16).controller_id==3
        assert session.get(Controller,1).host=='127.0.0.1'
        assert session.get(Controller,3).enabled is False
        assert session.scalar(select(Sample)).data=={'temperature':22.7}
        assert session.scalar(select(User)).username=='fixture'
        assert session.scalar(select(Audit).where(Audit.action=='fixture_preserved')).data=={'marker':'original'}
    wrong=Database(Settings(mode='live',database_url=db.settings.database_url,data_dir=db.settings.data_dir))
    try:
        with pytest.raises(RuntimeError,match='outro modo'):wrong.initialize()
    finally:wrong.close()


def test_postgres_migration_ddl_and_data_roll_back(pg_database):
    from app.migrations import migrate_database
    db=pg_database(legacy=True)
    def fail(conn,cursor,statement,parameters,context,executemany):
        if statement.lstrip().upper().startswith('INSERT INTO ASSETS'):raise RuntimeError('Falha de fixture após DDL')
    event.listen(db.engine,'before_cursor_execute',fail)
    try:
        with pytest.raises(RuntimeError,match='fixture'):migrate_database(db)
    finally:event.remove(db.engine,'before_cursor_execute',fail)
    assert 'kind' not in {c['name'] for c in inspect(db.engine).get_columns('assets')}
    with db.session() as session:
        assert session.get(Meta,'schema_version').value=='1'
        assert session.get(Controller,3) is None


def test_postgres_backup_restore_to_new_database_and_api(pg_database,tmp_path):
    from app.backups import perform_backup,verify_backup
    from app.migrations import migrate_database
    from app.postgres import client_connection
    from fastapi.testclient import TestClient
    from app.main import create_app
    source=pg_database(legacy=True)
    session_id=token_hash('fixture-session-cookie')
    with source.session() as session:
        user=session.scalar(select(User))
        session.add(Session(id=session_id,user_id=user.id,csrf='fixture-csrf',expires=time.time()+3600))
        session.add(Tag(controller_id=2,asset_id=4,symbol='EX_PRESERVED',area='holding',address=100,
            data_type='int16',scale=.1,unit='°C',semantic='temperature',validated=True,
            instrument={'location':'Fixture de instrumento','model':'Modelo fictício'}))
        session.add(Alarm(key='fixture:preserved',asset_id=4,controller_id=2,code='controller_alarm',
            title='Alarme fictício preservado',priority='warning',source='controller',active=True,
            evidence={'marker':'original-alarm'}))
    destination=tmp_path/'backup';destination.mkdir()
    report=perform_backup(source,destination,allow_same_device=True)
    assert verify_backup(report['manifest'])['integrity']=='archive_listed_only'
    target=pg_database(initialize=False)
    assert target.engine.url.database!=source.engine.url.database
    assert inspect(target.engine).get_table_names()==[]
    connection,env=client_connection(target.engine.url)
    subprocess.run(['pg_restore','--exit-on-error','--single-transaction','--no-owner','--no-acl','--no-password',
        '--dbname',connection,report['file']],env=env,capture_output=True,check=True,timeout=60)
    migrate_database(target)
    app=create_app(target.settings)
    with TestClient(app) as client:
        assert client.post('/api/auth/login',json={'username':'fixture','password':FIXTURE_PASSWORD}).status_code==200
        state=client.get('/api/state').json()
        assert len(state['assets'])==16 and state['assets'][0]['revision']==7
        rows=client.get('/api/assets/1/history').json()['rows']
        assert rows[-1]['data']['temperature']==22.7
        assert '22.7' in client.get('/api/assets/1/export.csv').text
    with source.session() as session:assert session.get(Meta,'schema_version').value=='1'
    assert 'kind' not in {c['name'] for c in inspect(source.engine).get_columns('assets')}
    with target.session() as session:
        tag=session.scalar(select(Tag).where(Tag.symbol=='EX_PRESERVED'))
        assert tag.validated is True and tag.asset_id==4 and tag.instrument['model']=='Modelo fictício'
        alarm=session.scalar(select(Alarm).where(Alarm.key=='fixture:preserved'))
        assert alarm.active is True and alarm.evidence=={'marker':'original-alarm'}
        assert session.get(Session,session_id).csrf=='fixture-csrf'
        assert session.scalar(select(Audit).where(Audit.action=='fixture_preserved')).data=={'marker':'original'}
        session.add(Audit(username='fixture',action='restored_sequence',target='1',data={}))
    assert verify_backup(report['manifest'])['restored_to_separate_database'] is False


def test_postgres_central_history_json_aggregation_and_stale(pg_database):
    from app.runtime import Runtime
    from app.history import history
    from app.models import Aggregate
    db=pg_database(mode='live')
    runtime=Runtime(db,db.settings);runtime.initialize()
    now=time.time()
    stamp=(int(now//3600)-1)*3600+10
    with db.session() as session:
        session.add(Sample(asset_id=16,ts=stamp,data={'supply_temperature':48.3,'pump_feedback':1},quality='good',source='live'))
    runtime.rollup()
    with db.session() as session:
        aggregate=session.scalar(select(Aggregate).where(Aggregate.asset_id==16))
        assert aggregate.data['supply_temperature']=={'mean':48.3,'min':48.3,'max':48.3,'count':1}
    assert history(db,16,stamp-1,now)['rows'][0]['data']['pump_feedback']==1
    runtime.latest[16]={'ts':now-60,'data':{'supply_temperature':48.3},'quality':'partial','source':'live','versions':{}}
    runtime.persist()
    rows=history(db,16,now-1,time.time()+1)['rows']
    assert rows[-1]['quality']=='stale' and rows[-1]['data']=={}


def test_postgres_incident_retention_and_evidence(pg_database):
    from app.runtime import Runtime
    from app.evidence import incident_evidence
    from app.models import PointSnapshot, Aggregate
    db=pg_database(mode='live');runtime=Runtime(db,db.settings);runtime.initialize()
    ts=int((time.time()-12*86400)//3600)*3600+1800
    with db.session() as s:
        alarm=Alarm(key='pg-fixture',asset_id=None,controller_id=3,code='communication',
            title='Fixture',priority='warning',source='system',evidence={},active=False,
            first_seen=ts,last_seen=ts+60,closed_at=ts+60)
        s.add(alarm);s.flush();alarm_id=alarm.id
        for delta in (-601,-600,0,660,661):
            s.add(Sample(asset_id=16,ts=ts+delta,data={'supply_temperature':None},
                quality='stale',source='live',versions={'map':7}))
            s.add(PointSnapshot(controller_id=3,ts=ts+delta,data={'1':{'value':None,'quality':'stale'}}))
        s.add(Sample(asset_id=15,ts=ts,data={},quality='unknown',source='live'))
    runtime.rollup();runtime.rollup()
    with db.session() as s:
        assert {r.ts-ts for r in s.scalars(select(Sample))}=={-600,0,660}
        assert len(s.scalars(select(PointSnapshot)).all())==3
        result=incident_evidence(s,s.get(Alarm,alarm_id),'samples',0,2)
        assert len(result['rows'])==2 and result['next_after']
        assert result['rows'][0]['versions']=={'map':7}
        assert result['rows'][0]['data']['supply_temperature'] is None
        assert s.scalar(select(Aggregate).where(Aggregate.asset_id==16)).valid_count==0


def test_postgres_typed_ai_history_summary(pg_database):
    from app.ai_history import summarize
    from app.schemas import AIHistory
    db=pg_database(mode='live');now=time.time()
    with db.session() as s:
        for value,quality in [(40,'good'),(44,'partial'),(999,'stale')]:
            s.add(Sample(asset_id=16,ts=now-30,data={'supply_temperature':value},quality=quality,source='live'))
    result=summarize(db,16,'caq',AIHistory(hours=1,metrics=['supply_temperature']))
    metric=result['metrics']['supply_temperature']
    assert metric['mean']==42 and metric['count']==2 and metric['min']==40 and metric['max']==44
    assert result['source']=='live' and result['coverage']=='not_verified'


def test_postgres_mixed_history_boundary_and_weighting(pg_database):
    from app.ai_history import summarize
    from app.schemas import AIHistory
    from app.history import history
    from app.models import Aggregate
    db=pg_database(mode='live');db.settings.history_days=1
    boundary=int((time.time()-86400)//3600)*3600
    with db.session() as s:
        for hour,value in [(boundary-3600,20),(boundary,999)]:
            s.add(Aggregate(asset_id=16,hour=hour,count=2,valid_count=2,
                data={'supply_temperature':{'mean':value,'min':value-1,'max':value+1,'count':2}}))
        s.add(Sample(asset_id=16,ts=boundary,data={'supply_temperature':26},quality='good',source='live'))
    result=history(db,16,boundary-3600,time.time())
    assert result['aggregation']=='mixed'
    assert [r['data']['supply_temperature'] for r in result['rows']]==[20,26]
    metric=summarize(db,16,'caq',AIHistory(hours=48,metrics=['supply_temperature']))['metrics']['supply_temperature']
    assert metric['count']==3 and metric['mean']==22


def test_postgres_fan_mismatch_and_valid_recovery(pg_database,monkeypatch):
    from app.runtime import Runtime
    db=pg_database(mode='live');runtime=Runtime(db,db.settings);runtime.initialize()
    profile={'validated':True,'fan_confirmation_validated':True,'settling_seconds':20,
        'persistence_seconds':30,'max_gap_seconds':15}
    with db.session() as s:s.get(Asset,1).profile=profile
    tags=[{'id':n,'asset_id':1,'semantic':key,'poll_seconds':2,'map_revision':1,'revision':1}
        for n,key in enumerate(('mode','fan_command','fan_feedback'),1)]
    base=time.time()-200
    for n in range(11):
        stamp=base+n*10;monkeypatch.setattr('app.runtime.time.time',lambda stamp=stamp:stamp)
        runtime.points[1]={str(t['id']):{'ts':stamp,'value':v,'quality':'good'} for t,v in zip(tags,(1,1,0))}
        runtime.update_live_assets(1,tags);runtime.detect()
    with db.session() as s:
        alarm=s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch'))
        assert alarm.active and alarm.evidence['versions']['asset_revision']==1
        initial=alarm.evidence['initial']
    for n in range(11,17):
        stamp=base+n*10;monkeypatch.setattr('app.runtime.time.time',lambda stamp=stamp:stamp)
        runtime.points[1]={str(t['id']):{'ts':stamp,'value':v,'quality':'good'} for t,v in zip(tags,(1,1,1))}
        runtime.update_live_assets(1,tags);runtime.detect()
    with db.session() as s:
        alarm=s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch'))
        assert not alarm.active and alarm.closed_at is not None
        assert alarm.evidence['initial']==initial
        assert alarm.evidence['recovery']['feedback']==1
