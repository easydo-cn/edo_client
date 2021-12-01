# -*- coding: utf-8 -*-
import logging
import os
from hashlib import md5
import time
import pyoauth2
import requests
from error import ApiError
from edo_client.api import (
    OcAPI, WoAPI, ViewerAPI, OrgAPI, OperatorAPI, MessageAPI, UploadAPI, HcAPI)

vendor = os.environ.get('EDO_VENDOR', 'test')
log = logging.getLogger(__name__)


# patch for pyoauth2
# pyoauth2 cause memory error when upload large file in hc and assistant
def _pyoauth2_libs_response_response_init(self, response, **opts):
    '''Monkey patch pyoauth2 Response encoding'''
    self.response = self.resp = response
    self.status_code = self.status = response.status_code
    self.reason = response.reason
    self.content_type = response.headers.get('content-type')

    options = {'parse': 'text'}
    options.update(opts)
    if options['parse'] in ('text', 'query', 'json', ):
        self.body = response.text
    self.options = options


def _pyoauth2_libs_oauthtoken_refresh(self, **opts):
    if not getattr(self, 'refresh_token', None):
        raise Exception('A refresh_token is not available')

    _opts = {
        'client_id': self.client.id,
        'client_secret': self.client.secret,
        'refresh_token': self.refresh_token,
        'grant_type': 'refresh_token',
    }
    _opts.update(opts)
    return self.client.get_token(**_opts)


# patch
pyoauth2.libs.response.Response.__init__ = _pyoauth2_libs_response_response_init
pyoauth2.libs.access_token.AccessToken.refresh = _pyoauth2_libs_oauthtoken_refresh

from pyoauth2.libs.response import Response  #noqa


# 针对使用post方式上传大文件的修补
def request(self, data=None):
    params = None
    if not data:
        if self.method in ('POST', 'PUT', ):
            data = self.opts
        else:
            params = self.opts
            data = self.opts.pop('data', None)
        response = requests.request(
            self.method, self.uri,
            params=params,
            data=data,
            headers=self.headers,
            files=self.files,
            timeout=self.timeout,
            allow_redirects=self.allow_redirects,
            proxies=self.proxies,
            hooks=self.hooks,
            stream=self.stream,
            verify=self.verify,
            cert=self.cert)
    # 针对使用post方式上传大文件的修补
    else:
        params = self.opts
        response = requests.post(
            self.uri,
            data=data,
            params=params,
            headers=self.headers,
            files=self.files,
            timeout=self.timeout,
            allow_redirects=self.allow_redirects,
            proxies=self.proxies,
            hooks=self.hooks,
            stream=self.stream,
            verify=self.verify,
            cert=self.cert)
    return Response(response, parse=self.parse)

# patch
pyoauth2.libs.request.Request.request = request

from pyoauth2.libs.request import Request
from pyoauth2 import Client as OAuthClient
from pyoauth2 import AccessToken
from pyoauth2.libs.connection import Connection

DEFAULT_TIMEOUT = 15

logger = logging.getLogger(__name__)

class EDOOAuthClient(OAuthClient):

    def get_token(self, **opts):
        """ 易度比标准得到更多的token信息

            token_info = {'app_id':'workoneline',  'pid':'zope.manager', 'permissions':'permissions', 'is_rpc':True}
        """
        logger.info('request url %s', self.token_url())
        self.response = self.request(self.opts['token_method'], self.token_url(), **opts)
        opts.update(self.response.parsed)
        token_info = opts.get('token_info', {})
        if token_info:
            token_info['access_token'] = opts['access_token']
            token_info['refresh_token'] = opts['refresh_token']
        return AccessToken.from_hash(self, **opts), token_info

    def request(self, method, uri, **opts):
        # 有部分API的请求结构比较特殊：
        # - POST请求体是文件数据流
        # - POST query string是其他参数数据
        # 对这些API，需要做特殊处理，否则query string数据会丢失（在服务端看来就是缺少参数）
        opts.setdefault('timeout', self.opts.get('timeout', DEFAULT_TIMEOUT))

        if uri in [
            '/api/v2/content/upload',
            '/api/v3/content/upload',
            '/api/v2/content/upload_rev',
            '/api/v2/content/upload_attachment',
        ]:
            uri = Connection.build_url(self.site, path=uri)
            data = opts.pop('data')
            response = Request(method, uri, verify=self.opts['verify'], **opts).request(data)
        else:
            uri = Connection.build_url(self.site, path=uri)
            response = Request(method, uri, verify=self.opts['verify'], **opts).request()
        return response


