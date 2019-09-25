import socket


class net:
    def __init__(self, Sampling, Cache, serverAddr=None):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sampling = Sampling
        self._mediaList = None
        self._isReady = True
        self._cache = Cache
        if serverAddr is None:
            self._defaultAddr = "localhost"
        else:
            self._defaultAddr = serverAddr

    def _sendSampling(self, Sampling):
        [msg, self._mediaList] = Sampling.toString()
        msg = "bsID:1001\r\n" + msg
        self._socket.sendall(msg.encode("utf-8"))
        pass

    def run(self, Sampling):
        # 此处应该是整个和MEC Center节点交互的线程的入口函数
        # 1、socket不应该中断，应当一直处于连接状态，
        self._socket.connect((self._defaultAddr, 6233))
        while True:
            # 死循环进行监听是否有消息到来,是否需要死循环存疑。
            if self._isReady:
                self._sendSampling(self._sampling)
            data = self._socket.recv(4096)
            # 此处已经收到了data，需要将其解析出来。
            self._cache.Parse(data)
        pass
