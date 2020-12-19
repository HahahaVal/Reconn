import sys
import gevent
from gevent import monkey,socket
monkey.patch_all()

from configparser import ConfigParser
config = ConfigParser()
config.read('conf')

#后端服务
class Upstream():
    def __init__(self):
        s_socket = socket.socket()
        addr = str(config['host']['addr'])
        port = int(config['host']['port'])
        address = (addr,port)
        s_socket.connect(address)
        self.conn = s_socket
        
    def read(self,size):
        try:
            data = self.conn.recv(size)
            if len(data)==0:
                return '', "server close"
            return data, None
        except Exception as err:
            return '', err

    def write(self,data):
        try:
            self.conn.send(data)
            return None
        except Exception as err:
            return err
        
    
    def close(self):
        self.conn.close()
        print(__file__, sys._getframe().f_lineno, "local conn close")