class BaseClient(WoAPI):
    """ token管理"""

    def __init__(
        self, api_host, client_id, client_secret,
        auth_host='', redirect='', refresh_hook=None,
        account=None, instance=None, verify=None, timeout=DEFAULT_TIMEOUT,
        login_callback=None,
    ):
        self.api_host = api_host
        self.auth_host = auth_host
        if self.auth_host:
            self.authorize_url = self.auth_host + '/@@authorize'
        else:
            self.authorize_url = ''

        self.client = EDOOAuthClient(
            client_id, client_secret,
            site=api_host,
            authorize_url=self.authorize_url,
            token_url=self.api_host + '/api/v1/oauth2/access_token',
            verify=verify,  # 是否验证证书
            timeout=timeout
        )

        self.refresh_hook = refresh_hook
        self.redirect_uri = redirect
        self.refresh_hook = refresh_hook
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None

        # 预先设置的account信息，方便接口调用
        self.account_name = account
        self.instance_name = instance
        self.login_callback = login_callback

        # 应用客户端不知道 OC 地址，无法处理 Token 刷新
        # 所以这里添加属性，通过 get_client 获取的 client 自带一个原始 OcClient 对象，用于刷新 Token
        self.oc_client = None

    @property
    def token_code(self):
        return getattr(self._access_token, 'token', None)

    @property
    def refresh_token_code(self):
        return getattr(self._access_token, 'refresh_token', None)

    def refresh_token(self, refresh_token):
        # 2020年3月11日 15点19分 lwq
        # NOTE: 如果本体不是OC Client 的话，调用 refresh_token 会出现 500 错误
        #       原因是 api_host 地址并未指向 oc。所以必须使用 oc_client 调用 refresh_token，
        #       最后把获取到的新 token 转交给应用 Client
        if not isinstance(self, OcClient):
            self.oc_client.refresh_token(refresh_token)
            self.auth_with_token(self.oc_client._access_token)
        else:
            access_token = AccessToken(self.client, token='', refresh_token=refresh_token)
            self._access_token = access_token.refresh(account=self.account_name)[0]
            if not self.token_code:
                raise ApiError(403, 403, 'Authentication failed')

    def get_authorize_url(self, account=''):
        if self.authorize_url:
            return self.client.auth_code.authorize_url(redirect_uri=self.redirect_uri)
        else:
            self._access_token = AccessToken(self.client, token='', refresh_token='')
            auth_host = self.oauth.get_auth_host(account or self.account_name)['url']
            self._access_token = None
            self.authorize_url = auth_host + '/@@authorize'
            self.client.opts['authorize_url'] = self.authorize_url
            return self.client.auth_code.authorize_url(redirect_uri=self.redirect_uri)

    def auth_with_code(self, code, account='', return_token_info=True):
        if not account:
            account = self.account_name
        self._access_token, token_info = self.client.auth_code.get_token(code, account=account, return_token_info=return_token_info)
        if not self.token_code:
            raise ApiError(403, 403, 'Authentication failed')
        return token_info

    def auth_with_password(self, username, password, account='', **opt):
        if not account:
            account = self.account_name
        self._access_token, token_info = self.client.password.get_token(
            username=username,
            password=password, account=account, **opt
        )
        if not self.token_code:
            raise ApiError(403, 403, 'Authentication failed')
        return token_info

    def auth_with_signcode(self, username, secret, account='', **opts):
        if not account:
            account = self.account_name

        timestamp = str(int(time.time()))
        params = {
            'grant_type': 'signcode',
            'username': username,
            'timestamp': timestamp,
            'signcode': md5(timestamp + username + secret).hexdigest(),
            'account': account,
        }
        params.update(self.client.password.client_params)
        opts.update(params)
        self._access_token, token_info = self.client.get_token(**opts)

        if not self.token_code:
            raise ApiError(403, 403, 'Authentication failed')
        return token_info

    def auth_with_borrow_token(self, access_token, **opt):
        self._access_token, token_info = self.client.borrow.get_token(
            access_token=access_token, **opt
        )
        if not self.token_code:
            raise ApiError(403, 403, 'Authentication failed')
        return token_info

    def auth_with_token(self, access_token, refresh_token=''):
        if isinstance(access_token, AccessToken):
            token = access_token
            access_token = token.token
            refresh_token = token.refresh_token
        self._access_token = AccessToken(
            self.client, token=access_token, refresh_token=refresh_token
        )

    def auth_with_swap_token(self, access_token):
        if isinstance(access_token, AccessToken):
            token = access_token
            access_token = token.token
        params = {
            'grant_type': 'swap_token',
            'old_token': access_token,
            'account': self.account_name,
        }
        params.update(self.client.password.client_params)
        self._access_token, token_info = self.client.get_token(**params)
        return token_info

    def auth_with_rpc(self):
        token = md5(self.client_id + self.client_secret).hexdigest()
        self.auth_with_token(token)


