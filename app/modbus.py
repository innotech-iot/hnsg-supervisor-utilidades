"""Small READ-ONLY Modbus TCP transport (FC 01/02/03/04).
No write opcode exists in this module. No discovery or network scanning.
Every frame is length/transaction/protocol/unit/function checked.
Commissioning on actual CAREL hardware remains mandatory.
"""
from __future__ import annotations
import math
import secrets
import socket
import struct

FUNCTIONS={'coil':1,'discrete':2,'holding':3,'input':4}
WIDTH={'bool':1,'int16':1,'uint16':1,'int32':2,'uint32':2,'float32':2}

class ModbusError(Exception): pass

def decode(registers, data_type, scale=1., offset=0., word_order='big', byte_order='big'):
    if data_type not in WIDTH or len(registers)!=WIDTH[data_type]: raise ValueError('Tamanho/tipo inválido')
    if word_order not in {'big','little'} or byte_order not in {'big','little'}: raise ValueError('Ordem inválida')
    words=list(registers)
    if any(not isinstance(v,int) or v<0 or v>65535 for v in words): raise ValueError('Word inválida')
    if word_order=='little': words.reverse()
    raw=b''.join(v.to_bytes(2,'big')[::(-1 if byte_order=='little' else 1)] for v in words)
    if data_type=='bool':
        value=words[0]
        if value not in {0,1}: raise ValueError('Valor booleano diferente de 0/1')
    else:
        value=struct.unpack('>'+{'int16':'h','uint16':'H','int32':'i','uint32':'I','float32':'f'}[data_type],raw)[0]
    value=float(value)*scale+offset
    if not math.isfinite(value): raise ValueError('Leitura/conversão não finita')
    return value


def read_blocks(tags, max_registers=60):
    blocks=[]
    for area in FUNCTIONS:
        subset=sorted([t for t in tags if t['area']==area],key=lambda t:t['address'])
        limit=max_registers if area in {'holding','input'} else 512
        for tag in subset:
            size=WIDTH[tag['data_type']]
            if blocks and blocks[-1]['area']==area and tag['address']==blocks[-1]['address']+blocks[-1]['count'] and blocks[-1]['count']+size<=limit:
                blocks[-1]['tags'].append(tag); blocks[-1]['count']+=size
            else:
                blocks.append({'area':area,'address':tag['address'],'count':size,'tags':[tag]})
    return blocks


def recv_exact(sock,size):
    data=bytearray()
    while len(data)<size:
        chunk=sock.recv(size-len(data))
        if not chunk: raise ModbusError('Conexão encerrada durante a resposta')
        data.extend(chunk)
    return bytes(data)


def read_tcp(host,port,unit_id,area,address,count,timeout=1.5):
    if area not in FUNCTIONS or not 0<=unit_id<=255: raise ValueError('Área/Unit ID inválidos')
    limit=2000 if area in {'coil','discrete'} else 125
    if not 1<=count<=limit or address<0 or address+count>65536: raise ValueError('Faixa inválida')
    tid=secrets.randbelow(65536); function=FUNCTIONS[area]
    request=struct.pack('>HHHBBHH',tid,0,6,unit_id,function,address,count)
    with socket.create_connection((host,port),timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        tx,protocol,length,unit=struct.unpack('>HHHB',recv_exact(sock,7))
        if tx!=tid or protocol!=0 or unit!=unit_id or not 2<=length<=254:
            raise ModbusError('Cabeçalho MBAP inválido')
        pdu=recv_exact(sock,length-1)
        if pdu[0]==(function|0x80):
            raise ModbusError(f'Exceção Modbus {pdu[1] if len(pdu)>1 else "?"}')
        expected=(count+7)//8 if area in {'coil','discrete'} else count*2
        if len(pdu)!=expected+2 or pdu[0]!=function or pdu[1]!=expected:
            raise ModbusError('Função/quantidade de bytes incompatível')
        if area in {'coil','discrete'}:
            return [(pdu[2+i//8]>>(i%8))&1 for i in range(count)]
        return list(struct.unpack('>'+'H'*count,pdu[2:]))


def read_controller(controller,tags,previous=None):
    """One controller worker; failures of one block do not forge values in other blocks."""
    import time
    result={}; errors=[]; started=time.monotonic()
    for block in read_blocks(tags):
        try:
            if time.monotonic()-started>6:
                raise ModbusError('Orçamento de aquisição excedido; reduzir blocos/ajustar frequências no comissionamento')
            values=read_tcp(controller['host'],controller['port'],controller['unit_id'],
                            block['area'],block['address'],block['count'])
            stamp=time.time()
            for tag in block['tags']:
                start=tag['address']-block['address']
                try:
                    value=decode(values[start:start+WIDTH[tag['data_type']]],tag['data_type'],tag['scale'],
                                 tag.get('offset',0),tag.get('word_order','big'),tag.get('byte_order','big'))
                    result[str(tag['id'])]={'value':value,'raw':values[start:start+WIDTH[tag['data_type']]],'ts':stamp,'quality':'good'}
                except ValueError as exc:
                    result[str(tag['id'])]={'value':None,'ts':stamp,'quality':'invalid','error':str(exc)}
        except (OSError,ValueError,ModbusError) as exc:
            errors.append(str(exc))
            for tag in block['tags']:
                result[str(tag['id'])]={'value':None,'ts':time.time(),'quality':'bad','error':str(exc)}
    return {'points':result,'errors':errors[:10]}
