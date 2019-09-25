import os
from tempfile import gettempdir
import time

from OpenSSL.crypto import PKey, TYPE_RSA, X509, X509Extension, dump_privatekey, FILETYPE_PEM, dump_certificate, \
    load_certificate, load_privatekey, X509Req


class CAAuth(object):
    '''
    用于CA证书的生成以及代理证书的自签名

    '''
    def __init__(self,ca_file = "ca.pem", cert_file = 'ca.crt'):
        self.ca_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),ca_file)
        self.cert_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cert_file)
        self._gen_ca()#生成CA证书，需要添加到浏览器的合法证书机构中

    def _gen_ca(self, again=False):
        # Generate key
        #如果证书存在而且不是强制生成，直接返回证书信息
        if os.path.exists(self.ca_file_path) and os.path.exists(self.cert_file_path) and not again:
            # self._read_ca(self.ca_file_path) #读取证书信息
            self._read_ca(self.ca_file_path)  # 读取证书信息
            return
        self.key = PKey()
        self.key.generate_key(TYPE_RSA, 2048)       # 生成了一个密钥对
        # Generate certificate
        self.cert = X509()
        self.cert.set_version(2)
        self.cert.set_serial_number(1)
        self.cert.get_subject().CN = 'baseproxy'
        self.cert.gmtime_adj_notBefore(0)
        self.cert.gmtime_adj_notAfter(315360000)
        self.cert.set_issuer(self.cert.get_subject())
        self.cert.set_pubkey(self.key)
        self.cert.add_extensions([
            X509Extension(b"basicConstraints", True, b"CA:TRUE, pathlen:0"),
            X509Extension(b"keyUsage", True, b"keyCertSign, cRLSign"),
            X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=self.cert),
        ])
        self.cert.sign(self.key, "sha256")
        with open(self.ca_file_path, 'wb+') as f:
            f.write(dump_privatekey(FILETYPE_PEM, self.key))
            f.write(dump_certificate(FILETYPE_PEM, self.cert))

        with open(self.cert_file_path, 'wb+') as f:
            f.write(dump_certificate(FILETYPE_PEM, self.cert))

    def _read_ca(self, file):
        self.cert = load_certificate(FILETYPE_PEM, open(file,'rb').read())
        self.key = load_privatekey(FILETYPE_PEM, open(file,'rb').read())

    def __getitem__(self, cn):
        #将为每个域名生成的服务器证书，放到临时目录中
        cache_dir  =gettempdir()
        root_dir = os.path.join(cache_dir,'baseproxy')
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)

        cnp = os.path.join(root_dir,"baseproxy_{}.pem".format(cn))

        if not os.path.exists(cnp):
            self._sign_ca(cn,cnp)
        return cnp


    def _sign_ca(self,cn,cnp):
        #使用合法的CA证书为代理程序生成服务器证书
        # create certificate
        try:

            key = PKey()
            key.generate_key(TYPE_RSA, 2048)

            # Generate CSR
            req = X509Req()
            req.get_subject().CN = cn
            req.set_pubkey(key)
            req.sign(key, 'sha256')

            # Sign CSR
            cert = X509()
            cert.set_version(2)
            cert.set_subject(req.get_subject())
            cert.set_serial_number(self.serial)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(31536000)
            cert.set_issuer(self.cert.get_subject())
            ss = ("DNS:%s" % cn).encode(encoding="utf-8")

            cert.add_extensions(
                [X509Extension(b"subjectAltName", False, ss)])

            cert.set_pubkey(req.get_pubkey())
            cert.sign(self.key, 'sha256')

            with open(cnp, 'wb+') as f:
                f.write(dump_privatekey(FILETYPE_PEM, key))
                f.write(dump_certificate(FILETYPE_PEM, cert))
        except Exception as e:
            raise Exception("generate CA fail:{}".format(str(e)))


    @property
    def serial(self):
        return int("%d" % (time.time() * 1000))
