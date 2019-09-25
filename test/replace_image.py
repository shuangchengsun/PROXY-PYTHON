#coding:utf-8
from baseproxy.Interceptor import ImageInterceptor

__author__ = 'qiye'
__date__ = '2018/6/22 22:55'

from baseproxy.proxy import RspIntercept, AsyncMitmProxy






if __name__ == "__main__":
    baseproxy = AsyncMitmProxy(https=True)
    baseproxy.register(ImageInterceptor)
    baseproxy.serve_forever()
    pass