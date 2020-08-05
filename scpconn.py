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
        self.conn.close()
        self.closed = True
        self.connerr = error

    #超时计数
    def _star_wait(self):
        reuse_timeout = int(config['listen']['reuse_time'])
        time_task = Timer(reuse_timeout,self.close)
        time_task.start()
        time_task.join()

    def acquire_conn(self):
        while True:
            if self.closed:
                return None, self.connerr
            elif self.connerr:
                self._star_wait()
            else:
                return self.conn, None

