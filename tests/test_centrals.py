import asyncio
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.main import create_app
from app.models import Sample, Tag, Aggregate, Alarm


@pytest.fixture
def central_client(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,run_collector=False,seed_hours=0,
        bootstrap_password='Teste-Seguro-2026!'))
    with TestClient(app) as client:
        response=client.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
        client.headers['X-CSRF-Token']=response.json()['csrf']
        yield client,app


def test_central_cadastro_and_demo_do_not_invent_uta_values(central_client):
    client,app=central_client
    state=client.get('/api/state').json()
    assert len(state['assets'])==16
    assert [a['id'] for a in state['assets'] if a['kind']=='uta']==list(range(1,15))
    assert [c['id'] for c in state['controllers']]==[1,2,3]
    for aid,kind,cid in [(15,'cag',2),(16,'caq',3)]:
        row=next(a for a in state['assets'] if a['id']==aid)
        assert row['kind']==kind and row['controller_id']==cid
        assert row['quality']=='unknown' and row['status']=='unknown'
        assert not row['data'] or all(v is None for v in row['data'].values())
        assert row['coverage'] and not any(c['ready'] for c in row['coverage'])
        assert not client.get(f'/api/assets/{aid}/live').json()['rows']
        assert client.get(f'/api/assets/{aid}/history').status_code==200
        assert client.get(f'/api/assets/{aid}/export.csv').status_code==200
    assert client.get('/api/assets/999/history').status_code==404


def mapping(asset_id,semantic):
    return {'asset_id':asset_id,'semantic':semantic,'validated':True,'expected_revision':1,
        'reason':'Fixture de vínculo fictício'}


def test_clp3_import_mapping_and_kind_validation(central_client):
    client,app=central_client
    text='symbol;description;area;address;type;scale;offset;unit;access;word_order;byte_order\n'
    text+='EX_WATER;Temperatura fictícia;holding;100;int16;0.1;0;°C;RO;big;big\n'
    response=client.post('/api/imports/preview',json={'controller_id':3,'filename':'fixture.txt','text':text,'address_base':0})
    assert response.status_code==200,response.text
    assert client.post('/api/imports/'+response.json()['id']+'/activate',json={'confirmation':'CONFIRMO MAPA DE LEITURA'}).status_code==200
    tag=client.get('/api/tags?controller_id=3').json()['tags'][0]
    assert client.put(f"/api/tags/{tag['id']}",json=mapping(16,'supply_temperature')).status_code==200
    with app.state.db.session() as s:
        s.add(Tag(controller_id=2,symbol='EX_OTHER',area='holding',address=100,data_type='int16',scale=.1,unit='°C'))
        s.flush();tid=s.scalar(select(Tag.id).where(Tag.symbol=='EX_OTHER'))
    for aid,semantic in [(15,'fan_feedback'),(4,'pump_feedback'),(16,'supply_temperature'),(999,'temperature')]:
        assert client.put(f'/api/tags/{tid}',json=mapping(aid,semantic)).status_code==422
    assert client.put(f'/api/tags/{tid}',json=mapping(15,'return_temperature')).status_code==200


def test_live_central_persistence_history_rollup_and_no_uta_diagnosis(tmp_path):
    app=create_app(Settings(mode='live',data_dir=tmp_path,run_collector=False,bootstrap_password='Teste-Seguro-2026!'))
    with TestClient(app) as client:
        r=client.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
        client.headers['X-CSRF-Token']=r.json()['csrf']
        rt=app.state.runtime
        now=time.time()
        tags=[{'id':1,'asset_id':16,'semantic':'supply_temperature','poll_seconds':5,'map_revision':1},
              {'id':2,'asset_id':16,'semantic':'pump_feedback','poll_seconds':5,'map_revision':1}]
        rt.points[3]={'1':{'ts':now,'quality':'good','value':48.3},'2':{'ts':now,'quality':'good','value':1}}
        rt.update_live_assets(3,tags)
        row=next(a for a in client.get('/api/state').json()['assets'] if a['id']==16)
        assert row['data']['supply_temperature']==48.3 and row['data']['pump_feedback']==1
        assert row['status']=='unknown'  # Pump feedback does not prove whole-plant operation.
        rt.persist()
        rows=client.get('/api/assets/16/history').json()['rows']
        assert rows[-1]['data']['supply_temperature']==48.3
        assert '48.3' in client.get('/api/assets/16/export.csv').text
        rt.latest[16]['ts']=now-60
        rt.persist()
        rows=client.get('/api/assets/16/history').json()['rows']
        assert rows[-1]['quality']=='stale' and not rows[-1]['data']
        with app.state.db.session() as s:
            s.add(Sample(asset_id=16,ts=(int(now//3600)-1)*3600+10,data={'supply_temperature':48.3},
                quality='good',source='live'))
        rt.rollup()
        with app.state.db.session() as s:
            aggregate=s.scalar(select(Aggregate).where(Aggregate.asset_id==16))
            assert aggregate.data['supply_temperature']['mean']==48.3
        rt.rings[16].append({'ts':now,'quality':'good','data':{'mode':1,'fan_feedback':1,'temperature':100,'temp_sp':22}})
        rt.detect()
        with app.state.db.session() as s:assert not s.scalars(select(Alarm).where(Alarm.asset_id==16,Alarm.source=='detector')).all()


def test_three_independent_live_workers_and_readiness(tmp_path):
    from app.database import Database
    from app.runtime import Runtime
    settings=Settings(mode='live',data_dir=tmp_path)
    db=Database(settings);rt=Runtime(db,settings);rt.initialize()
    async def probe():
        started=[]
        async def worker(cid):
            started.append(cid)
            await asyncio.Event().wait()
        rt.live_worker=worker
        await rt.start()
        await asyncio.sleep(0)
        try:assert started==[1,2,3]
        finally:await rt.stop()
    try:asyncio.run(probe())
    finally:db.close()
    app=create_app(Settings(mode='live',data_dir=tmp_path/'ready',run_collector=False))
    with TestClient(app) as client:
        runtime=app.state.runtime
        runtime.last_persist=time.time()
        runtime.controllers={i:{'status':'online','last_ok':time.time()} for i in [1,2]}
        assert client.get('/health/ready').status_code==503
        runtime.controllers[3]={'status':'online','last_ok':time.time()}
        assert client.get('/health/ready').status_code==200


def test_centrals_cannot_use_uta_commands_or_profiles(central_client):
    client,app=central_client
    response=client.post('/api/commands/prepare',json={'asset_id':16,'semantic':'temp_sp','value':23,'expected':22,
        'reason':'Fixture somente leitura'})
    assert response.status_code==403
    response=client.put('/api/assets/16',json={'name':'CAQ','sector':'Fixture central','expected_revision':1,
        'reason':'Fixture de cadastro','profile':{'validated':True}})
    assert response.status_code==422


def test_central_temperature_mapping_requires_celsius_unit(central_client):
    client,app=central_client
    with app.state.db.session() as s:
        tag=Tag(controller_id=3,symbol='EX_FAHRENHEIT',area='holding',address=101,data_type='int16',scale=.1,unit='°F')
        s.add(tag);s.flush();tid=tag.id
    response=client.put(f'/api/tags/{tid}',json=mapping(16,'supply_temperature'))
    assert response.status_code==422
    with app.state.db.session() as s:
        assert not s.get(Tag,tid).validated
        s.get(Tag,tid).unit='°C'
    assert client.put(f'/api/tags/{tid}',json=mapping(16,'supply_temperature')).status_code==200
