import random

p = 0xffffffffffffffc5
g = 0x0000000000000005

def mulModP(a,b):
    m = 0x0000000000000000
    while b>0:
        if b&1 > 0:
            t = p - a
            if m >= t:
                m -= t
            else:
                m += a
        if a >= p-a:
            a = a*2 - p
        else:
            a = a * 2
        b >>= 1
    return m

def powModP(a,b):
    if b == 1:
        return a
    t = powModP(a, b>>1)
    t = mulModP(t,t)
    if b%2 > 0:
        t = mulModP(t,a)
    return t

def _powmodp(a,b):
    if a == 0:
        raise ValueError('invalid value: %s' % a)
    if b == 0:
        raise ValueError('invalid value: %s' % b)
    if a > p:
        a %= p
    return powModP(a,b)

def public_key(private_key):
    return _powmodp(g,private_key)

def private_key():
    while True:
        v = random.randint(0x0000000000000001,0xffffffffffffffff)
        return v

def secret(private_key, anotherPublicKey):
    return _powmodp(anotherPublicKey, private_key)