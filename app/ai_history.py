"""Typed, read-only history evidence computed before any LLM invocation."""
import math
import time

from .history import history
from .equipment import catalog_for


def validate_metrics(kind,metrics):
    catalog=catalog_for(kind)
    if len(metrics)!=len(set(metrics)) or any(m not in catalog or catalog[m]['unit'] in {'boolean','enum'} for m in metrics):
        raise ValueError('Selecione métricas numéricas únicas compatíveis com o equipamento')


def summarize(db,asset_id,kind,query):
    validate_metrics(kind,query.metrics)
    end=time.time();start=end-query.hours*3600
    result=history(db,asset_id,start,end,limit=1200)
    if any(row.get('aggregation')=='hourly' for row in result['rows']):
        result['rows']=[row for row in result['rows'] if row.get('aggregation')!='hourly' or
            (row['ts']>=start and row['interval_end']<=end)]
        result['notice']+=' Somente horas completas dentro do intervalo solicitado entram no resumo.'
    catalog=catalog_for(kind);summaries={}
    for metric in query.metrics:
        total=0;weighted=0.;minimum=None;maximum=None
        for row in result['rows']:
            value=row['data'].get(metric)
            if row['quality'] not in {'good','partial'} or not isinstance(value,(int,float)) or not math.isfinite(value):continue
            ext=row.get('extrema',{}).get(metric,{})
            count=ext.get('count',1);lo=ext.get('min',value);hi=ext.get('max',value)
            if count<=0 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (count,lo,hi)):continue
            total+=count;weighted+=value*count
            minimum=lo if minimum is None else min(minimum,lo)
            maximum=hi if maximum is None else max(maximum,hi)
        summaries[metric]={'label':catalog[metric]['label'],'unit':catalog[metric]['unit'],
            'count':total,'mean':weighted/total if total else None,'min':minimum,'max':maximum}
    return {'start':start,'end':end,'hours':query.hours,'source':result['source'],
        'aggregation':result['aggregation'],'metrics':summaries,
        'snapshot_count':sum(row.get('sample_count',1) for row in result['rows']),
        'quality_flags':sorted({row['quality'] for row in result['rows']}),
        'coverage':'not_verified','notice':result['notice'],
        'limitations':['Contagens descrevem registros disponíveis, não disponibilidade temporal nem normalidade.',
            'Qualidade inválida/nulos não entram nas estatísticas; períodos ausentes não são interpolados.',
            'Média ponderada por contagem de medições; não é média ponderada pelo tempo.']}
