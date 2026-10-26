import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import Sample


@pytest.fixture
def setup(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,run_collector=False,seed_hours=0,
        bootstrap_password='Teste-Seguro-2026!'))
    with TestClient(app) as client:
        auth=client.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
        client.headers['X-CSRF-Token']=auth.json()['csrf']
        yield app,client


def ask(c,asset_id=1,**history):
    return c.post('/api/ai/explain',json={'asset_id':asset_id,'question':'Analise o período selecionado',
        'history':{'hours':1,'metrics':['temperature'],**history}})


def test_history_summary_preserves_missing_and_excludes_bad_quality(setup):
    app,c=setup;now=time.time()
    with app.state.db.session() as s:
        for aid,delta,value,quality in [(1,90,20,'good'),(1,60,24,'partial'),(1,30,999,'stale'),(1,10,None,'unknown'),(2,20,100,'good')]:
            s.add(Sample(asset_id=aid,ts=now-delta,data={'temperature':value},quality=quality,source='demo',versions={}))
    r=ask(c);assert r.status_code==200,r.text
    h=r.json()['evidence']['history'];metric=h['metrics']['temperature']
    assert metric['mean']==22 and metric['min']==20 and metric['max']==24 and metric['count']==2
    assert h['snapshot_count']==4 and h['coverage']=='not_verified'
    assert r.json()['explanation']['summary'].startswith('Histórico')
    assert r.json()['engine']=='deterministic' and r.json()['advisory_only']


def test_empty_history_does_not_fall_back_to_current_state(setup):
    _,c=setup;r=ask(c,16,metrics=['supply_temperature'])
    assert r.status_code==200,r.text
    metric=r.json()['evidence']['history']['metrics']['supply_temperature']
    assert metric['mean'] is None and metric['min'] is None and metric['count']==0
    assert 'sem medições válidas' in r.json()['explanation']['summary']


@pytest.mark.parametrize('history',[{'hours':0},{'hours':169},{'metrics':['pump_feedback']},
    {'metrics':['supply_temperature']},{'metrics':['temperature','temperature']},
    {'metrics':['DROP TABLE samples']},{'sql':'SELECT 1'},{'metrics':[]}])
def test_history_rejects_untyped_or_incompatible_queries(setup,history):
    _,c=setup;assert ask(c,**history).status_code==422


def test_hourly_summary_weights_metric_counts_and_preserves_extrema(setup):
    from app.models import Aggregate
    app,c=setup;app.state.settings.history_days=1
    hour=int((time.time()-3*86400)//3600)*3600
    with app.state.db.session() as s:
        for offset,count,mean,lo,hi in [(0,2,20,19,21),(3600,6,24,22,26)]:
            s.add(Aggregate(asset_id=1,hour=hour+offset,count=count,valid_count=count,
                data={'temperature':{'mean':mean,'min':lo,'max':hi,'count':count}}))
    r=ask(c,hours=96);assert r.status_code==200,r.text
    h=r.json()['evidence']['history'];m=h['metrics']['temperature']
    assert h['aggregation']=='hourly' and m=={'label':'Temperatura','unit':'°C','count':8,'mean':23.0,'min':19,'max':26}


def test_hourly_summary_excludes_hour_crossing_requested_start(setup):
    from app.models import Aggregate
    app,c=setup;app.state.settings.history_days=0
    boundary=int((time.time()-3600)//3600)*3600
    with app.state.db.session() as s:
        s.add(Aggregate(asset_id=1,hour=boundary,count=10,valid_count=10,
            data={'temperature':{'mean':99,'min':99,'max':99,'count':10}}))
    r=ask(c);assert r.status_code==200,r.text
    assert r.json()['evidence']['history']['metrics']['temperature']['count']==0


def test_bucketed_history_weights_measurements_and_audits_query(setup):
    from sqlalchemy import select
    from app.models import Audit
    app,c=setup;now=time.time()
    with app.state.db.session() as s:
        for n in range(1300):
            s.add(Sample(asset_id=1,ts=now-3500+n*2,data={'temperature':20 if n<100 else 24},
                quality='good',source='demo'))
    r=ask(c);assert r.status_code==200,r.text
    h=r.json()['evidence']['history'];metric=h['metrics']['temperature']
    assert h['aggregation']=='bucketed' and metric['count']==1300
    assert metric['mean']==pytest.approx((100*20+1200*24)/1300)
    assert metric['min']==20 and metric['max']==24
    with app.state.db.session() as s:
        audit=s.scalar(select(Audit).where(Audit.action=='ai_explanation'))
        assert audit.data['evidence']['history']['hours']==1
    del c.headers['X-CSRF-Token']
    assert ask(c).status_code==403
