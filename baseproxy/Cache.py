class Cache:
    def __init__(self):
        self._mediaList = list()  # 存储着需要缓存的内容，content name
        self._fileList = list()  # 已经缓存的内容
        self._content = dict()  # 缓存映射,如果文件直接缓存在内存中，那么如何
        self._contentSize = dict()  # 描述文件大小。
        self._defaultPath = "../static/cache/"
        file = open(self._defaultPath + "5.mp4", "rb")
        self._msg = file.read()
        self._flag = 0

    def cache(self, media, content):
        """
        :param media: 是缓存内容的名称，string
        :param content: 内容，byte[]格式，以二进制方式存储，可能产生的问题，一个response没有存完，下一个response会接着存，如何避免这个问题
        :return:
        """
        # 第一个BUG，涉及到文件的拼接，即文件很可能不是一次性就发送完成了，因此如何保证文件第二次到达的时候也能进行缓存。
        # 其次，如何将文件直接缓存在内存中呢？ 文件预计大小500MBd
        # if media in self._mediaList and media not in self._fileList:
        if True:
            file = open(self._defaultPath + media, "wb")
            file.write(content)
            self._fileList.append(media)
        pass

    def read(self, media):
        # 考虑到需要可能需要多次发送，所以，此处直接返回文件描述符。毕竟一个视频不会完全存在内存中（可以试一下）
        file = open(self._defaultPath + media, "rb")
        size = 1024*1024*10             # 10MB的buff
        data = file.read(size)
        data = self._msg
        # 当读取得到的数据长度小于规定的长度的时候，标志着已经读取完毕。
        return [data, len(data), len(data) < size]

    def isCached(self, media):
        # return media in self._fileList
        return media == "5.mp4"
    def needCached(self, media):
        """
        :param media:需要缓存的内容名称
        :return: True or False
        """
        if media is not None and media in self._mediaList:
            # 在需要缓存的列表中
            if media in self._fileList:
                # 在已经缓存的目录中，则不需要再缓存
                return False
            else:
                return True
        else:
            return False
        pass

    def _fileWrite(self, writeInDisk=True):
        """
        :param writeInDisk:是否缓存在硬盘中，
        :return: 是否已经缓存完成
        """
        pass

    def Parse(self, data):
        """
        :param data:从服务器得到的缓存指令
        :return:
        """

        pass
