import common

class LoopBuffer():
    def __init__(self):
        self.off = 0
        self.looped = False
        self.buf = bytearray()

    def get_len(self):
        return len(self.buf)
    
    def write(self,data):
        capacity = common.LoopBuffSize
        n = len(data)
        if n > capacity:
            self.buf = data[n-capacity:]
            self.looped = True
            self.off = 0
            return 
        
        right = capacity - self.off
        if n < right:
            self.buf[self.off:] = data[:]
            self.off += n
            return
        
        #从off开始填充满buf后，把数据往buf头继续填充，同时移动off
        self.buf[self.off:] = data[:right]
        self.buf[0:] = data[right:]
        self.looped = True
        self.off = n - right
    
    def read_last_bytes(self,n):
        capacity = common.LoopBuffSize
        data = bytearray()
        if n > self.get_len():
            return
        #buf中有足够的数据，则从off标记处往前读n个字节
        if n <= self.off:
            data = self.buf[self.off-n:self.off]
            return data

        #buf中没有足够的数据，则先从尾部取一定数量再拷贝
        wrapped = n - self.off
        data[0:] = self.buf[capacity-wrapped:]
        data[wrapped:] = self.buf[:self.off]