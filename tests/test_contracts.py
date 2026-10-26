import math
import struct
import pytest


def test_parser_requires_explicit_base():
    from app.importer import parse_protocol
    p = parse_protocol('symbol;area;address;type;scale\nT;holding;10;int16;0.1', address_base=None)
    assert not p['activatable']
    assert any('base' in e['message'].lower() for e in p['errors'])


def test_parser_decimal_and_zero_based_address():
    from app.importer import parse_protocol
    p = parse_protocol('symbol;area;address;type;scale;unit;access\nT;holding;11;int16;0,1;°C;RO', address_base=1)
    assert p['activatable']
    assert p['tags'][0]['address'] == 10
    assert p['tags'][0]['scale'] == .1
    assert p['tags'][0]['write_enabled'] is False


def test_unknown_line_never_silent():
    from app.importer import parse_protocol
    p = parse_protocol('symbol;area;address;type;scale\nT;holding;10;int16;0.1\nLIXO SEM FORMATO', address_base=0)
    assert not p['activatable']
    assert p['errors'][0]['line'] == 3
    assert 'LIXO' in p['errors'][0]['raw']


def test_duplicate_symbols_rejected():
    from app.importer import parse_protocol
    p = parse_protocol('symbol;area;address;type;scale\nT;holding;10;int16;0.1\nT;holding;11;int16;0.1', address_base=0)
    assert not p['activatable']


def test_missing_scale_not_guessed():
    from app.importer import parse_protocol
    p = parse_protocol('symbol;area;address;type\nT;holding;10;int16', address_base=0)
    assert not p['activatable']


def test_nan_scale_rejected():
    from app.importer import parse_protocol
    p = parse_protocol('symbol;area;address;type;scale\nT;holding;10;int16;nan', address_base=0)
    assert not p['activatable']


def test_same_numeric_address_different_areas_allowed():
    from app.importer import parse_protocol
    p = parse_protocol('symbol;area;address;type;scale\nT;holding;10;int16;1\nRUN;coil;10;bool;1', address_base=0)
    assert p['activatable']


def test_codec_signed_scale_once():
    from app.modbus import decode
    assert decode([65526], 'int16', .1) == -1


def test_codec_float_order():
    from app.modbus import decode
    a,b=struct.unpack('>HH', struct.pack('>f', 23.5))
    assert decode([b,a], 'float32', 1, word_order='little') == 23.5


def test_codec_nan_invalid():
    from app.modbus import decode
    with pytest.raises(ValueError): decode([0x7fc0,0], 'float32', 1)


def test_blocks_dont_cross_holes():
    from app.modbus import read_blocks
    tags=[{'id':1,'area':'holding','address':10,'data_type':'int16'},
          {'id':2,'area':'holding','address':11,'data_type':'int16'},
          {'id':3,'area':'holding','address':15,'data_type':'int16'}]
    blocks=read_blocks(tags)
    assert [(x['address'],x['count']) for x in blocks] == [(10,2),(15,1)]


def test_good_stable_sensor_not_automatically_frozen():
    from app.analysis import analyze
    rows=[{'ts':i*10,'data':{'temperature':22,'temp_sp':22,'cooling':30,'fan_feedback':1,'mode':1},'quality':'good'} for i in range(100)]
    assert not any(x['code']=='sensor_frozen' for x in analyze(rows,{'validated':True}))


def test_deviation_requires_duration():
    from app.analysis import analyze
    rows=[{'ts':0,'data':{'temperature':26,'temp_sp':22,'cooling':99,'fan_feedback':1,'mode':1},'quality':'good'}]
    assert not analyze(rows,{'validated':True,'settling_seconds':0,'persistence_seconds':300})


def test_deviation_persistent_and_saturated():
    from app.analysis import analyze
    rows=[{'ts':i*10,'data':{'temperature':26,'temp_sp':22,'cooling':99,'fan_feedback':1,'mode':1},'quality':'good'} for i in range(100)]
    codes={x['code'] for x in analyze(rows,{'validated':True,'settling_seconds':0,'persistence_seconds':300})}
    assert 'temperature_deviation' in codes
    assert 'cooling_saturation' in codes


def test_no_diagnosis_without_approved_profile_or_fresh_data():
    from app.analysis import analyze
    rows=[{'ts':i*10,'data':{'temperature':26,'temp_sp':22,'cooling':99,'fan_feedback':1,'mode':1},'quality':'bad'} for i in range(100)]
    assert analyze(rows,{'validated':True}) == []
    assert analyze(rows,{'validated':False}) == []


def test_password_not_plaintext():
    from app.security import hash_password, verify_password
    encoded=hash_password('Senh@-teste-2026')
    assert 'Senh@-teste-2026' not in encoded
    assert verify_password('Senh@-teste-2026',encoded)
    assert not verify_password('errada',encoded)


def test_csv_formula_escaped():
    from app.security import csv_safe
    assert csv_safe('=cmd()').startswith("'")
    assert csv_safe('texto') == 'texto'

def test_overlapping_32_bit_registers_rejected():
    from app.importer import parse_protocol
    text='symbol;area;address;type;scale;word_order;byte_order\nF1;holding;10;float32;1;big;big\nI2;holding;11;int16;1;big;big'
    result=parse_protocol(text,0)
    assert result['activatable'] is False
    assert any('sobrepos' in e['message'].lower() for e in result['errors'])

def test_32_bit_order_must_be_explicit():
    from app.importer import parse_protocol
    result=parse_protocol('symbol;area;address;type;scale\nF1;holding;10;float32;1',0)
    assert not result['activatable']

def test_reference_address_is_not_silently_remapped():
    from app.importer import parse_protocol
    result=parse_protocol('symbol;area;address;type;scale\nF1;holding;40001;int16;1',1)
    assert result['tags'][0]['address']==40000
