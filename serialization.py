import struct
import hashlib
import math
def unit64(v):
    return int.from_bytes(v, byteorder = 'little')

def to_byte8(v):
    return (v).to_bytes(8,byteorder = 'little')

def to_byte4(v):
    return (v).to_bytes(4,byteorder = 'little')

def hmac(x,y):
    w = bytearray()
    w[0:8] = x[:]
    w[8:16] = y[:]
    w[16:32] = w[0:16] 
    w[32:48] = w[0:16]

    md5 = hashlib.md5()
    md5.update(w[:])
    v = md5.digest()
    
    a = v[:8]
    b = v[8:]
    return to_byte8(unit64(a) ^ unit64(b))
    
def hashc(s):
    djb_hash = 5381
    js_hash  = 1315423911
    #32bit pow(2,32)
    overflow = int(math.pow(2,32))
    for c in s:
        djb_hash += (djb_hash << 5) + c
        if djb_hash > overflow:
            djb_hash = djb_hash % overflow

        js_hash ^= ((js_hash << 5) + c + (js_hash >> 2))
        if js_hash > overflow:
            js_hash = js_hash % overflow
    
    v = bytearray()
    v[:4] = to_byte4(djb_hash)
    v[4:] = to_byte4(js_hash)
    return v