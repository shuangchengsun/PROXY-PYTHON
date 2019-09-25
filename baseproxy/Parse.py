
# 该函数用来解析用户的URL，此外还需要一个生命周期贯穿整个过程的全局变量，或者说，解析一个发送一个

def URLParse(url):
    '''
    :param url:传入的URL，形如/index.html、xxx.mp4?*****
    :return:
    '''
    splitOnce = url.split("?")[0]               # 丢弃URL中带的参数
    splitTwice = splitOnce.split("/")[-1]       # 丢弃URL中的目录信息
    # 一般而言，经过以上操作之后，剩下的都是media，但是也需要验证是否是我们需要的media
    splitThree = splitTwice.split(".")          # 用点做划分，
    if len(splitThree) == 1:                  # 长度为1 显然没有后缀，不是media
        return None
    else:
        if splitThree[1] == "mp4" or splitThree[1] == "mkv" or splitThree[1] == "3gp":      # 后缀为视频类型
            return splitThree[0]+"."+splitThree[1]
        elif splitThree[1] == "js":
            return splitThree[0]+"."+splitThree[1]
        elif splitThree[1] == "png" or splitThree[1] == "jpg":
            return splitThree[0] + "." + splitThree[1]
        else:
            return None
    pass
