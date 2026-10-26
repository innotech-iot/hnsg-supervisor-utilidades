"""Deterministic engineering fixtures, never hospital limits or CAREL registers.

Daily thermal load and slow control ripple keep signals correlated. This is a
synthetic steady-state model, not a validated thermodynamic plant or controller.
"""
import math


def plant_values(asset_id, kind, stamp, overrides=None, scenario='normal'):
    load = .55 + .2 * math.sin(2 * math.pi * (stamp / 86400 - .35))
    ripple = math.sin(stamp / 180 + asset_id * .7)
    if kind in {'cag', 'caq'}:
        supply = (7 + .25 * ripple) if kind == 'cag' else (48 + .6 * ripple)
        delta = 3 + 3 * load
        return {'supply_temperature': round(supply, 2),
                'return_temperature': round(supply + (delta if kind == 'cag' else -delta), 2),
                'pump_command': 1, 'pump_feedback': 1}, 'good'
    ov = overrides or {}
    mode = int(ov.get('mode', 1))
    running = mode != 0
    sp = float(ov.get('temp_sp', 22))
    hsp = float(ov.get('humidity_sp', 55))
    fsp = float(ov.get('airflow_sp', 2200 + asset_id * 60))
    speed = 65 + 8 * load + 1.2 * ripple
    cooling = 25 + 45 * load + 3 * ripple
    dehum = running and asset_id in {8, 12}
    data = {'temperature': round(sp + .22 * ripple if running else sp + 3 + load, 2),
            'temp_sp': sp, 'humidity': round(hsp + 1.3 * math.sin(stamp / 240 + asset_id), 2),
            'humidity_sp': hsp, 'airflow_sp': fsp,
            'airflow': round(fsp * (1 + .012 * ripple) if running else 0, 1),
            'pressure': round(220 * (speed / 72) ** 2 if running else 0, 1),
            'fan_speed': round(speed if running else 0, 1),
            'cooling': round(cooling if running else 0, 1),
            'heating': round(10 + 2 * ripple, 1) if dehum else 0.,
            'fan_command': int(running), 'fan_feedback': int(running),
            'mode': mode, 'dehumidifying': int(dehum)}
    if scenario == 'faults':
        if asset_id == 11:
            return dict.fromkeys(data), 'bad'
        if running and asset_id == 3:
            data.update(temperature=round(sp + 3.1 + .25 * ripple, 2), cooling=98.4)
        if running and asset_id == 7:
            wave = math.sin(stamp / 38)
            data.update(temperature=round(sp + 1.7 * wave, 2), cooling=round(55 + 27 * wave, 1))
        if running and asset_id == 8:
            data['humidity'] = round(hsp + 10.5 + .5 * ripple, 2)
    return data, 'good'
