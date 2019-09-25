import zlib

import chardet

from http.client import HTTPResponse

class HttpTransfer(object):
    version_dict = {9: 'HTTP/0.9', 10: 'HTTP/1.0', 11: 'HTTP/1.1'}

    def __init__(self):
        self.hostname = None
        self.port = None

        #这是请求
        self.command = None
        self.path = None
        self.request_version = None

        #这是响应
        self.response_version = None
        self.status = None
        self.reason = None

        self._headers = None

        self._body = b''

    def parse_headers(self,headers_str):
        '''
        暂时用不到
        :param headers:
        :return:
        '''
        header_list = headers_str.rstrip("\r\n").split("\r\n")
        headers = {}
        for header in header_list:
            [key,value] = header.split(": ")
            headers[key.lower()] = value
        return headers

    def to_data(self):
        raise NotImplementedError("function to_data need override")


    def set_headers(self,headers):
        headers_tmp={}
        for k,v in headers.items():
            headers_tmp[k.lower()]= v
        self._headers = headers_tmp


    def build_headers(self):
        '''
        返回headers字符串
        :return:
        '''
        header_str = ""
        for k, v in self._headers.items():
            header_str += k + ': ' + v + '\r\n'

        return header_str

    def get_header(self, key):
        if isinstance(key, str):
            return self._headers.get(key.lower(), None)
        raise Exception("parameter should be str")

    def get_headers(self):
        '''
        获取头部信息
        :return:
        '''
        return self._headers

    def set_header(self,key,value):
        '''
        设置头部
        :param key:
        :param value:
        :return:
        '''
        if isinstance(key,str) and isinstance(value,str):
            self._headers[key.lower()] = value
            return
        raise Exception("parameter should be str")

    def get_body_data(self):
        '''
        返回是字节格式的body内容
        :return:
        '''
        return self._body


    def set_body_data(self,body):
        if isinstance(body, bytes):
            self._body = body
            self.set_header("Content-length",str(len(body)))
            return
        raise Exception("parameter should be bytes")



class Request(HttpTransfer):

    def __init__(self, req):
        HttpTransfer.__init__(self)

        self.hostname = req.hostname
        self.port = req.port
        # 这是请求
        self.command = req.command
        self.path = req.path
        self.request_version = req.request_version

        self.set_headers(req.headers)

        if self.get_header('Content-Length'):
            self.set_body_data(req.rfile.read(int(self.get_header('Content-Length'))))


    def to_data(self):
        # Build request
        req_data = '%s %s %s\r\n' % (self.command, self.path, self.request_version)
        # Add headers to the request
        req_data += '%s\r\n' % self.build_headers()
        req_data = req_data.encode("utf-8")
        req_data += self.get_body_data()
        return req_data


class Response(HttpTransfer):

    def __init__(self, request, proxy_socket):

        HttpTransfer.__init__(self)

        self.request = request

        h = HTTPResponse(proxy_socket)
        h.begin()
        ##HTTPResponse会将所有chunk拼接到一起，因此会直接得到所有内容，所以不能有Transfer-Encoding
        del h.msg['Transfer-Encoding']
        del h.msg['Content-Length']

        self.response_version =self.version_dict[h.version]
        self.status = h.status
        self.reason = h.reason
        self.set_headers(h.msg)

        body_data = self._decode_content_body(h.read(),self.get_header('Content-Encoding'))
        self.set_body_data(body_data)
        self._text()#尝试将文本进行解码

        h.close()
        proxy_socket.close()

    def _text(self):

        body_data=self.get_body_data()
        if self.get_header('Content-Type') and ('text' or 'javascript') in self.get_header('Content-Type'):
            self.decoding = chardet.detect(body_data)['encoding']  # 探测当前的编码
            if self.decoding:
                try:
                    self._body_str = body_data.decode(self.decoding)  # 请求体
                except Exception as e:
                    self._body_str = body_data
                    self.decoding = None
            else:
                self._body_str = body_data
        else:
            self._body_str = body_data
            self.decoding = None


    def get_body_str(self,decoding=None):
        if decoding:
            try:
                return self.get_body_data().decode(decoding)
            except Exception as e:
                return None

        if isinstance(self._body_str,bytes):
            return None
        return self._body_str


    def set_body_str(self,body_str,encoding=None):
        if isinstance(body_str,str):
            if encoding:
                self.set_body_data(body_str.encode(encoding))
            else:
                self.set_body_data(body_str.encode(self.decoding if self.decoding else 'utf-8'))
            self._body_str = body_str
            return
        raise Exception("parameter should be str")





    def _encode_content_body(self,text, encoding):

        if encoding == 'identity':
            data = text
        elif encoding in ('gzip', 'x-gzip'):

            gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
            data = gzip_compress.compress(text) + gzip_compress.flush()

        elif encoding == 'deflate':
            data = zlib.compress(text)
        else:
            data = text

        return data

    def _decode_content_body(self, data, encoding):
        if encoding == 'identity':#没有压缩
            text = data

        elif encoding in ('gzip', 'x-gzip'):#gzip压缩
            text = zlib.decompress(data, 16+zlib.MAX_WBITS)
        elif encoding == 'deflate':#zip压缩
            try:
                text = zlib.decompress(data)
            except zlib.error:
                text = zlib.decompress(data, -zlib.MAX_WBITS)
        else:
            text = data

        self.set_header('Content-Encoding','identity')#没有压缩
        return text

    def to_data(self):
        res_data = '%s %s %s\r\n' % (self.response_version, self.status, self.reason)
        res_data += '%s\r\n' % self.build_headers()
        res_data = res_data.encode(self.decoding if self.decoding else 'utf-8')
        res_data += self.get_body_data()
        return res_data