class OrgClient(BaseClient, OrgAPI):
    pass


class WoClient(BaseClient, OperatorAPI, WoAPI):
    pass


class MessageClient(BaseClient, OperatorAPI, MessageAPI):
    pass


class ViewerClient(BaseClient, OperatorAPI, ViewerAPI):
    pass


class UploadClient(BaseClient, OperatorAPI, UploadAPI):
    pass


class HcClient(HcAPI):
    pass


class OcClient(BaseClient, OcAPI):
    """提供多种token获取途径"""

    def get_client(self, application='workonline', instance=None, login_callback=None):
        '''获取其他客户端'''
        instance = instance or self.instance_name
        # wo 实例信息可以从 oc 获取
        if application == 'org':
            api_client = OrgClient(
                self.api_host, self.client_id, self.client_secret,
                account=self.account_name, instance=instance, timeout=DEFAULT_TIMEOUT,
                login_callback=login_callback,
            )
            api_client.auth_with_token(self._access_token)
            return api_client

        elif application == 'workonline':
            app_instance = self.account.get_instance(
                account=self.account_name, application=application, instance=instance,
            )
            api_url = app_instance['api_url']
            log.debug(
                u'站点 %s 的 %s 服务 API 地址为: %s', instance, application, api_url,
            )

            #  获取连接
            app_client = WoClient(
                api_url, self.client_id, self.client_secret,
                account=self.account_name, instance=instance,
                timeout=DEFAULT_TIMEOUT,
                login_callback=login_callback,
            )

            #  获取认证
            app_client.auth_with_token(self._access_token)
            log.debug(
                u'成功创建 %s 帐号 %s 站点的 %s 服务客户端，OC: %s',
                self.account_name, instance, application, self.api_host,
            )
            app_client.oc_client = self
            return app_client

        else:
            # 其他服务的实例信息必须从 wo 获取
            # 先获取 wo 信息，构造 WoClient
            wo_api_url = self.account.get_instance(
                account=self.account_name, application='workonline', instance=instance,
            )['api_url']
            wo = WoClient(
                wo_api_url, self.client_id, self.client_secret,
                account=self.account_name, instance=instance, timeout=DEFAULT_TIMEOUT,
                login_callback=login_callback,
            )
            wo.auth_with_token(self._access_token)

            # 查询服务 API 地址，构造指定服务的 client
            api_url = wo.content.list_api_urls(self.account_name, instance)[application]
            log.debug(u'站点 %s 的 %s 服务 API 地址为: %s', instance, application, api_url)
            app_client = APP_CLIENTS[application](
                api_url, self.client_id, self.client_secret,
                account=self.account_name, instance=instance, timeout=DEFAULT_TIMEOUT,
                login_callback=login_callback,
            )
            app_client.auth_with_token(self._access_token)
            log.debug(
                u'成功创建 %s 帐号 %s 站点的 %s 服务客户端，OC: %s',
                self.account_name, instance, application, self.api_host,
            )
            app_client.oc_client = self
            return app_client


