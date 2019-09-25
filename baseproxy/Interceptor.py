
from baseproxy.Parse import URLParse
from baseproxy.proxy import ReqIntercept, RspIntercept


class DebugInterceptor(ReqIntercept, RspIntercept):
    def deal_request(self, request, Sampling):
        print(request.path)
        return request

    def deal_response(self, response, request, Cache):
        if response.get_header("Content-Type") and 'image' in response.get_header("Content-Type"):
            response = None

        return response


# 处理缓存，以及手机url中的media。
class CacheInterceptor(ReqIntercept, RspIntercept):
    def deal_request(self, request, Sampling):
        # 此处为了加快速度应该开一个线程去处理
        # URL = request.path  # 获取用户发起的请求，
        # media = URLParse(URL)
        # Sampling.count(media=media)
        # print(URL)
        return request

    def deal_response(self, response, request, Cache):
        # 在此处将会判断内容，并开始准备缓存
        URL = request.path  # 获取用户发起的请求，
        media = URLParse(URL)
        print(response.get_headers())
        if response.get_header("Content-Type") and "application/octet-stream" in response.get_header("Content-Type") \
                and media is not None:
            # 此处的判断逻辑是 有Content-Type这个选项，其次数据是二进制流式数据。
            Cache.cache(media, response.get_body_data())
        else:
            # print(response.get_headers())
            # print(response.get_body_str())
            pass
        return response


class NoneInterceptor(ReqIntercept, RspIntercept):
    def deal_request(self, request, Sampling):
        print("request ", request.get_headers())
        return request

    def deal_response(self, response, request, Cache):
        print("response ", response.get_headers())
        return response


class ImageInterceptor(RspIntercept):
    def deal_response(self, response, request, Cache):
        URL = request.path  # 获取用户发起的请求，
        media = URLParse(URL)
        print(media)
        if response.get_header("Content-Type") and "image" in response.get_header("Content-Type") and media is not None:
            print("debug test the response type is image ")
            Cache.cache(media, response.get_body_data())
        else:
            print(response.get_headers())
            print(response.get_body_str())
            # 此处可以将图片换成自己的图片，更进一步，可以将别人的收款二维码换成自己的。。
        # if response.get_header("Content-Type") and 'image' in response.get_header("Content-Type"):
        #     with open("../img/qiye2.jpg", 'rb') as f:
        #         response.set_body_data(f.read())
        print("method finished")
        return response
