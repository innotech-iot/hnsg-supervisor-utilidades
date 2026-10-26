"""Advisory command/feedback comparison, never a protection or control loop."""
import math

CODE='fan_confirmation_mismatch'
SIGNALS=('mode','fan_command','fan_feedback')


def pair(row):
    data=row.get('data',{})
    command,feedback=data.get('fan_command'),data.get('fan_feedback')
    if row.get('quality')!='good' or data.get('mode')!=1 or command not in (0,1) or feedback not in (0,1):
        return None
    return command,feedback


def observed_time(row,stale_seconds):
    stamp=row.get('ts')
    if not isinstance(stamp,(int,float)) or not math.isfinite(stamp):return None
    if row.get('source')!='live':return stamp
    observed=row.get('observed_at',{})
    values=[observed.get(key) for key in SIGNALS]
    if not all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=stamp-v<=stale_seconds for v in values):return None
    return min(values)


def evaluate(rows,profile,now,stale_seconds,profile_revision=None,config_epoch=None):
    unknown={'state':'unknown','evidence':None}
    if not profile.get('validated') or profile.get('fan_confirmation_validated') is not True or not rows:
        return unknown
    last=rows[-1];current=pair(last);stamp=last.get('ts')
    if current is None or not isinstance(stamp,(int,float)) or not math.isfinite(stamp) or stamp>now or now-stamp>stale_seconds:
        return unknown
    acquired=observed_time(last,stale_seconds)
    if acquired is None or now-acquired>stale_seconds:return unknown
    settle=profile.get('settling_seconds',120);persistence=profile.get('persistence_seconds',300)
    gap=profile.get('max_gap_seconds',45)
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (settle,persistence,gap)) or settle<0 or persistence<=0 or gap<=0:
        return unknown
    versions=last.get('versions',{});run=[]
    live=last.get('source')=='live'
    if live and not versions:return unknown
    if profile_revision is not None and (live or 'asset_revision' in versions) and versions.get('asset_revision')!=profile_revision:return unknown
    if config_epoch is not None and (live or 'config_epoch' in versions) and versions.get('config_epoch')!=config_epoch:return unknown
    previous_stamp=None;oldest=None
    for row in reversed(rows):
        ts=row.get('ts')
        if pair(row)!=current or row.get('versions',{})!=versions or not isinstance(ts,(int,float)) or not math.isfinite(ts):break
        if previous_stamp is not None and not 0<previous_stamp-ts<=gap:break
        previous_stamp=ts
        observed=observed_time(row,stale_seconds)
        if observed is None:break
        if oldest is not None:
            if observed==oldest:
                run[-1]=row  # Keep earliest snapshot of this acquisition, never add a sample.
                continue
            if not 0<oldest-observed<=gap:break
        oldest=observed
        run.append(row)
    start=run[-1]['ts'] if run else acquired
    seconds=acquired-start
    if len(run)<2 or seconds<settle+persistence:return {'state':'pending','evidence':None}
    return {'state':'agreement' if current[0]==current[1] else 'mismatch',
        'evidence':{'start':start,'end':acquired,'seconds':round(seconds,3),'samples':len(run),
            'command':current[0],'feedback':current[1],'mode':1,'versions':versions,
            'observed_at':last.get('observed_at',{}),
            'settling_seconds':settle,'persistence_seconds':persistence,'max_gap_seconds':gap,
            'notice':'Divergência dos pontos associados; não confirma falha física ou causa.'}}
