import time

import pytest
from sqlalchemy import select

from app.config import Settings
from app.database import Database
from app.models import Asset, Alarm
from app.runtime import Runtime


def rows(command=1,feedback=0,seconds=100,now=100):
    return [{'ts':now-seconds+n*10,'quality':'good','source':'demo',
        'data':{'mode':1,'fan_command':command,'fan_feedback':feedback},'versions':{'map':1}}
        for n in range(seconds//10+1)]


PROFILE={'validated':True,'fan_confirmation_validated':True,
    'settling_seconds':20,'persistence_seconds':30,'max_gap_seconds':15}


@pytest.fixture
def runtime(tmp_path):
    db=Database(Settings(data_dir=tmp_path,run_collector=False,seed_hours=0,
        bootstrap_password='Teste-Seguro-2026!'))
    run=Runtime(db,db.settings);run.initialize()
    with db.session() as s:
        a=s.get(Asset,1);a.profile=PROFILE.copy()
    yield run
    db.close()


@pytest.mark.parametrize('command,feedback',[(1,0),(0,1)])
def test_runtime_detects_persistent_mismatch_when_return_is_off_or_on(runtime,command,feedback):
    runtime.rings[1].extend(rows(command,feedback,now=time.time()))
    runtime.detect()
    with runtime.db.session() as s:
        alarm=s.scalar(select(Alarm).where(Alarm.asset_id==1,Alarm.code=='fan_confirmation_mismatch'))
        assert alarm and alarm.active
        assert alarm.evidence['command']==command and alarm.evidence['feedback']==feedback
        assert alarm.evidence['seconds']==100 and alarm.evidence['versions']=={'map':1}


def test_runtime_unknown_or_brief_agreement_never_normalizes(runtime):
    now=time.time();runtime.rings[1].extend(rows(now=now));runtime.detect()
    with runtime.db.session() as s:
        assert s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch')) is not None
    for samples in [rows(feedback=None,now=now),rows(feedback=1,seconds=20,now=now),
        rows(feedback=1,now=now-100),[{**r,'quality':'partial'} for r in rows(feedback=1,now=now)],
        [{**r,'data':{**r['data'],'mode':2}} for r in rows(feedback=1,now=now)]]:
        runtime.rings[1].clear();runtime.rings[1].extend(samples);runtime.detect()
        with runtime.db.session() as s:
            assert s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch')).active
    runtime.rings[1].clear();runtime.rings[1].extend(rows(feedback=1,now=time.time()));runtime.detect()
    with runtime.db.session() as s:
        alarm=s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch'))
        assert not alarm.active and alarm.closed_at is not None
        assert alarm.evidence['recovery']['command']==1 and alarm.evidence['recovery']['feedback']==1


@pytest.mark.parametrize('change',[{'fan_confirmation_validated':False},{'validated':False}])
def test_existing_profiles_do_not_enable_detector_implicitly(runtime,change):
    with runtime.db.session() as s:s.get(Asset,1).profile=PROFILE|change
    runtime.rings[1].extend(rows(now=time.time()));runtime.detect()
    with runtime.db.session() as s:
        assert s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch')) is None


@pytest.mark.parametrize('command,feedback,mode',[(None,0,1),(1,None,1),(2,0,1),(1,.5,1),(1,0,0),(1,0,2)])
def test_invalid_binary_values_and_other_modes_are_unknown(command,feedback,mode):
    from app.fan_confirmation import evaluate
    samples=rows(command,feedback)
    for r in samples:r['data']['mode']=mode
    assert evaluate(samples,PROFILE,100,15)['state']=='unknown'


@pytest.mark.parametrize('mutation',['gap','revision','transition','duplicate','partial'])
def test_discontinuous_or_changed_evidence_does_not_trigger(mutation):
    from app.fan_confirmation import evaluate
    samples=rows()
    if mutation=='gap':samples[-2]['ts']=30
    elif mutation=='revision':samples[-2]['versions']={'map':2}
    elif mutation=='transition':samples[-2]['data']['fan_feedback']=1
    elif mutation=='duplicate':samples[-2]['ts']=samples[-1]['ts']
    elif mutation=='partial':samples[-2]['quality']='partial'
    assert evaluate(samples,PROFILE,100,15)['state']=='pending'


def test_disabling_rule_preserves_existing_occurrence(runtime):
    runtime.rings[1].extend(rows(now=time.time()));runtime.detect()
    with runtime.db.session() as s:s.get(Asset,1).profile=PROFILE|{'fan_confirmation_validated':False}
    runtime.rings[1].clear();runtime.rings[1].extend(rows(feedback=1,now=time.time()));runtime.detect()
    with runtime.db.session() as s:
        assert s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch')).active


def live_tags():
    return [{'id':n,'asset_id':1,'semantic':key,'poll_seconds':3600,'map_revision':1,'revision':1}
        for n,key in enumerate(('mode','fan_command','fan_feedback'),1)]


def test_production_cached_points_cannot_trigger_or_close(runtime,monkeypatch):
    from app.fan_confirmation import evaluate
    tags=live_tags();base=time.time()-60
    runtime.points[1]={str(t['id']):{'ts':base,'quality':'good','value':value}
        for t,value in zip(tags,(1,1,0))}
    runtime.rings[1].clear()
    for n in range(7):
        monkeypatch.setattr('app.runtime.time.time',lambda n=n:base+n*10)
        runtime.update_live_assets(1,tags)
    result=evaluate(list(runtime.rings[1]),PROFILE,base+60,15)
    assert result['state']=='unknown'
    assert runtime.rings[1][-1]['versions']
    assert runtime.rings[1][-1]['observed_at']['fan_feedback']==base
    with runtime.db.session() as s:
        s.add(Alarm(key='uta:1:fan_confirmation_mismatch',asset_id=1,controller_id=1,
            code='fan_confirmation_mismatch',title='Fixture',priority='warning',source='detector',
            evidence={'initial':{'start':base-100}},active=True,first_seen=base-50,last_seen=base))
    runtime.points[1]['3']['value']=1
    runtime.update_live_assets(1,tags);runtime.detect()
    with runtime.db.session() as s:
        assert s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch')).active


def test_production_versions_break_window_and_preserve_initial_evidence(runtime,monkeypatch):
    tags=live_tags();base=time.time()-100
    runtime.rings[1].clear()
    for n in range(11):
        stamp=base+n*10;monkeypatch.setattr('app.runtime.time.time',lambda stamp=stamp:stamp)
        runtime.points[1]={str(t['id']):{'ts':stamp,'quality':'good','value':v} for t,v in zip(tags,(1,1,0))}
        runtime.update_live_assets(1,tags)
    runtime.detect()
    with runtime.db.session() as s:
        alarm=s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch'))
        assert alarm and alarm.evidence['versions']
        initial=alarm.evidence['initial']
        s.get(Asset,1).revision+=1
    stamp=base+110;monkeypatch.setattr('app.runtime.time.time',lambda:stamp)
    runtime.points[1]={str(t['id']):{'ts':stamp,'quality':'good','value':v} for t,v in zip(tags,(1,1,1))}
    runtime.update_live_assets(1,tags);runtime.detect()
    with runtime.db.session() as s:
        alarm=s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch'))
        assert alarm.active and alarm.evidence['initial']==initial


def test_bounded_window_updates_do_not_erase_original_onset(runtime,monkeypatch):
    from collections import deque
    runtime.rings[1]=deque(maxlen=6);base=time.time()-100
    for n in range(11):
        stamp=base+n*10;monkeypatch.setattr('app.runtime.time.time',lambda stamp=stamp:stamp)
        runtime.rings[1].append(rows(seconds=0,now=stamp)[0]);runtime.detect()
    with runtime.db.session() as s:
        alarm=s.scalar(select(Alarm).where(Alarm.code=='fan_confirmation_mismatch'))
        assert alarm.evidence['start']>alarm.evidence['initial']['start']
        assert alarm.evidence['initial']['start']==pytest.approx(base)


def test_demo_provenance_does_not_cross_profile_revision():
    from app.fan_confirmation import evaluate
    samples=rows()
    for row in samples:row['versions']={'demo':'1','asset_revision':1,'config_epoch':2}
    assert evaluate(samples,PROFILE,100,15,profile_revision=2,config_epoch=2)['state']=='unknown'


def test_staggered_acquisitions_do_not_backdate_full_pair_evidence():
    from app.fan_confirmation import evaluate
    samples=rows(seconds=50,now=60)
    for row in samples:
        row['source']='live'
        row['versions']={'asset_revision':1,'config_epoch':0}
        stamp=row['ts']
        row['observed_at']={'mode':stamp-10,'fan_command':stamp,'fan_feedback':stamp-5}
    assert evaluate(samples,PROFILE,60,15,1,0)['state']=='pending'


def test_profile_and_controller_updates_clear_continuity(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    app=create_app(Settings(data_dir=tmp_path,run_collector=False,seed_hours=0,
        bootstrap_password='Teste-Seguro-2026!'))
    with TestClient(app) as c:
        auth=c.post('/api/auth/login',json={'username':'admin','password':'Teste-Seguro-2026!'})
        c.headers['X-CSRF-Token']=auth.json()['csrf']
        rt=app.state.runtime;rt.rings[1].extend(rows(now=time.time()))
        a=c.get('/api/state').json()['assets'][0]
        patch={'name':a['name'],'sector':a['sector'],'criticality':a['criticality'],
            'profile':PROFILE,'expected_revision':a['revision'],'reason':'Fixture de revisão explícita'}
        result=c.put('/api/assets/1',json=patch)
        assert result.status_code==200,result.text
        assert result.json()['profile']['fan_confirmation_validated'] is True
        assert not rt.rings[1]
        patch['expected_revision']=result.json()['revision']
        patch['profile']=PROFILE|{'persistence_seconds':7200}
        assert c.put('/api/assets/1',json=patch).status_code==422
        rt.rings[1].extend(rows(now=time.time()))
        controller=c.get('/api/controllers').json()[0]
        patch={k:controller[k] for k in ('host','port','unit_id','enabled','assignment_confirmed')}
        patch|={'expected_revision':controller['revision'],'reason':'Fixture de conexão revisada'}
        assert c.put('/api/controllers/1',json=patch).status_code==200
        assert not rt.rings[1]
