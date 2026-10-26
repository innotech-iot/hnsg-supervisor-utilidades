import socketserver
import struct
import threading
import pytest
from app.modbus import read_tcp, ModbusError

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
    daemon_threads=True
class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        req=b''
        while len(req)<12:
            piece=self.request.recv(12-len(req))
            if not piece:return
            req+=piece
        tid,protocol,length,unit,fc,addr,count=struct.unpack('>HHHBBHH',req)
        self.server.seen.append(fc)
        if addr==99:pdu=bytes([fc|128,2])
        elif fc in [1,2]:pdu=bytes([fc,(count+7)//8])+bytes([0b01010101])*((count+7)//8)
        else:pdu=bytes([fc,count*2])+struct.pack('>'+'H'*count,*range(addr,addr+count))
        if addr==88:tid+=1
        response=struct.pack('>HHHB',tid,0,len(pdu)+1,unit)+pdu
        # Split every response deliberately to exercise exact receive.
        try:
            for byte in response:self.request.sendall(bytes([byte]))
        except (BrokenPipeError,ConnectionResetError):
            # Expected when the client rejects the intentionally invalid MBAP early.
            pass

@pytest.fixture
def server():
    s=Server(('127.0.0.1',0),Handler);s.seen=[]
    t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
    yield s
    s.shutdown();s.server_close();t.join()

def test_holding_split_frames(server):
    assert read_tcp('127.0.0.1',server.server_address[1],1,'holding',10,3)==[10,11,12]
    assert server.seen==[3]

def test_discrete_bits(server):
    assert read_tcp('127.0.0.1',server.server_address[1],1,'discrete',0,4)==[1,0,1,0]
    assert server.seen==[2]

def test_exception_response(server):
    with pytest.raises(ModbusError,match='Exceção'):
        read_tcp('127.0.0.1',server.server_address[1],1,'input',99,1)

def test_wrong_transaction_rejected(server):
    with pytest.raises(ModbusError,match='MBAP'):
        read_tcp('127.0.0.1',server.server_address[1],1,'holding',88,1)

def test_write_functions_do_not_exist():
    import app.modbus as driver
    assert not any(name.startswith('write') for name in vars(driver))
