import messages
import loopbuffer
import struct
import dh64
import serialization
import sys
from gevent.lock import Semaphore
from common import ErrCode
from Crypto.Cipher import ARC4
import traceback

error = "conn close"
class CipherReader():
    def __init__(self, cipher, conn):
        self.cipher = cipher
        self.count = 0
        self.rd = conn
    def read(self,size):
        try:
            data = self.rd.recv(size)
            if len(data)==0:
                return '', error
            decrypt_data = self.cipher.decrypt(data)
            self.count += size
            return decrypt_data, None
        except Exception as err:
            return '', err



class CipherWriter():
    def __init__(self, cipher, conn):
        self.cipher = cipher
        self.count = 0
        self.reuse_buffer = loopbuffer.LoopBuffer()
        self.wr = conn
    def write(self,data):
        try:
            self.reuse_buffer.write(data)
            encrypt_data = self.cipher.encrypt(data)
            self.wr.send(encrypt_data)
            self.count += len(data)
            return None
        except Exception as err:
            return err
            
    

class Scon(object):
    def __init__(self,server,conn):
        self.server = server
        self.conn = conn
        self.reuse = False
        self.handshakes = 0
        self.id = 0
        self.sem = Semaphore(1)

    def get_id(self):
        return self.id

    def gen_rc4_key(self,v1,v2):
        h = serialization.hmac(v1,v2)
        return h[:]
    
    def deepcopy_cipherreader(self,old):
        new = CipherReader(old.cipher,old.rd)
        new.count = old.count
        return new

    def deepcopy_cipherwriter(self,old):
        new = CipherWriter(old.cipher,old.wr)
        new.count = old.count
        return new

    def _new_conn_reader(self,secret):
        key = bytearray()
        h = self.gen_rc4_key(secret, serialization.to_byte8(0))
        key[0:8] = h
        h = self.gen_rc4_key(secret, serialization.to_byte8(1))
        key[8:16] = h
        h = self.gen_rc4_key(secret, serialization.to_byte8(2))
        key[16:24] = h
        h = self.gen_rc4_key(secret, serialization.to_byte8(3))
        key[24:32] = h
        rc4 = ARC4.new(bytes(key))
        return CipherReader(rc4,self.conn)

    def _new_conn_writer(self,secret):
        key = bytearray()
        h = self.gen_rc4_key(secret, serialization.to_byte8(0))
        key[0:8] = h
        h = self.gen_rc4_key(secret, serialization.to_byte8(1))
        key[8:16] = h
        h = self.gen_rc4_key(secret, serialization.to_byte8(2))
        key[16:24] = h
        h = self.gen_rc4_key(secret, serialization.to_byte8(3))
        key[24:32] = h
        rc4 = ARC4.new(bytes(key))
        return CipherWriter(rc4,self.conn)


    def _read_record(self):
        size = struct.unpack('>H', self.conn.recv(2))
        size = int(size[0])
        data = self.conn.recv(size)
        print(__file__, sys._getframe().f_lineno, "_read_record: ",size,type(data),data)
        return data

    def _write_record(self, data):
        size = struct.pack('>H', len(data))
        self.conn.send(size)
        self.conn.send(data)
        print(__file__, sys._getframe().f_lineno, "_write_record : ",size,type(data),data)


    def _new_handshake(self,conn_req):
        self.reuse = False
        self.id = self.server.acquire_id()
        print(__file__, sys._getframe().f_lineno, "new handshake id = ",self.id)

        prikey = dh64.private_key()
        pubkey = dh64.public_key(prikey)
        pubkey = serialization.to_byte8(pubkey)

        resp = messages.NewConnResp(self.id,pubkey)
        data = resp.marshal()
        self._write_record(data)

        conn_req_key = serialization.unit64(conn_req.key)
        secret = dh64.secret(prikey,conn_req_key)

        self.secret = serialization.to_byte8(secret)
        self.reader = self._new_conn_reader(self.secret)
        self.writer = self._new_conn_writer(self.secret)
        return True
    
    def _spawn(self,new):
        self.freeze()
        new.id = self.id
        new.secret = self.secret
        new.reader = self.deepcopy_cipherreader(self.reader)
        new.writer = self.deepcopy_cipherwriter(self.writer)
        new.reuse = True


    def _reuse_handshake(self,conn_req):
        diff = 0
        resp = messages.ReuseConnResp()

        while True:
            pair = self.server.query_by_id(conn_req.id)
            old_conn = pair.remote_conn.conn
            if not old_conn:
                resp.code = ErrCode['SCPStatusIDNotFound']
                break
            if not conn_req.verify_sum(old_conn.secret):
                resp.code = ErrCode['SCPStatusUnauthorized']
                break
            if old_conn.handshakes >= conn_req.handshakes:
                resp.code = ErrCode['SCPStatusExpired']
                break
            self.handshakes = conn_req.handshakes
            #all check pass, spawn new conn
            old_conn._spawn(self)
            diff = self.writer.count - conn_req.received
            if diff < 0 :
                resp.code = ErrCode['SCPStatusNotAcceptable']
                break
            resp.received = self.reader.count
            break

        data = resp.marshal()
        self._write_record(data)
        if diff > 0:
            last_bytes = self.writer.reuse_buffer.read_last_bytes(diff)
            self.write(last_bytes)
        return True

    def hand_shake(self):
        self.sem.acquire()
        
        data = self._read_record()
        sq = messages.ServerReq()
        q = sq.unmarshal(data)
        if isinstance(q,messages.NewConnReq):
            return self._new_handshake(q)
        elif isinstance(q,messages.ReuseConnReq):
            return self._reuse_handshake(q)
        else:
            print(__file__, sys._getframe().f_lineno, "hand_shake error")
            return False
        self.sem.release()

    
    def is_reused(self):
        return self.reuse

    def read(self,size):
        return self.reader.read(size)
        
    def write(self,data):
        return self.writer.write(data)

    
    #Close closes raw conn and releases all resources. After close, c can't be reused.
    def close(self):
        traceback.print_stack()
        self.conn.close()
        print(__file__, sys._getframe().f_lineno, "remote conn close")
    
    #Freeze make conn frozen, and wait for resue
    def freeze(self):
        traceback.print_stack()
        self.conn.close()
        print(__file__, sys._getframe().f_lineno, "remote conn freeze")