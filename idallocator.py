import gevent
from gevent.lock import RLock


class IDallocator(object):
    def __init__(self,start):
        self.mutex = RLock()
        self.start = start
        self.off = start
        self.free = []
        

    def acquire_id(self):
        self.mutex.acquire()
        if len(self.free) > 0:
            id = self.free.pop()
            return id
        id = self.off
        self.off = self.off + 1
        self.mutex.release()
        return id
    
    def release_id(self,id):
        self.mutex.acquire()
        self.free.append(id)
        #所有已分配的id都在空闲池中，则重置池和分配器
        if len(self.free) == (self.off - self.start):
            self.off = self.start
            self.free = []
        self.mutex.release()

