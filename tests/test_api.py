import time
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(tmp_path):
    from app.config import Settings
    from app.main import create_app
    app=create_app(Settings(data_dir=tmp_path,mode='demo',bootstrap_password='Teste-Seguro-2026!',run_collector=False,seed_hours=.02))
    with TestClient(app) as c:
        yield c

def login(client):
    r=client.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
    assert r.status_code==200,r.text
    return {'X-CSRF-Token':r.json()['csrf']}

def test_private_state_requires_login(client):
    assert client.get('/api/state').status_code==401

def test_login_and_14_assets(client):
    login(client)
    r=client.get('/api/state'); assert r.status_code==200
    d=r.json(); assert d['mode']=='demo' and len(d['assets'])==16
    assert len([a for a in d['assets'] if a['kind']=='uta'])==14
    assert [a['id'] for a in d['assets'] if a['controller_id']==1]==[1,2,3,9,10,12]
    assert d['controllers'][1]['assignment_confirmed'] is False

def test_csrf_is_mandatory(client):
    login(client)
    r=client.post('/api/tickets',json={'title':'Manutenção demonstrativa','asset_id':1,'details':'Verificar dados'})
    assert r.status_code==403

def test_invalid_origin_rejected_on_login(client):
    r=client.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'},headers={'Origin':'https://attacker.invalid'})
    assert r.status_code==403

def test_no_hardcoded_credential(client):
    assert client.post('/api/auth/login',json={'username':'admin','password':'admin'}).status_code==401

def test_viewer_cannot_write(client):
    h=login(client)
    r=client.post('/api/users',headers=h,json={'username':'viewer','name':'Plantão','role':'viewer','password':'Viewer-Long-2026!'})
    assert r.status_code==200,r.text
    client.post('/api/auth/logout',headers=h)
    r=client.post('/api/auth/login',json={'username':'viewer','password':'Viewer-Long-2026!'})
    csrf={'X-CSRF-Token':r.json()['csrf']}
    assert client.get('/api/state').status_code==200
    assert client.post('/api/commands/prepare',headers=csrf,json={'asset_id':1,'semantic':'temp_sp','value':23,'expected':22,'reason':'Teste de permissão'}).status_code==403

def test_history_has_source_and_quality(client):
    login(client)
    d=client.get('/api/assets/1/history?hours=1').json()
    assert d['source']=='demo' and d['rows']
    assert 'temp_sp' in d['rows'][0]['data']
    assert d['rows'][0]['quality']=='good'

def test_import_preview_rejects_unknown(client):
    h=login(client)
    r=client.post('/api/imports/preview',headers=h,json={'controller_id':1,'filename':'teste.txt','text':'DIALETO AINDA DESCONHECIDO','address_base':0})
    assert r.status_code==200,r.text
    assert not r.json()['parsed']['activatable']
    batch=r.json()['id']
    assert client.post(f'/api/imports/{batch}/activate',headers=h,json={'confirmation':'CONFIRMO MAPA DE LEITURA'}).status_code==422

def test_import_never_enables_writes(client):
    h=login(client)
    text='symbol;area;address;type;scale;access\nT1;holding;10;int16;0.1;RW'
    p=client.post('/api/imports/preview',headers=h,json={'controller_id':1,'filename':'contrato.txt','text':text,'address_base':0}).json()
    r=client.post(f'/api/imports/{p["id"]}/activate',headers=h,json={'confirmation':'CONFIRMO MAPA DE LEITURA'})
    assert r.status_code==200,r.text
    tags=client.get('/api/tags?controller_id=1').json()['tags']
    assert len(tags)==1 and tags[0]['validated'] is False and tags[0]['write_enabled'] is False

def test_simulated_command_confirmation_and_replay(client):
    h=login(client)
    r=client.post('/api/commands/prepare',headers=h,json={'asset_id':1,'semantic':'temp_sp','value':23,'expected':22,'reason':'Teste simulado aprovado'})
    assert r.status_code==200,r.text
    cid=r.json()['id']
    r=client.post(f'/api/commands/{cid}/confirm',headers=h)
    assert r.status_code==200,r.text
    assert r.json()['simulated'] is True
    assert client.post(f'/api/commands/{cid}/confirm',headers=h).status_code==409

def test_stale_expected_value_rejected(client):
    h=login(client)
    r=client.post('/api/commands/prepare',headers=h,json={'asset_id':1,'semantic':'temp_sp','value':23,'expected':19,'reason':'Teste de conflito'})
    assert r.status_code==409

def test_ai_falls_back_without_ollama(client):
    h=login(client)
    r=client.post('/api/ai/explain',headers=h,json={'asset_id':3,'question':'Analise temperatura e resfriamento'})
    assert r.status_code==200,r.text
    assert r.json()['engine']=='deterministic' and r.json()['advisory_only']

def test_static_csp_no_external_cdn(client):
    r=client.get('/')
    assert r.status_code==200
    assert "default-src 'self'" in r.headers['content-security-policy']
