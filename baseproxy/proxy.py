# coding:utf-8

import logging
import select

from baseproxy import Parse
from baseproxy.Cache import Cache
from baseproxy.Certificate import *
from baseproxy.HTTP import *
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, ParseResult, urlunparse
from ssl import wrap_socket
from socket import socket

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


# 代理所有数据的处理class
class ProxyHandle(BaseHTTPRequestHandler):
    def __init__(self, request, client_addr, server):
        self.is_connected = False
        BaseHTTPRequestHandler.__init__(self, request, client_addr, server)

    def do_CONNECT(self):
        '''
        处理https连接请求
        :return:
        '''

        self.is_connected = True  # 用来标识是否之前经历过CONNECT
        if self.server.https:
            self.connect_intercept()
        else:
            self.connect_relay()

    def do_GET(self):
        '''
        处理GET请求
        :return:
        '''
        if self.path == 'http://baseproxy.ca/':
            self._send_ca()
            return

        # 判定是不是https。
        if not self.is_connected:
            # 如果不是https，需要连接http服务器
            try:
                self._proxy_to_dst()
            except Exception as e:
                self.send_error(500, '{} connect fail '.format(self.hostname))
                return
        # 这里就是代理发送请求，并接收响应信息
        request = Request(self)
        request = self.mitm_request(request, self.server.sampling)
        if request:
            URL = request.path
            media = Parse.URLParse(URL)

            if media is not None and self.server.cache.isCached(media):
                # 此处还有一个问题：在分段存储的时候，如何确保分段存储时候能够有效的发送和接收。即在分段存储的情况下，需要多次调用此处的函数
                [msg, length, isFinish] = self.server.cache.read(media)
                while not isFinish:  # 循环直到文件顺利的完全读完
                    response = "HTTP/1.1 200 OK\r\n " \
                               "Content-Encoding: Identity\r\n" \
                               "Content-type: application/octet-stream\r\n" \
                               "Connection: Keep-Alive\r\n" \
                               "Content-Length: " + str(length) + "\r\n"
                    response = response + "Content-Disposition: attachment;filename=" + media + "\r\n\r\n"
                    # 此处构造了响应头，但是需要格外注意的是，从文件中读出来的数据是二进制数据，因此，不能直接拼接，要么全转二进制，要么都用字符串9-22
                    response = response.encode("utf-8") + msg
                    if response:
                        self.request.sendall(response)
                    else:
                        self.send_error(404, 'response is None')
                    [msg, length, isFinish] = self.server.cache.read(media)
                # 在最后读取之后，如果有数据，可能还未发送，因此需要将最后的部分发送出去
                if length != 0:
                    response = "HTTP/1.1 200 OK\r\n " \
                               "Content-Encoding: Identity\r\n" \
                               "Content-type: application/octet-stream\r\n" \
                               "Connection: Close\r\n" \
                               "Content-Length: " + str(length) + "\r\n"
                    response = response + "Content-Disposition: attachment;filename=" + media + "\r\n\r\n"
                    # 此处构造了响应头，但是需要格外注意的是，从文件中读出来的数据是二进制数据，因此，不能直接拼接，要么全转二进制，要么都用字符串9-22
                    response = response.encode("utf-8") + msg
                    if response:
                        self.request.sendall(response)
                    else:
                        self.send_error(404, 'response is None')
                # 发送完毕后，缓存命中的部分完结
            else:
                # 没有缓存的步骤
                self._proxy_sock.sendall(request.to_data())  # proxy发送数据到服务器
                # 将响应信息返回给客户端。
                response = Response(request, self._proxy_sock)  # 此处从浏览器获取消息
                response = self.mitm_response(response, request, self.server.cache,
                                              self.server.sampling)  # 为了得到对应的请求名称，需要这一步

                if response:
                    self.request.sendall(response.to_data())
                else:
                    self.send_error(404, 'response is None')
        else:
            self.send_error(404, 'request is None')

    do_HEAD = do_GET
    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET
    do_OPTIONS = do_GET

    def _proxy_to_ssldst(self):
        '''
        代理连接https目标服务器
        :return:
        '''
        ##确定一下目标的服务器的地址与端口

        # 如果之前经历过connect
        # CONNECT www.baidu.com:443 HTTP 1.1
        self.hostname, self.port = self.path.split(':')
        self._proxy_sock = socket()
        self._proxy_sock.settimeout(10)
        self._proxy_sock.connect((self.hostname, int(self.port)))
        # 进行SSL包裹
        self._proxy_sock = wrap_socket(self._proxy_sock)

    def _proxy_to_dst(self):
        # 代理连接http目标服务器
        # http请求的self.path 类似http://www.baidu.com:80/index.html
        u = urlparse(self.path)
        if u.scheme != 'http':
            raise Exception('Unknown scheme %s' % repr(u.scheme))
        self.hostname = u.hostname
        self.port = u.port or 80
        # 将path重新封装，比如http://www.baidu.com:80/index.html会变成 /index.html
        self.path = urlunparse(
            ParseResult(scheme='', netloc='', params=u.params, path=u.path or '/', query=u.query, fragment=u.fragment))
        self._proxy_sock = socket()
        self._proxy_sock.settimeout(10)
        self._proxy_sock.connect((self.hostname, int(self.port)))

    def connect_intercept(self):
        '''
        需要解析https报文,包装socket
        :return:
        '''
        try:
            # 首先建立和目标服务器的链接
            self._proxy_to_ssldst()
            # 建立成功后,proxy需要给client回复建立成功
            self.send_response(200, "Connection established")
            self.end_headers()

            # 这个时候需要将客户端的socket包装成sslsocket,这个时候的self.path类似www.baidu.com:443，根据域名使用相应的证书
            self.request = wrap_socket(self.request, server_side=True, certfile=self.server.ca[self.path.split(':')[0]])

        except Exception as e:
            self.send_error(500, str(e))
            return

        self.setup()
        self.ssl_host = 'https://%s' % self.path
        self.handle_one_request()

    def connect_relay(self):
        '''
        对于https报文直接转发
        '''

        self.hostname, self.port = self.path.split(':')
        try:
            self._proxy_sock = socket()
            self._proxy_sock.settimeout(10)
            self._proxy_sock.connect((self.hostname, int(self.port)))
        except Exception as e:
            self.send_error(500)
            return

        self.send_response(200, 'Connection Established')
        self.end_headers()

        inputs = [self.request, self._proxy_sock]

        while True:
            readable, writeable, errs = select.select(inputs, [], inputs, 10)
            if errs:
                break
            for r in readable:
                data = r.recv(8092)
                if data:
                    if r is self.request:
                        self._proxy_sock.sendall(data)
                    elif r is self._proxy_sock:
                        self.request.sendall(data)
                else:
                    break
        self.request.close()
        self._proxy_sock.close()

    def _send_ca(self):
        # 发送CA证书给用户进行安装并信任
        cert_path = self.server.ca.cert_file_path
        with open(cert_path, 'rb') as f:
            data = f.read()

        self.send_response(200)
        self.send_header('Content-Type', 'application/x-x509-ca-cert')
        self.send_header('Content-Length', len(data))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(data)

    def mitm_request(self, req, Sampling):
        for p in self.server.req_plugs:
            req = p(self.server).deal_request(req, Sampling)
        return req

    def mitm_response(self, rsp, req, Cache, Sampling):
        """
        :param rsp:响应头
        :param req: 请求头
        :param Sampling: 采样类
        :return:
        """
        # 此处是经过经过插件拦截返回的数据，但是有一个问题，并不能将其和浏览器发送的请求结合在一起
        for p in self.server.rsp_plugs:
            rsp = p(self.server).deal_response(rsp, req, Cache)

        return rsp


