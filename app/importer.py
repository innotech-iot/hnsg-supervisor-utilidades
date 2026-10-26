"""Explicit delimited TXT contract. Actual CAREL dialect awaits the user's files.
No best-effort numeric guessing: every noncomment line is accounted for.
"""
from __future__ import annotations
import csv
import hashlib
import io
import math
import re
import unicodedata

ALIASES={
    'symbol':{'symbol','simbolo','nome','name','tag','variavel','variable'},
    'description':{'description','descricao','descrizione','desc'},
    'area':{'area','table','tabela','register_area'},
    'address':{'address','endereco','offset_address','registro'},
    'data_type':{'type','tipo','data_type','datatype'},
    'scale':{'scale','escala','fator'},
    'offset':{'offset','bias'},
    'unit':{'unit','unidade'},
    'access':{'access','acesso'},
    'word_order':{'word_order','ordem_palavras'},
    'byte_order':{'byte_order','ordem_bytes'},
}
AREAS={'holding':'holding','holding_register':'holding','hr':'holding','03':'holding',
       'input':'input','input_register':'input','ir':'input','04':'input',
       'coil':'coil','coils':'coil','01':'coil','discrete':'discrete','di':'discrete','02':'discrete'}
TYPES={'int16':'int16','uint16':'uint16','int32':'int32','uint32':'uint32','float32':'float32','bool':'bool'}

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.strip().lower()) if unicodedata.category(c)!='Mn').replace(' ','_')

def number(s):
    # Only an explicit decimal comma or dot, never a thousands separator heuristic.
    x=float(str(s).strip().replace(',','.'))
    if not math.isfinite(x): raise ValueError('número não finito')
    return x

def parse_protocol(text: str, address_base: int | None, delimiter: str | None=None) -> dict:
    result={'format':'delimited-explicit-v1','carel_dialect_verified':False,'tags':[], 'errors':[],
            'warnings':['Adaptador genérico: formato CAREL definitivo depende de arquivo real e validação.'],
            'activatable':False,'address_base':address_base,
            'sha256':hashlib.sha256(text.encode()).hexdigest(),'line_count':len(text.splitlines())}
    def error(line,raw,message): result['errors'].append({'line':line,'raw':raw[:1000],'message':message})
    if len(text.encode())>2_000_000:
        error(0,'','Arquivo excede 2 MB'); return result
    if address_base not in {0,1}:
        error(0,'','Base de endereço 0 ou 1 deve ser explicitamente confirmada'); return result
    lines=[(i,line) for i,line in enumerate(text.lstrip('\ufeff').splitlines(),1)
           if line.strip() and not line.lstrip().startswith(('#','//'))]
    if not lines:
        error(0,'','Arquivo vazio'); return result
    if len(lines)>5001:
        error(0,'','Limite de 5000 pontos por importação'); return result
    header=lines[0][1]
    if delimiter not in {';',',','\t','|'}:
        delimiter=next((d for d in [';','\t','|',','] if d in header),None)
    if not delimiter:
        error(lines[0][0],header,'Cabeçalho delimitado não reconhecido. Não houve importação.'); return result
    try:
        raw_headers=next(csv.reader([header],delimiter=delimiter,strict=True))
        headers=[]
        for h in raw_headers:
            key=norm(h)
            headers.append(next((a for a, names in ALIASES.items() if key in names),key))
        if len(headers)!=len(set(headers)):
            error(lines[0][0],header,'Colunas repetidas'); return result
        for col in ['symbol','area','address','data_type','scale']:
            if col not in headers: error(lines[0][0],header,f'Coluna obrigatória ausente: {col}')
        if result['errors']: return result
        seen=set(); locations=set()
        unknown=set(headers)-set(ALIASES)
        if unknown: result['warnings'].append('Colunas preservadas em metadata: '+', '.join(sorted(unknown)))
        for line, raw in lines[1:]:
            try:
                vals=next(csv.reader([raw],delimiter=delimiter,strict=True))
                if len(vals)!=len(headers): raise ValueError('Número de campos diferente do cabeçalho; linhas multilinha não suportadas')
                row=dict(zip(headers,[v.strip() for v in vals]))
                symbol=row['symbol']
                if not symbol or len(symbol)>200: raise ValueError('Nome vazio ou maior que 200 caracteres')
                if symbol in seen: raise ValueError('Símbolo repetido no mesmo CLP')
                area=AREAS.get(norm(row['area']))
                if not area: raise ValueError('Área Modbus desconhecida; não inferir por número de endereço')
                dtype=TYPES.get(norm(row['data_type']))
                if not dtype: raise ValueError('Tipo desconhecido; informar int16/uint16/int32/uint32/float32/bool')
                if area in {'coil','discrete'} and dtype!='bool': raise ValueError('Área de bits requer tipo bool')
                addr=int(row['address'],10)-address_base
                count=2 if dtype in {'int32','uint32','float32'} else 1
                if addr<0 or addr+count>65536: raise ValueError('Endereço fora da faixa Modbus')
                occupied={(area,addr+i) for i in range(count)}
                if occupied & locations: raise ValueError('Sobreposição de endereço/área; aliases exigem revisão manual')
                scale=number(row['scale'])
                if scale==0: raise ValueError('Escala zero não é aceita')
                offset=number(row.get('offset') or '0')
                if dtype=='bool' and (scale!=1 or offset!=0): raise ValueError('Bool requer escala 1 e offset 0')
                word=row.get('word_order') or ('big' if count==1 else '')
                byte=row.get('byte_order') or ('big' if count==1 else '')
                if word not in {'big','little'} or byte not in {'big','little'}:
                    raise ValueError('Tipos de 32 bits requerem word_order e byte_order explícitos (big/little)')
                access=(row.get('access') or 'RO').upper()
                if access not in {'RO','RW'}: raise ValueError('Acesso deve ser RO ou RW')
                if area in {'input','discrete'} and access!='RO': raise ValueError('Área somente leitura não aceita RW')
                if not row.get('access'): result['warnings'].append(f'Linha {line}: acesso ausente; escrita permanece bloqueada')
                seen.add(symbol); locations.update(occupied)
                result['tags'].append({'symbol':symbol,'description':row.get('description','')[:500],
                    'area':area,'address':addr,'source_address':row['address'],'data_type':dtype,'scale':scale,
                    'offset':offset,'unit':row.get('unit','')[:40],'access':access,'word_order':word,'byte_order':byte,
                    'validated':False,'write_enabled':False,'metadata':{k:row[k] for k in unknown},'line':line})
            except (ValueError,csv.Error) as exc:
                error(line,raw,str(exc))
    except csv.Error as exc:
        error(lines[0][0],header,str(exc))
    if not result['tags'] and not result['errors']: error(0,'','Nenhum ponto reconhecido')
    result['activatable']=bool(result['tags']) and not result['errors']
    return result


def signature(tag: dict) -> tuple:
    return tuple(tag.get(k) for k in ('area','address','data_type','scale','offset','unit','access','word_order','byte_order'))
