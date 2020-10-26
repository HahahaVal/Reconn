import threading
from threading import Timer
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
        self.condition = threading.Condition()
        
    def read(self,size):
        conn, err = self.acquire_conn()
        if err:
            return '',err
        data,err = conn.read(size)
        if err:
            self.connerr = err
        return data, None


    def write(self,data):
        self.conn.write(data)
    
    def close(self):
        if self.closed:
            return self.connerr
        self.conn.close()
        self.closed = True
        self.connerr = error
        self.condition.acquire()
        self.condition.notify()
        self.condition.wait()

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
                self.condition.acquire()
                self.condition.wait()
            else:
                return self.conn, None

