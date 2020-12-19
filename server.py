#codeing=utf-8
import conn
import gevent
import scpconn
import common
import sys
import upstream
import idallocator
from gevent.lock import RLock
from gevent import monkey,socket
monkey.patch_all()

from configparser import ConfigParser
config = ConfigParser()
config.read('conf')

class ConnPair():
    def __init__(self,remote,local):
        self.remote_conn = remote
        self.local_conn = local

    def _pump(self,id,tag,dst,src):
        while True:
            data, err = src.read(common.NetBufferSize)
            if len(data) > 0 :
                err = dst.write(data)
                if err:
                    break
            if err:
                break

        src.close()
        dst.close()
                
    def pump(self):
        gevent.spawn(self._pump,id,"c2s",self.local_conn,self.remote_conn)
        gevent.spawn(self._pump,id,"s2c",self.remote_conn,self.local_conn)


class Server():
    def __init__(self):
        self.conn_pairs = {}
        self.id_allocator = idallocator.IDallocator(1)
        self.conn_pair_mutex = RLock()

    def acquire_id(self):
        return self.id_allocator.acquire_id()

    def query_by_id(self,id):
        self.conn_pair_mutex.acquire()
        pair = self.conn_pairs[id]
        self.conn_pair_mutex.release()
        return pair

    def _add_pair_id(self,conn_id,conn_pair):
        self.conn_pair_mutex.acquire()
        self.conn_pairs[conn_id] = conn_pair
        self.conn_pair_mutex.release()

    def _on_reuse_conn(self,conn_obj):
        conn_id = conn_obj.get_id()
        pair = self.query_by_id(conn_id)
        if not pair:
            print(__file__, sys._getframe().f_lineno, "reuse pair not find")
            return False
        ret = pair.remote_conn.replace_conn(conn_obj)
        if not ret:
            print(__file__, sys._getframe().f_lineno, "replace conn failed")
            return False
        print(__file__, sys._getframe().f_lineno, "replace conn success")
        return True

    def _on_new_conn(self,conn_obj):
        conn_id = conn_obj.get_id()
        remote_conn = scpconn.ScpSever(conn_obj)
        local_conn = upstream.Upstream()

        conn_pair = ConnPair(remote_conn,local_conn)
        self._add_pair_id(conn_id, conn_pair) 
        conn_pair.pump()
        return True

    def _handle_conn(self,rd_socket):
        conn_obj = conn.Scon(self,rd_socket)
        ret = conn_obj.hand_shake()
        if not ret:
            conn_obj.close()

        if conn_obj.is_reused():
            ret = self._on_reuse_conn(conn_obj)
        else:
            ret = self._on_new_conn(conn_obj)
        if not ret:
            conn_obj.close()
    
    def server(self):
        addr = str(config['listen']['addr'])
        port = int(config['listen']['port'])
        max_accept = int(config['listen']['max_accept'])
        timeout = int(config['listen']['timeout'])
        
        listen_socket = socket.socket()
        address = (addr,port)
        try:
            #set socket reuse
            listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_socket.bind(address)
            listen_socket.listen(max_accept)
        except:
            print(__file__, sys._getframe().f_lineno, "listen failed")
            sys.exit(1)
            
        while True:
            try:
                rd_socket, addr = listen_socket.accept()
                rd_socket.settimeout(timeout)
                print(__file__, sys._getframe().f_lineno, "new connect fd:%d, addr:%s"%(rd_socket.fileno(),addr))
                gevent.spawn(self._handle_conn,rd_socket)
            except:
                print(__file__, sys._getframe().f_lineno, "accept failed")
                sys.exit(1)
        listen_socket.close()
