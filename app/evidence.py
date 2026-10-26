"""Persisted incident snapshots: no interpolation or inferred recovery."""
import time

from sqlalchemy import select, and_, or_, literal

from .models import Alarm, Asset, Sample, PointSnapshot
from .database import asdict

WINDOW_SECONDS=600  # Engineering default, not an approved hospital requirement.


def window_condition(model,alarm=Alarm):
    first,active,closed=(alarm.first_seen,alarm.active,alarm.closed_at)
    if alarm is not Alarm:first,active,closed=literal(first),literal(active),literal(closed)
    return and_(model.ts>=first-WINDOW_SECONDS,
        or_(active==True,closed.is_(None),model.ts<=closed+WINDOW_SECONDS))


def scope_condition(model,alarm=Alarm):
    if model is PointSnapshot:
        return model.controller_id==alarm.controller_id
    controller_assets=select(Asset.id).where(Asset.controller_id==alarm.controller_id).correlate(Alarm)
    return or_(model.asset_id==alarm.asset_id,
        and_(alarm.asset_id.is_(None),model.asset_id.in_(controller_assets)))


def protected(model):
    return select(Alarm.id).where(scope_condition(model),window_condition(model)).correlate(model).exists()


def incident_evidence(session,alarm,kind,after,limit):
    model=Sample if kind=='samples' else PointSnapshot
    # Instance scope uses concrete values; the retention predicate uses correlated columns.
    if model is Sample:
        scope=model.asset_id==alarm.asset_id if alarm.asset_id is not None else model.asset_id.in_(
            select(Asset.id).where(Asset.controller_id==alarm.controller_id))
    else:scope=model.controller_id==alarm.controller_id
    records=session.scalars(select(model).where(scope,window_condition(model,alarm),model.id>after)
        .order_by(model.id).limit(limit+1)).all()
    more=len(records)>limit;records=records[:limit]
    return {'alarm_id':alarm.id,'kind':kind,'rows':[asdict(row) for row in records],
        'next_after':records[-1].id if more else None,
        'start':alarm.first_seen-WINDOW_SECONDS,
        'end':None if alarm.active or alarm.closed_at is None else alarm.closed_at+WINDOW_SECONDS,
        'observed_until':time.time(),'pre_seconds':WINDOW_SECONDS,'post_seconds':WINDOW_SECONDS,
        'coverage':'not_verified',
        'notice':'Snapshots persistidos, não todas as aquisições. Dados ausentes ou já apagados não são reconstruídos; paginação por ID, não por horário.'}
