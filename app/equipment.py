"""Equipment-specific read-only semantics; no assumed plant limits or sequence."""
from .analysis import CATALOG

WATER_CATALOG={
    'supply_temperature':{'label':'Temperatura de ida da água','unit':'°C','color':'cyan'},
    'return_temperature':{'label':'Temperatura de retorno da água','unit':'°C','color':'orange'},
    'pump_command':{'label':'Comando da bomba associada','unit':'boolean'},
    'pump_feedback':{'label':'Retorno da bomba associada','unit':'boolean'},
}
ALL_CATALOG=CATALOG|WATER_CATALOG


def catalog_for(kind):
    return CATALOG if kind=='uta' else WATER_CATALOG if kind in {'cag','caq'} else {}


def equipment_coverage(kind,data,profile):
    if kind=='uta':
        from .analysis import coverage
        return coverage(data,profile)
    return [{'name':'Diagnóstico específico da central','missing':[], 'ready':False,
             'status':'sequência e detectores da central pendentes de comissionamento'}]
