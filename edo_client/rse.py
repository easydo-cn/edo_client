# -*- coding: utf-8 -*-

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from base64 import b64decode
import logging
from functools import wraps

_logger = logging.getLogger(__name__)


class ScriptDownloadError(Exception):
    ''' 无法从系统下载脚本'''

    def __init__(self, script_name, err):
        self.script_name = script_name
        self.error = err

    def __repr__(self):
        return (
            u'<ScriptDownloadError: '
            u'script "{}" failed to download, see .error attribute>'
            u'error: {}'
        ).format(self.script_name, self.error)

    __str__ = __repr__


class ScriptSecurityError(Exception):
    '''脚本未能通过安全检查'''
    def __init__(self, script_name):
        self.script_name = script_name

    def __repr__(self):
        return (
            u'<ScriptSecurityError: '
            u'"{}" has been blocked from running because it\'s not signed.>'
        ).format(self.script_name)

    __str__ = __repr__


def retry(on_exception=Exception, max_retries=5, logger=None):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            cnt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except on_exception:
                    if cnt >= max_retries:
                        raise
                    cnt += 1
                    
                    if logger:
                        logger.warning('函数%s调用发生异常%s，将进行第%d次重试。' % (func.__name__, on_exception, cnt))
        
        return wrapped
    return wrapper


class RemoteScriptExecuteEngine:
    def __init__(self, wo_client, exec_environ=None, verify=True):
        self._wo_client = wo_client
        self.script_exec_env = exec_environ or {}
        self.script_exec_env.update({
            'call_script': self.call
        })
        self.verify = verify
        self.script_cache = {}

    def call(self, script_name, *args, **kwargs):
        if kwargs.get('package_versions_', None):
            package_versions = kwargs['package_versions_']
        elif kwargs.get('params', None):
            package_versions = kwargs['params']['package_versions_']
        else:
            package_versions = {script_name.split(":")[0]: '1.0.0'}
        version = package_versions[script_name.split(':')[0]]
        script_obj = self.load_script(script_name, version)

        if self.verify and not self._validate_edo_signature(script_obj):
            raise ScriptSecurityError(script_name)


        func_name = script_obj['name']
        # 为脚本拼装函数源代码
        source = self._make_function(
            func_name, script_obj['script'], script_obj['args']
        )
        # 生成函数定义
        code = compile(source, '<script>', 'exec')
        # 运行（调用函数）
        exec code in self.script_exec_env

        return self.script_exec_env[func_name](*args, **kwargs)

    @retry(ScriptDownloadError, 5, logger=_logger)
    def load_script(self, script_name, version=None):
        if script_name not in self.script_cache or version != self.script_cache[script_name][0]:
            # 下载脚本
            try:
                script_obj = self._wo_client.content.download_shell_script(script_name)
                # 下载的脚本使用内存来做临时缓存，在多次调用时，不需要多次下载。
                self.script_cache[script_name] = (version, script_obj)
            except Exception as e:
                raise ScriptDownloadError(script_name, e)
                
        # 使用缓存脚本
        return  self.script_cache[script_name][1]


    @staticmethod
    def _validate_edo_signature(script_obj):
        '''
        检查给定脚本是否允许运行
        判断条件：
        - 脚本带有易度下发的签名；
        '''
        # Issued on 2017.10.13 from zopen.beta.easydo.cn/default
        PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEArgsR+t6+G0HDHrI0tdLO
u4mjumP+SW+MQhKfmRlQ5VEW7LWj3YooEAjjOHHSETzYaRJQhuUzeVxIZMfqQ906
ZyeoyoIf6/PCRAv9ETIe2mopchfwHzAFgScMBki1iVrqQTuQO6CQIrdXa1NRR7pU
OKHDOmuqgRV9gd0Tv5UesXXlNEv9W0kag1sIvmpNdFOEPN7Ic57DFExh/2htCIFZ
OzPyGQ2Pj7KYWVNlP5BMb6tFWrStbKBBowrfv7rJ409JvtomwW/r1ES0Az4lx5Ll
A6VQMp/fovk2OVBt2TSgJfsxW5fb6l8COY+q7ngzJFDcrxdlow20UFaGIPJmx0c5
6pjpezwY+cR+/BQhRF3B08IvYWZOIQlWgct6GtgSis01sc8M54UUn3hdLUsqJUni
9i1cgg227ABh3SCUK6WLdzfvRAnf2JIABFvVsPTxatk/r3574UrrPMtRT/s/gpVH
MlwSzllOfw7ytdMvdpDTnvRKkwxG+7WCHSuUAKkI0Kl6VZAR/6SODuNhhhR00mCi
pzzXrIZbtNJO5D7c4aTXpA8kjWON27F5QG8ngoLhl956+7AcPcv8pORY2Qjd5SEa
oav6kXwROIgqy4+Vjwu7kThrSQ5UbAoZWZl0ER8UdNhayetXcoMO7ydLdOU6psa9
+JHqu3yg5zdUKtu0B4igyo0CAwEAAQ==
-----END PUBLIC KEY-----
'''
        
        # 检查易度签名
        edo_signature = script_obj.get('edo_signature', None)
        script_content = script_obj['script']

        if edo_signature:
            text = script_content.strip()
            if isinstance(text, unicode):
                text = text.encode('utf-8')

            try:
                key = RSA.importKey(PUBLIC_KEY)
                _hash = SHA256.new(text)
                pkcs = PKCS1_v1_5.new(key)
                return pkcs.verify(_hash, b64decode(edo_signature))
                 
            except Exception:
                _logger.exception(u'unexpected exception.')

        return False


    @staticmethod
    def _make_function(func_name, script, variables=None):
        if variables:
            args = u'{}, **kw'.format(variables)
        else:
            args = u'**kw'
        lines = []
        in_multi_line_str = False
        for line in script.splitlines():
            if in_multi_line_str:
                lines.append(line)
            else:
                lines.append('    ' + line)
            if len(line.split("'''")) == 2 or len(line.split('"""')) == 2:
                in_multi_line_str = not in_multi_line_str
        return u'def {}({}):\n{}'.format(func_name, args, '\n'.join(lines))




