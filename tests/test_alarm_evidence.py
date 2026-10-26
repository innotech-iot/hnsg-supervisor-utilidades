import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.main import create_app
from app.models import Alarm, Sample, PointSnapshot, Aggregate


@pytest.fixture
def setup(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,run_collector=False,seed_hours=0,
        bootstrap_password='Teste-Seguro-2026!'))
    with TestClient(app) as client:
        yield app,client


def occurrence(s,ts,asset_id=1,controller_id=1,active=False):
    a=Alarm(key='fixture',asset_id=asset_id,controller_id=controller_id,
        code='fixture',title='Fixture',priority='warning',source='detector',
        evidence={'fixture':True},first_seen=ts,last_seen=ts+60,
        active=active,closed_at=None if active else ts+60)
    s.add(a);s.flush()
    return a.id


def sample(s,aid,ts,quality='good'):
    s.add(Sample(asset_id=aid,ts=ts,data={'temperature':None if quality=='stale' else 22.7},
        quality=quality,source='demo',versions={'profile':3}))


@pytest.mark.parametrize('asset_id,kept',[(1,{1}),(None,{1,2})])
def test_retention_preserves_only_incident_scope_and_window(setup,asset_id,kept):
    app,_=setup;ts=int((time.time()-12*86400)//3600)*3600+1800
    with app.state.db.session() as s:
        occurrence(s,ts,asset_id=asset_id)
        for aid in (1,2,4):
            for delta in (-601,-600,0,660,661):sample(s,aid,ts+delta,'stale' if delta==0 else 'good')
        for cid in (1,2):
            for delta in (-601,-600,0,660,661):s.add(PointSnapshot(controller_id=cid,ts=ts+delta,data={'1':{'value':None,'quality':'stale'}}))
    app.state.runtime.rollup();app.state.runtime.rollup()
    with app.state.db.session() as s:
        rows=s.scalars(select(Sample)).all()
        assert {(r.asset_id,r.ts-ts) for r in rows}=={(aid,d) for aid in kept for d in (-600,0,660)}
        assert {(r.controller_id,r.ts-ts) for r in s.scalars(select(PointSnapshot))}=={(1,d) for d in (-600,0,660)}
        assert all(r.data['temperature'] is None for r in rows if r.quality=='stale')


def test_active_alarm_preserves_unknown_and_rollup_advances_across_gap(setup):
    app,_=setup;ts=time.time()-20*86400;recent=int((time.time()-7200)//3600)*3600+15
    with app.state.db.session() as s:
        occurrence(s,ts,active=True)
        sample(s,1,ts,'stale');sample(s,1,recent,'stale');sample(s,2,recent)
    app.state.runtime.rollup();app.state.runtime.rollup()
    with app.state.db.session() as s:
        assert s.scalar(select(Aggregate).where(Aggregate.asset_id==2,Aggregate.hour==int(recent//3600)*3600)) is not None
        assert s.scalar(select(Sample).where(Sample.asset_id==1,Sample.ts==ts)) is not None
        assert s.scalar(select(Alarm)).active is True


def test_evidence_api_auth_pagination_quality_and_scope(setup):
    app,c=setup;ts=time.time()-12*86400
    with app.state.db.session() as s:
        aid=occurrence(s,ts)
        for d in (-600,0,660):sample(s,1,ts+d,'stale')
        sample(s,2,ts)
        s.add(PointSnapshot(controller_id=1,ts=ts,data={'7':{'value':None,'quality':'stale','map_revision':4}}))
    url=f'/api/alarms/{aid}/evidence'
    assert c.get(url).status_code==401
    assert c.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'}).status_code==200
    r=c.get(url+'?limit=2');assert r.status_code==200,r.text
    body=r.json();assert len(body['rows'])==2 and body['next_after']
    assert all(row['quality']=='stale' and row['data']['temperature'] is None and row['versions']=={'profile':3} for row in body['rows'])
    assert c.get(url+f"?after={body['next_after']}").json()['rows'][0]['ts']==ts+660
    points=c.get(url+'?kind=points').json()['rows']
    assert points[0]['data']['7']['map_revision']==4
    assert c.get(url+'?limit=1001').status_code==422
    assert c.get('/api/alarms/999999/evidence').status_code==404


def test_point_only_retention_and_unclosed_alarm_fail_safe(setup):
    app,c=setup;ts=time.time()-12*86400
    with app.state.db.session() as s:
        aid=occurrence(s,ts,asset_id=None,active=True)
        s.add(PointSnapshot(controller_id=1,ts=ts+86400,data={'1':{'quality':'unknown','value':None}}))
        s.add(PointSnapshot(controller_id=2,ts=ts,data={}))
    app.state.runtime.rollup()
    with app.state.db.session() as s:
        assert [p.controller_id for p in s.scalars(select(PointSnapshot))]==[1]
        alarm=s.get(Alarm,aid);alarm.active=False  # Legacy incomplete closure: preserve fail-safe.
    app.state.runtime.rollup()
    c.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
    result=c.get(f'/api/alarms/{aid}/evidence?kind=points').json()
    assert len(result['rows'])==1 and result['end'] is None
    assert c.get(f'/api/alarms/{aid}/evidence?kind=bad').status_code==422


def test_protected_old_hour_does_not_stall_recent_aggregation(setup):
    app,_=setup;ts=time.time()-20*86400;recent=int((time.time()-7200)//3600)*3600+15
    with app.state.db.session() as s:
        occurrence(s,ts,active=True);sample(s,1,ts)
    app.state.runtime.rollup()
    with app.state.db.session() as s:sample(s,1,recent)
    app.state.runtime.rollup()
    with app.state.db.session() as s:
        assert s.scalar(select(Aggregate).where(Aggregate.asset_id==1,Aggregate.hour==int(recent//3600)*3600)) is not None


def test_expired_protected_hours_do_not_starve_recent_rollup(setup):
    app,_=setup;old=int((time.time()-400*86400)//3600)*3600+15
    recent=int((time.time()-7200)//3600)*3600+15
    with app.state.db.session() as s:
        occurrence(s,old,active=True)
        for n in range(49):sample(s,1,old+n*3600,'stale')
        sample(s,1,recent)
    for _ in range(3):app.state.runtime.rollup()
    with app.state.db.session() as s:
        assert s.scalar(select(Aggregate).where(Aggregate.asset_id==1,Aggregate.hour==int(recent//3600)*3600)) is not None
        assert len(s.scalars(select(Sample)).all())==50
