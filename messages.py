import base64
import serialization
from common import ErrCode

class ServerReq(object):
    def __init__(self):
        pass
    def unmarshal(self,data):
        if data.startswith(b"0\n"):
            nq = NewConnReq()
            nq.unmarshal(data)
            return nq
        else:
            rq = ReuseConnReq()
            rq.unmarshal(data)
            return rq

    def marshal(self):
        pass

class NewConnReq(object):
    def __init__(self):
        self.key = bytes(8)

    def unmarshal(self,data):
        lines = str(data,'utf8').split("\n")
        if len(lines) < 2:
            raise
        self.id = int(lines[0])
        self.key = base64.b64decode(lines[1])

    def marshal(self):
        pass

class ReuseConnReq(object):
    def __init__(self):
        self.sum = bytes(8)

    def unmarshal(self,data):
        lines = str(data,'utf8').split("\n")
        if len(lines) < 4:
            raise
        self.id = int(lines[0])
        self.handshakes = int(lines[1])
        self.received = int(lines[2])
        self.sum = base64.b64decode(lines[3])

    def marshal(self):
        pass
    
    def verify_sum(self,secret):
        data = "{:d}\n{:d}\n{:d}\n".format(self.id, self.handshakes, self.received)
        hash_data = serialization.hashc(bytes(data,"utf-8"))
        rsum = serialization.hmac(hash_data,secret)
        return rsum == self.sum



class NewConnResp(object):
    def __init__(self,id,key):
        #标识服务器的唯一conn
        self.id = id
        self.key = key
    def unmarshal(self,data):
        pass
    def marshal(self):
        key = base64.b64encode(self.key).decode()
        data = "{:d}\n{:s}".format(self.id,key)
        return bytes(data,"utf-8")

class ReuseConnResp(object):
    def __init__(self):
        self.received = 0
        self.code = ErrCode['SCPStatusOK']
        
    def unmarshal(self,data):
        pass

    def marshal(self):
        data = "{:d}\n{:d}".format(self.received,self.code)
        return bytes(data,"utf-8")