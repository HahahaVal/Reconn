import gevent
from gevent.lock import Semaphore


class IDallocator(object):
    def __init__(self,start):
        self.sem = Semaphore(1)
        self.start = start
        self.off = start
        self.free = []
        

    def acquire_id(self):
        self.sem.acquire()
        if len(self.free) > 0:
            index = len(self.free) - 1
            id = self.free.pop(index)
            return id
        id = self.off
        self.off = self.off + 1
        self.sem.release()
        return id
    
    def release_id(self,id):
        self.sem.acquire()
        index = len(self.free)
        self.free.append(id)
        #所有已分配的id都在空闲池中，则重置池和分配器
        if len(self.free) == (self.off - self.star):
            self.off = self.start
            self.free = []
        self.sem.release()

