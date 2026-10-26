"""Deterministic, evidence-first advisory analysis. Never a control/protection loop."""
from __future__ import annotations
import math
import statistics

CATALOG={
 'temperature':{'label':'Temperatura','unit':'°C','sp':'temp_sp','color':'cyan'},
 'humidity':{'label':'Umidade','unit':'% UR','sp':'humidity_sp','color':'blue'},
 'airflow':{'label':'Vazão de ar','unit':'m³/h','sp':'airflow_sp','color':'lime'},
 'pressure':{'label':'Pressão diferencial','unit':'Pa','color':'purple'},
 'cooling':{'label':'Comando de resfriamento','unit':'%','color':'cyan'},
 'heating':{'label':'Comando de aquecimento','unit':'%','color':'orange'},
 'fan_command':{'label':'Comando do ventilador','unit':'boolean'},
 'fan_feedback':{'label':'Retorno do ventilador','unit':'boolean'},
 'fan_speed':{'label':'Velocidade do ventilador','unit':'%','color':'blue'},
 'temp_sp':{'label':'Setpoint efetivo de temperatura','unit':'°C'},
 'humidity_sp':{'label':'Setpoint efetivo de umidade','unit':'% UR'},
 'airflow_sp':{'label':'Setpoint efetivo de vazão','unit':'m³/h'},
 'mode':{'label':'Modo: 0 desligado · 1 automático · 2 manual','unit':'enum'},
 'dehumidifying':{'label':'Desumidificação habilitada/ativa conforme vínculo','unit':'boolean'},
}

def analyze(rows,profile):
    if not profile.get('validated') or not rows: return []
    last=rows[-1]
    if last.get('quality')!='good': return []
    if last['data'].get('mode')!=1 or last['data'].get('fan_feedback')!=1: return []
    gap=float(profile.get('max_gap_seconds',45)); persistence=float(profile.get('persistence_seconds',300))
    settle=float(profile.get('settling_seconds',120))
    contiguous=[]
    for r in reversed(rows):
        if r.get('quality')!='good' or r['data'].get('mode')!=1 or r['data'].get('fan_feedback')!=1: break
        if contiguous and contiguous[-1]['ts']-r['ts']>gap: break
        contiguous.append(r)
    contiguous.reverse()
    if len(contiguous)<2 or contiguous[-1]['ts']-contiguous[0]['ts']<settle+persistence: return []
    stable_from=contiguous[0]['ts']+settle
    results=[]
    for metric,sp,tol,code in [
        ('temperature','temp_sp',profile.get('temperature_tolerance',2),'temperature_deviation'),
        ('humidity','humidity_sp',profile.get('humidity_tolerance',8),'humidity_deviation')]:
        run=[]; current_sp=last['data'].get(sp)
        if current_sp is None: continue
        for r in reversed(contiguous):
            v=r['data'].get(metric); s=r['data'].get(sp)
            if r['ts']<stable_from or v is None or s!=current_sp or abs(v-s)<=tol: break
            run.append(r)
        if len(run)<2 or run[0]['ts']-run[-1]['ts']<persistence: continue
        vals=[r['data'][metric] for r in run]
        evidence={'start':run[-1]['ts'],'end':run[0]['ts'],'seconds':round(run[0]['ts']-run[-1]['ts']),
                  'metric':metric,'setpoint':current_sp,'min':round(min(vals),3),'max':round(max(vals),3),
                  'tolerance':tol,'samples':len(run)}
        results.append({'code':code,'priority':'warning','title':f'{CATALOG[metric]["label"]}: desvio persistente',
                        'evidence':evidence,'hypotheses':['Verificar condições do processo, medição e atuação antes de atribuir causa à sintonia.']})
        if metric=='temperature' and all(r['data'].get('cooling',-1)>=95 and r['data']['temperature']>r['data'][sp] for r in run):
            results.append({'code':'cooling_saturation','priority':'warning','title':'Resfriamento saturado com erro persistente',
                            'evidence':evidence|{'command_min':min(r['data']['cooling'] for r in run)},
                            'hypotheses':['Comando alto não confirma abertura da válvula nem disponibilidade de água gelada.']})
    # No frozen-sensor flag from constant values alone; require varying actuation and persistent error.
    window=[r for r in contiguous if r['ts']>=last['ts']-600 and r['ts']>=stable_from]
    if len(window)>=10 and window[-1]['ts']-window[0]['ts']>=300:
        vs=[r['data'].get('temperature') for r in window]; us=[r['data'].get('cooling') for r in window]
        if all(v is not None for v in vs+us) and max(vs)-min(vs)<.001 and max(us)-min(us)>20 and abs(vs[-1]-last['data'].get('temp_sp',vs[-1]))>2:
            results.append({'code':'sensor_frozen','priority':'warning','title':'Possível leitura congelada de temperatura',
                'evidence':{'start':window[0]['ts'],'end':last['ts'],'value':vs[-1],'command_span':max(us)-min(us)},
                'hypotheses':['Conferir resolução do ponto, aquisição e sensor; hipótese não confirma defeito.']})
        # Simple oscillation detector, not a PID auto-tuner. Constant SP is mandatory.
        sp=[r['data'].get('temp_sp') for r in window]
        if all(v is not None for v in vs+sp) and max(sp)==min(sp):
            threshold=.6; signs=[]
            for v,s in zip(vs,sp):
                d=v-s
                if abs(d)>threshold:
                    sg=1 if d>0 else -1
                    if not signs or signs[-1]!=sg: signs.append(sg)
            if len(signs)>=6 and max(vs)-min(vs)>2:
                results.append({'code':'temperature_oscillation','priority':'warning','title':'Oscilação recorrente de temperatura',
                    'evidence':{'start':window[0]['ts'],'end':last['ts'],'crossings':len(signs)-1,'amplitude':round(max(vs)-min(vs),3)},
                    'hypotheses':['Conferir carga, atuador, interação das malhas e sintonia; não alterar PID automaticamente.']})
    return results


def coverage(data,profile):
    checks=[]
    for label,required in [('Temperatura',['temperature','temp_sp','cooling','mode','fan_feedback']),
                           ('Umidade',['humidity','humidity_sp','mode','fan_feedback']),
                           ('Vazão',['airflow','airflow_sp','mode','fan_feedback'])]:
        missing=[k for k in required if data.get(k) is None]
        checks.append({'name':label,'missing':missing,'ready':not missing and bool(profile.get('validated')),
                       'status':'perfil pendente' if not profile.get('validated') else ('dados insuficientes' if missing else 'dados disponíveis')})
    from .fan_confirmation import pair
    enabled=bool(profile.get('validated')) and profile.get('fan_confirmation_validated') is True
    available=pair({'data':data,'quality':'good'}) is not None
    missing=[k for k in ('mode','fan_command','fan_feedback') if data.get(k) is None]
    checks.append({'name':'Comando/retorno do ventilador','missing':missing,'ready':enabled and available,
        'status':'comparação não autorizada' if not enabled else 'dados disponíveis' if available else 'dados/modo insuficientes'})
    return checks
