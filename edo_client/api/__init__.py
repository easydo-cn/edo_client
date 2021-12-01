# -*- coding: utf-8 -*-
import logging

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

from ..error import ApiError, UploadTokenExpired, UploadDupException

from .auth import AuthApi
from .org import OrgApi
from .oauth2 import OAuthApi
from .viewer import ViewerApi
from .operator import OperatorApi
from .content import ContentApi, ContentV2Api, ContentV3Api
from .message import MessageApi, MessageV2Api
from .session import SessionApi
from .package import PackageApi
from .admin import AdminApi
from .send import SendApi
from .account import AccountApi as account_api
from .upload import UploadApi

from .hc import HcApi as HcAPI  # noqa
from .session_store import SessionStore  # noqa
from .base import check_execption
from ..rse import RemoteScriptExecuteEngine



class OperatorAPI(object):

    @property
    def operator(self):
        """ 当前用户相关的接口 """
        return OperatorApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)


class OcAPI(object):

    @property
    def auth(self):
        """ 当前用户相关的接口 """
        return AuthApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def account(self):
        return account_api(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def oauth(self):
        """ 当前token相关的接口 """
        return OAuthApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def admin(self):
        """ 充值码相关接口, 易度内部使用 """
        return AdminApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)


class OrgAPI(object):

    @property
    def org(self):
        """ 组织架构相关的管理接口"""
        return OrgApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)


class WoAPI(object):
    @property
    def content(self):
        return ContentApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def content_v2(self):
        return ContentV2Api(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def content_v3(self):
        return ContentV3Api(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def package(self):
        """ 当前用户相关的接口 """
        return PackageApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @check_execption
    def xapi(self, script_name, account=None, instance=None, uid=None, path=None, **kw):
        '''调用扩展应用 API'''
        endpoint = '/api/v3/x-api/{}'.format(script_name)
        kw.update({
            'account': account or self.account_name,
            'instance': instance or self.instance_name,
            'uid': uid,
            'path': path,
        })
        response = self._access_token.post(endpoint, **kw)
        if response.content_type == 'application/json':
            try:
                return response, response.resp.json()
            except ValueError:
                raise ApiError(
                    response.resp.status_code, 500,
                    u'服务器错误：{}'.format(response.resp.reason)
                )
        else:
            return response, response.resp.content

    def get_rse(self, script_env=None, verify=True):
        '''获取脚本执行引擎'''
        return RemoteScriptExecuteEngine(self, script_env, verify)

    def upload_file(self, path='', uid='', filename='', upload_sign=None, chuck_size=None, parent_rev=None,
               expire=60*60*24*2, on_progress=None,maxsize=1024*1024*1024*1024, account=None, allow_duplicate=None,
               instance=None,auto_fork=False,notify_subscribers=False, setprivate=False,hash=None):

        from ..client import DEFAULT_TIMEOUT, UploadClient
        # 获取上传凭证
        def _get_upload_ticket():
            upload_sign = self.content.get_upload_signcode(
                account=account,
                instance=instance,
                uid=uid, path=path,
                parent_rev=parent_rev,
                expire=expire,
                maxsize=maxsize,
                filename=filename,
                auto_fork=auto_fork,
                notify_subscribers=notify_subscribers,
                setprivate=setprivate,
                hash=hash)
            return upload_sign

        # 1.获取上传凭证
        # 如果有旧的上传凭证使用旧的,没有的话新申请一个
        if not upload_sign:
            upload_sign = _get_upload_ticket()

        if not allow_duplicate and upload_sign.get('duplicated_files'):
            raise UploadDupException(upload_sign)

        while True:
            # 2. 上传
            try:
                # 2.1 调用上传
                upload_client = UploadClient(
                    upload_sign.get('upload_server'),
                    self.client_id,
                    self.client_secret,
                    account=account or self.account_name,
                    instance=instance or self.instance_name,
                    timeout=DEFAULT_TIMEOUT,
                )
                upload_client.auth_with_token(self._access_token)
                metadata = upload_client.upload.upload(fpath=path,
                                   upload_sign=upload_sign,
                                   chunk_size=chuck_size,
                                   on_progress=on_progress)
                break
            # 2.2 token过期则重新生成一个token再次上传
            except UploadTokenExpired:
                upload_sign = _get_upload_ticket()

        return metadata

class MessageAPI(object):

    @property
    def message(self):
        return MessageApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def message_v2(self):
        return MessageV2Api(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def session(self):
        return SessionApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)


class ViewerAPI(object):

    @property
    def viewer(self):
        return ViewerApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)

    @property
    def send(self):
        return SendApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)


class UploadAPI(object):
    @property
    def upload(self):
        return UploadApi(self, self._access_token, self.refresh_hook, self.account_name, self.instance_name)
