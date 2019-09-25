class Sampling:
    def __init__(self):
        self._mediaMap = dict()          # 存储media，以及其对象

    def count(self, media):
        """
        :param media: 经过抓取得到的用户访问的媒介
        :return:
        """
        keys = self._mediaMap.keys()
        if media in keys:
            value = self._mediaMap.get(media)
            self._mediaMap[media] = value + 1
        else:
            self._mediaMap[media] = 1
        pass

    def toString(self):
        keys = list(self._mediaMap.keys())
        values = list(self._mediaMap.values())
        msg = str()
        # 需要对values进行排序
        for i in range(len(values)):
            for j in range(i,len(values)-1):
                if values[j]<values[j+1]:
                    values[j] = values[j] + values[j+1]
                    values[j+1] = values[j] - values[j+1]
                    values[j] = values[j] - values[j+1]
                    temp = keys[j]
                    keys[j] = keys[j+1]
                    keys[j+1] = temp
        for k in range(len(keys)):
            msg = msg + "CONTENT:"
            msg = msg + keys[k] + ":" + str(values[k]) + ","

        msg = msg + "\r\n" + "STATE:OVER"
        self._clear()
        return [msg, keys]

    def _clear(self):
        self._mediaMap.clear()
        pass