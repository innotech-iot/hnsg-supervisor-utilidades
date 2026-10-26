import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.config import Settings
from app.database import Database
from app.main import create_app
from app.models import Sample, Command, Session
from app.ai import retrieve

def test_live_has_no_synthetic_values_and_cannot_write(tmp_path):
    app=create_app(Settings(mode='live',data_dir=tmp_path,run_collector=False,bootstrap_password='Teste-Seguro-2026!'))
    with TestClient(app) as c:
        r=c.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
        headers={'X-CSRF-Token':r.json()['csrf']}
        state=c.get('/api/state').json()
        assert all(a['status']=='unknown' for a in state['assets'])
        assert all(not a['data'] or all(v is None for v in a['data'].values()) for a in state['assets'])
        assert not c.get('/api/assets/1/history').json()['rows']
        assert c.post('/api/commands/prepare',headers=headers,json={'asset_id':1,'semantic':'temp_sp','value':23,'expected':22,'reason':'Não executar no CLP'}).status_code==403
        assert c.get('/health/ready').status_code==503
        assert all(not a['profile']['validated'] for a in state['assets'])

def test_database_refuses_mix_of_demo_and_live(tmp_path):
    db=Database(Settings(mode='demo',data_dir=tmp_path));db.initialize();url=str(db.engine.url);db.close()
    db=Database(Settings(mode='live',data_dir=tmp_path,database_url=url))
    with pytest.raises(RuntimeError,match='outro modo'):db.initialize()
    db.close()

def test_missing_ssd_blocks_startup(tmp_path):
    with pytest.raises(RuntimeError,match='SSD'):
        Database(Settings(data_dir=tmp_path,require_storage_mount=True,storage_mount=str(tmp_path/'not-mounted')))

def test_rag_only_approved_and_matching_equipment():
    docs=[{'id':i,'title':'Temperatura','body':'Verificação de temperatura e válvula.','revision':'1','approved':approved,'asset_id':asset} for i,asset,approved in [(1,1,True),(2,2,True),(3,None,True),(4,1,False)]]
    ids={x['id'] for x in retrieve(docs,'Temperatura',1)}
    assert ids=={1,3}

def test_sessions_store_hash_not_bearer(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,run_collector=False,seed_hours=0,bootstrap_password='Teste-Seguro-2026!'))
    with TestClient(app) as c:
        r=c.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
        raw=c.cookies.get('hnsg_session')
        with app.state.db.session() as s:
            session=s.scalar(select(Session))
            assert session.id != raw and len(session.id)==64
        assert r.cookies.get('hnsg_session')
        assert 'HttpOnly' in r.headers['set-cookie']

def test_partial_snapshot_expires_in_ui_and_persistence(tmp_path):
    from app.runtime import Runtime
    settings=Settings(data_dir=tmp_path,mode='live',run_collector=False)
    db=Database(settings);runtime=Runtime(db,settings);runtime.initialize()
    try:
        runtime.latest[1]={'ts':time.time()-60,'data':{'temperature':22.3,'fan_feedback':1},'quality':'partial','source':'live','versions':{}}
        row=runtime.snapshot()['assets'][0]
        assert row['quality']=='stale' and row['data']['temperature'] is None
        runtime.persist()
        with db.session() as s:
            sample=s.scalar(select(Sample).where(Sample.asset_id==1))
            assert sample.quality=='stale' and not sample.data
    finally:db.close()

def test_live_series_uses_acquisition_buffer(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,run_collector=False,seed_hours=.02,bootstrap_password='Teste-Seguro-2026!'))
    with TestClient(app) as c:
        c.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
        r=c.get('/api/assets/1/live?minutes=15')
        assert r.status_code==200
        data=r.json()
        assert data['aggregation']=='raw' and data['buffered'] and data['rows']

def test_readiness_rejects_old_controller_success(tmp_path):
    app=create_app(Settings(mode='live',data_dir=tmp_path,run_collector=False))
    with TestClient(app) as c:
        rt=app.state.runtime
        rt.last_persist=time.time()
        rt.controllers={i:{'status':'online','last_ok':time.time()-300} for i in [1,2]}
        assert c.get('/health/ready').status_code==503
