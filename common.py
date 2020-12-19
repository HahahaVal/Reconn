NetBufferSize = 32*1024

LoopBuffSize = 64*1024

ErrCode = {
    'SCPStatusOK'             : 200,  #表示连接成功
    'SCPStatusUnauthorized'   : 401,  #表示 HMAC 计算错误
    'SCPStatusExpired'        : 403,  #表示 Index 已经使用过
    'SCPStatusIDNotFoun'      : 404,  #表示连接 id 已经无效
    'SCPStatusNotAcceptable'  : 406,  #表示 cache 的数据流不够
}
