import threading
from threading import Timer
import gevent
from gevent.lock import Semaphore
from gevent.lock import RLock
from gevent import monkey,socket
from goto import with_goto
monkey.patch_all()

from configparser import ConfigParser
config = ConfigParser()
config.read('conf')

error = "scpconn close"

#前端服务
class ScpSever():
    def __init__(self,conn):
        self.conn = conn
        self.closed = False
        self.connerr = None
        self.conn_mutex = RLock()
        self.conn_cond = Semaphore(0)
        
    def read(self,size):
        conn, err = self.acquire_conn()
        if err: #conn is closed
            return '',err
        data,err = conn.read(size)
        if err:
            #freeze, waiting for reuse
            conn.freeze()
            self.connerr = err
        return data, None


    def write(self,data):
        conn, err = self.acquire_conn()
        if err: #conn is closed
            return '',err
        err = self.conn.write(data)
        if err:
            #freeze, waiting for reuse
            conn.freeze()
            self.connerr = err
        return None
    
    @with_goto
    def close(self):
        self.conn_mutex.acquire()
        if self.closed:
            goto .end
        self.conn.close()
        self.closed = True
        self.connerr = error
        label .end
        self.conn_cond.release()
        self.conn_mutex.release()
        return self.connerr

    #超时计数
    def _star_wait(self):
        reuse_timeout = int(config['listen']['reuse_time'])
        self.time_task = Timer(reuse_timeout,self.close)
        self.time_task.start()

    def _stop_wait(self):
        self.time_task.cancel()

    def _cond_wait(self):
        self.conn_mutex.release()
        self.conn_cond.acquire()
        self.conn_mutex.acquire()

    def acquire_conn(self):
        self.conn_mutex.acquire()
        conn = None
        connerr = None
        while True:
            if self.closed:
                connerr = self.connerr
                break
            elif self.connerr:
                self._star_wait()
                self._cond_wait()
                self._stop_wait()
            else:
                conn = self.conn
                break
        self.conn_mutex.release()
        return conn, connerr

    @with_goto
    def replace_conn(self, conn):
        self.conn_mutex.acquire()
        ret = False
        if self.closed:
            goto .end
        #close old conn
        self.conn.close()
        #set new status
        self.conn = conn
        self.connerr = None
        ret = True
        label .end
        self.conn_cond.release()
        self.conn_mutex.release()
        return ret
        
