### 新建连接

Client->Server: 传输一个 2 byte size(big-endian) + content 的包, size == len(content)

包的内容如下:
    ```
    0\n
    base64(DHPublicKey)\n
    ```
将Client的DHPublicKey字符串使用base64格式解密成 8 bytes 值, 经过 DH 算法计算出来的 key。 
    ```
    DHPrivateKey = dh64.PrivateKey()
    DHPublicKey = dh64.PublicKey(DHPrivateKey)
    ```


Server->Client: 回应给 Client 一个握手信息:
    ```
    id\n
    base64(DHPublicKey)
    ```
id为Server端生成的唯一id,标识这个Conn连接
DHPublicKey 的算法与Client 的算法一致，将DHPublicKey bytes通过base64格式加密成字符串发送



握手完毕后, 双方获得一个公有的 64bit secret,  计算方法为:
    ```
    secret = dh64.Secret(myDHPrivateKey, otherDHPublicKey)
    ```

将secret与 8bytes 的0混合成48bytes的w，取长度固定为16 bytes的MD5摘要值，前后8 bytes进行异或运算，得到key的[:8]前8字节，后续secret与 8bytes 的1/2/3进行同样的操作，key作为32 bytes


### 数据加解密
Client和Server 通信的协议数据包收发都使用rc4加密， rc4的秘钥都是key

Client <->  Goson：协议请求数据包需要rc4加解密
Goscon <-> Server: 数据包直接发送，不需要加解密


### 数据读取
read之前先获取socket连接conn：
    socket已经处于close状态，返回None
    socket处于连接状态，返回该连接conn
    socket处于出错状态，则启动超时计数，close关闭该连接




### 恢复连接

Client->Server: 传输一个 2 byte size(big-endian) + content 的包, size == len(content)

包的内容如下:

```
id\n
handshakes\n
recvnumber\n
base64(HMAC_CODE)
```

这里 id 为新建连接时, 服务器交给 Client 的 id .

handshakes 是一个从 1 开始(第一次恢复为 1), 递增的十进制数字. 服务器会拒绝重复使用过的数字.

recvnumber 是一个 10 进制数字, 表示 (曾经从服务器收到多少字节 mod 2^32).

把以上三行放在一起(保留 \n) content, 以及在新建连接时交换得到的 serect, 计算一个 HMAC_CODE, 算法是:

HMAC_CODE = crypt.hmac64(crypt.hashkey(content), secret)

Server->Client: 回应握手消息:

```
recvnumber\n
CODE msg
```

这里, recvnumber 是一个 10 进制数字, 表示 (曾经在这个会话上, 服务器收到过客户端发出的多少字节 mod 2^32).
CODE 是一个10进制三位数, 表示连接是否恢复:

* 200 OK : 表示连接成功
* 401 Unauthorized : 表示 HMAC 计算错误
* 403 Index Expired : 表示 Index 已经使用过
* 404 User Not Found : 表示连接 id 已经无效
* 406 Not Acceptable : 表示 cache 的数据流不够

当连接恢复后, 服务器应当根据之前记录的发送出去的字节数（不计算每次握手包的字节）, 减去客户端通知它收到的字节数, 开始补发未收到的字节。
客户端也做相同的事情。


keepalive_interval：客户端异常关闭后，指定时间没回心跳包，则抛出异常
read_timeout：读IO阻塞超时时间
reuse_time：当客户端到中间层的连接关闭后，指定时间后中间层到服务器的连接也关闭