# 默认情况下，是工作在正常的代理模式下
class MitmProxy(HTTPServer):
    def __init__(self, Sampling, server_addr=('', 8044), RequestHandlerClass=ProxyHandle, bind_and_activate=True,
                 https=False):
        # 开启了一个server去处理
        HTTPServer.__init__(self, server_addr, RequestHandlerClass, bind_and_activate)
        logging.info('HTTPServer is running at address( %s , %d )......' % (server_addr[0], server_addr[1]))
        self.req_plugs = []  # 请求拦截插件列表
        self.rsp_plugs = []  # 响应拦截插件列表
        self.ca = CAAuth(ca_file="ca.pem", cert_file='ca.crt')
        self.https = https
        self.sampling = Sampling
        self.cache = Cache()

    def register(self, intercept_plug):
        if not issubclass(intercept_plug, InterceptPlug):
            raise Exception('Expected type InterceptPlug got %s instead' % type(intercept_plug))

        if issubclass(intercept_plug, ReqIntercept):
            self.req_plugs.append(intercept_plug)

        if issubclass(intercept_plug, RspIntercept):
            self.rsp_plugs.append(intercept_plug)


class AsyncMitmProxy(ThreadingMixIn, MitmProxy):
    pass


class InterceptPlug(object):

    def __init__(self, server):
        self.server = server


class ReqIntercept(InterceptPlug):
    def deal_request(self, request, Sampling):
        pass


class RspIntercept(InterceptPlug):
    def deal_response(self, response, request, Cache):
        pass
