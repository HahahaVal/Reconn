import threading
from threading import Timer
import gevent
from gevent.lock import Semaphore
from configparser import ConfigParser
config = ConfigParser()
config.read('conf')

error = "conn close"

#前端服务
class ScpSever():
    def __init__(self,conn):
        self.conn = conn
        self.closed = False
        self.connerr = None
        self.sem = Semaphore(1)
        
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
    
    def close(self):
        if self.closed:
            return self.connerr
        self.conn.close()
        self.closed = True
        self.connerr = error
        self.sem.release()

    #超时计数
    def _star_wait(self):
        reuse_timeout = int(config['listen']['reuse_time'])
        time_task = Timer(reuse_timeout,self.close)
        time_task.start()

    def acquire_conn(self):
        while True:
            if self.closed:
                return None, self.connerr
            elif self.connerr:
                self._star_wait()
                self.sem.acquire()
            else:
                return self.conn, None

    def replace_conn(self, conn):
        if self.closed:
            return False
        #close old conn
        self.conn.close()
        self.conn = conn
        self.connerr = None
      
        return True
        
