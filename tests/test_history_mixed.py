import time

import pytest
from sqlalchemy import select

from app.config import Settings
from app.database import Database
from app.models import Sample, Aggregate
from app.history import history


@pytest.fixture
def db(tmp_path):
    database=Database(Settings(data_dir=tmp_path,run_collector=False,seed_hours=0,
        bootstrap_password='Teste-Seguro-2026!',history_days=1))
    database.initialize()
    yield database
    database.close()


def agg(s,ts,value,count=2):
    s.add(Aggregate(asset_id=1,hour=ts,data={'temperature':{'mean':value,'min':value-1,'max':value+1,'count':count}},count=count,valid_count=count))


def raw(s,ts,value,quality='good'):
    s.add(Sample(asset_id=1,ts=ts,data={'temperature':value},quality=quality,source='demo',versions={'map':4}))


def test_mixed_keeps_recent_raw_and_no_overlap(db):
    boundary=int((time.time()-86400)//3600)*3600
    with db.session() as s:
        agg(s,boundary-3600,20);agg(s,boundary,100)
        raw(s,boundary-1,999);raw(s,boundary,24);raw(s,time.time()-10,None,'stale')
    result=history(db,1,boundary-3600,time.time())
    assert result['aggregation']=='mixed'
    assert [r['data']['temperature'] for r in result['rows']]==[20,24,None]
    assert [r['aggregation'] for r in result['rows']]==['hourly','raw','raw']
    assert result['rows'][0]['resolution_seconds']==3600
    assert result['rows'][1]['versions']=={'map':4}
    assert result['rows'][-1]['quality']=='stale'


def test_mixed_summary_uses_hourly_and_raw_counts(db):
    from app.ai_history import summarize
    from app.schemas import AIHistory
    boundary=int((time.time()-86400)//3600)*3600
    with db.session() as s:
        agg(s,boundary-3600,20,2);raw(s,time.time()-30,26)
    result=summarize(db,1,'uta',AIHistory(hours=48,metrics=['temperature']))
    m=result['metrics']['temperature']
    assert result['aggregation']=='mixed' and m['count']==3 and m['mean']==22
    assert m['min']==19 and m['max']==26


def test_mixed_recent_buckets_preserve_extrema_and_missing(db):
    boundary=int((time.time()-86400)//3600)*3600
    with db.session() as s:
        agg(s,boundary-3600,20)
        for n in range(20):raw(s,boundary+100+n,24 if n else 30,'good' if n else 'stale')
    result=history(db,1,boundary-3600,time.time(),limit=2)
    assert result['aggregation']=='mixed'
    recent=[r for r in result['rows'] if r['aggregation']=='bucketed']
    assert len(recent)==1 and recent[0]['has_gap']
    assert recent[0]['extrema']['temperature']['max']==24
    assert recent[0]['sample_count']==20


def test_hour_ending_at_requested_start_is_not_returned(db):
    boundary=int((time.time()-86400)//3600)*3600
    start=boundary-7200
    with db.session() as s:
        agg(s,start-3600,999);agg(s,start,20)
    result=history(db,1,start,boundary)
    assert [r['data']['temperature'] for r in result['rows']]==[20]
