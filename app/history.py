from __future__ import annotations
import math
import time
from collections import defaultdict
from sqlalchemy import select
from .models import Sample, Aggregate
from .equipment import ALL_CATALOG as CATALOG


def history(db,asset_id,start,end,limit=1200):
    if not all(math.isfinite(v) for v in (start,end)) or end<=start or end-start>366*86400:
        raise ValueError('Intervalo inválido ou maior que 366 dias')
    if not isinstance(limit,int) or limit<1:raise ValueError('Limite de pontos inválido')
    boundary=math.floor((time.time()-db.settings.history_days*86400)/3600)*3600
    raw_start=max(start,boundary);hourly=[]
    with db.session() as s:
        if start<boundary:
            aggregates=s.scalars(select(Aggregate).where(Aggregate.asset_id==asset_id,
                Aggregate.hour>=start-3600,Aggregate.hour+3600>start,
                Aggregate.hour<min(end,boundary)).order_by(Aggregate.hour)).all()
            hourly=[{'ts':a.hour,'data':{k:v['mean'] for k,v in a.data.items()},'extrema':a.data,
                'quality':'good' if a.valid_count==a.count else 'partial',
                'has_gap':a.valid_count<a.count,'sample_count':a.count,'valid_count':a.valid_count,
                'aggregation':'hourly','resolution_seconds':3600,'interval_end':a.hour+3600} for a in aggregates]
        samples=s.scalars(select(Sample).where(Sample.asset_id==asset_id,Sample.ts>=raw_start,
            Sample.ts<=end).order_by(Sample.ts,Sample.id).limit(100_001)).all() if end>=raw_start else []
        if len(samples)>100_000:raise ValueError('Consulta excede 100 mil snapshots brutos; reduza o intervalo ou use agregados')
        rows=[{'ts':r.ts,'data':r.data,'quality':r.quality,'versions':r.versions,'source':r.source,
            'aggregation':'raw','resolution_seconds':db.settings.history_seconds} for r in samples]
    aggregation='raw'
    if len(rows)>limit:
        # Time buckets preserve extrema, number of valid samples and any missing-data flags.
        width=max(1,(end-raw_start)/limit); buckets=defaultdict(list)
        for row in rows: buckets[int((row['ts']-raw_start)/width)].append(row)
        compact=[]
        for key,group in sorted(buckets.items()):
            means={}; extrema={}
            for metric in CATALOG:
                vals=[r['data'][metric] for r in group if r['data'].get(metric) is not None and r['quality'] in {'good','partial'}]
                if vals:
                    means[metric]=sum(vals)/len(vals)
                    extrema[metric]={'min':min(vals),'max':max(vals),'count':len(vals)}
            allgood=all(r['quality']=='good' for r in group)
            compact.append({'ts':raw_start+key*width,'data':means,'extrema':extrema,'quality':'good' if allgood else 'partial',
                            'has_gap':any(r['quality'] not in {'good','partial'} for r in group),
                            'sample_count':len(group),'valid_count':sum(r['quality']=='good' for r in group),
                            'aggregation':'bucketed','resolution_seconds':width,
                            'interval_end':min(end,raw_start+(key+1)*width)})
        rows=compact; aggregation='bucketed'
    aggregation='mixed' if hourly and rows else 'hourly' if hourly else aggregation
    return {'rows':hourly+rows,'aggregation':aggregation,'source':db.settings.mode,'start':start,'end':end,
            'raw_boundary':boundary,
            'notice':'Agregados horários anteriores à fronteira; snapshots/buckets recentes a partir dela, sem sobreposição. Extremos preservados; horas e intervalos ausentes não são interpolados. Ausência de dados não é normalidade.'}