APP_CLIENTS = {
    'workonline': WoClient,
    'viewer': ViewerClient,
    'message': MessageClient,
    'org': OrgClient,
    'oc': OcClient,
    'upload': UploadClient,
}


def get_client(
    application, oc_api, account, instance,
    username='', password='', token='',
    client_id='test', client_secret='022127e182a934dea7d69s10697s8ac2',
    timeout=DEFAULT_TIMEOUT, login_callback=None, refresh_token='', refresh_hook=None
):
    if not token and not (username or password):
        log.critical(u'token 和 用户名+密码 必须至少提供一个')
        return None

    # 连接应用服务器
    log.debug(u'连接到 OC, 地址: %s', oc_api)

    # 这几种客户端可以直接实例化返回，不需要连接 oc 去查询地址
    if application in ('oc', 'org', ):
        api_client = APP_CLIENTS[application](
            oc_api, client_id, client_secret,
            account=account, instance=instance, timeout=timeout,
            login_callback=login_callback, refresh_hook=refresh_hook
        )
        if token:
            api_client.auth_with_token(token, refresh_token)
        else:
            api_client.auth_with_password(
                username=username,
                password=password,
                account=account
            )
        return api_client

    oc_client = OcClient(
        oc_api, client_id, client_secret, account=account, timeout=timeout,
        login_callback=login_callback
    )

    #  获取认证
    log.debug(u'获取服务器认证, 账号: %s', account)
    if token:
        oc_client.auth_with_token(token, refresh_token)
    else:
        oc_client.auth_with_password(
            username=username,
            password=password,
            account=account,
        )

    #  获取服务
    log.debug(u'获取站点 %s 的 %s 服务 API 地址', instance, application)

    # wo 实例信息可以从 oc 获取
    if application in ('workonline', ):
        app_instance = oc_client.account.get_instance(
            account=account, application=application, instance=instance
        )
        api_url = app_instance['api_url']
        log.debug(u'站点 %s 的 %s 服务 API 地址为: %s', instance, application, api_url)

        #  获取连接
        app_client = APP_CLIENTS[application](
            api_url, client_id, client_secret,
            account=account, instance=instance, timeout=timeout,
            login_callback=login_callback,
        )

        #  获取认证
        app_client.auth_with_token(oc_client._access_token)
        log.debug(
            u'成功创建 %s 帐号 %s 站点的 %s 服务客户端，OC: %s',
            account, instance, application, oc_api,
        )
        app_client.oc_client = oc_client
        return app_client
    else:
        # 其他服务的实例信息必须从 wo 获取
        # 先获取 wo 信息，构造 WoClient
        wo_api_url = oc_client.account.get_instance(
            account=account, application='workonline', instance=instance
        )['api_url']
        wo = WoClient(
            wo_api_url, client_id, client_secret,
            account=account, instance=instance, timeout=timeout,
            login_callback=login_callback,
        )
        wo.auth_with_token(oc_client._access_token)

        # 查询服务 API 地址，构造指定服务的 client
        api_url = wo.content.list_api_urls(account, instance)[application]
        log.debug(u'站点 %s 的 %s 服务 API 地址为: %s', instance, application, api_url)
        app_client = APP_CLIENTS[application](
            api_url, client_id, client_secret,
            account=account, instance=instance, timeout=timeout,
            login_callback=login_callback,
        )
        app_client.auth_with_token(oc_client._access_token)
        log.debug(
            u'成功创建 %s 帐号 %s 站点的 %s 服务客户端，OC: %s',
            account, instance, application, oc_api,
        )
        app_client.oc_client = oc_client
        return app_client


if __name__ == '__main__':
    pass
