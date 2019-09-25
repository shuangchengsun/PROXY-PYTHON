# coding:utf-8
from baseproxy.Interceptor import DebugInterceptor, CacheInterceptor, NoneInterceptor, ImageInterceptor
from baseproxy.Sampling import Sampling
from baseproxy.proxy import AsyncMitmProxy
from threading import Timer


if __name__ == "__main__":
    baseproxy = AsyncMitmProxy(Sampling=Sampling(), https=True)
    baseproxy.register(CacheInterceptor)
    baseproxy.serve_forever()
