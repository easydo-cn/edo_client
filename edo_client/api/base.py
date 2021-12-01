# -*- coding: utf-8 -*-
import logging
from ..error import ApiError
from requests.exceptions import ConnectionError
from requests import Response
import time
from pyoauth2 import AccessToken

DEFAULT_START = 0
DEFAULT_COUNT = 20
logger = logging.getLogger(__name__)

def check_execption(func):
    def _check(*arg, **kws):
        # 网络错误, 连接不到服务器
        try:
            resp, data = func(*arg, **kws)
        except ConnectionError:
            # retry
            time.sleep(0.1)
            try:
                resp, data = func(*arg, **kws)
            except ConnectionError as e:
                raise ApiError(111, 111, 'network error: ' + str(e))
        # 地址错误
        if resp.status == 404:
            raise ApiError(404, 404, '404 Not Found')

        if resp.status >= 400:
            self = arg[0]
            # 如果得到的是一个Response对象，先将数据转化为json
            if isinstance(data, Response):
                try:
                    data = data.json()
                except ValueError as e:
                    data = {
                        'code': resp.status,
                        'message': data.text
                    }
            if data['code'] == 401:
                if not kws.get('___refreshed', False) and self._access_token.refresh_token:
                    logger.info(u'Found 401 error, trying refresh access token')
                    try:
                        self.client.refresh_token(self._access_token.refresh_token)
                        if self.refresh_hook:
                            self.refresh_hook(self._access_token.token, self._access_token.refresh_token)
                        return _check(*arg, ___refreshed=True, **kws)
                    except Exception:
                        logger.exception('error occured when refreshing access token using refresh token.')

                if not kws.get('___logined', False) and self.client.login_callback:
                    logger.info(u'Refreshing failed, try login callback.')
                    try:
                        access_token, refresh_token = self.client.login_callback()
                        self.client.auth_with_token(access_token, refresh_token)
                        return _check(*arg, ___logined=True, **kws)
                    except Exception:
                        logger.exception('error occured when trying to call login_callback.')

            raise ApiError(resp.status, data['code'], data['message'])

        # 根据返回值的 errcode 抛出 ApiError
        if isinstance(data, dict):
            errcode = data.get('errcode', None)
            if errcode is not None and errcode != 0:
                raise ApiError(resp.status, errcode, data.get('errmsg'))

        return data

    return _check


class BaseApi(object):
    def __init__(self, client, access_token, refresh_hook, account=None, instance=None):
        self.client = client
        self.refresh_hook = refresh_hook
        self._access_token = access_token
        self.account_name = account
        self.instance_name = instance

    def __repr__(self):
        return '<EverydoAPI Base>'

    @check_execption
    def _get(self, url, raw=False, **opts):
        # 是否返回json格式的数据
        if raw:
            response = self._access_token.get(url, stream=True, parse=None, **opts)
            return response, response.resp

        else:
            response = self._access_token.get(url, **opts)
            try:
                return response, response.resp.json()
            except:
                #raise ApiError(response.resp.status_code, 500, "服务器出错：\nreason: %s\nAPI地址：%s\n" % (response.resp.reason, response.resp.url))
                raise ApiError(response.resp.status_code, 500, "服务器出错：\nreason: %s\nAPI地址：%s\n" % (response.resp.reason, ''))

    @check_execption
    def _post(self, url, raw=False, **opts):
        # 是否返回json格式的数据
        if raw:
            response = self._access_token.post(url, stream=True, parse=None, **opts)
            return response, response.resp
        else:
            response = self._access_token.post(url, **opts)
            try:
                return response, response.resp.json()
            except:
                raise ApiError(response.resp.status_code, 500, "服务器出错：\nreason: %s\nAPI地址：%s\n" % (response.resp.reason, ''))


    @check_execption
    def _put(self, url, raw=False, **opts):
        # 是否返回json格式的数据
        if raw:
            response = self._access_token.put(url, stream=True, parse=None, **opts)
            return response, response.resp

        else:
            response = self._access_token.put(url, **opts)
            try:
                return response, response.resp.json()
            except:
                raise ApiError(response.resp.status_code, 500, "服务器出错：\nreason: %s\nAPI地址：%s\n" % (response.resp.reason, ''))

    @check_execption
    def _patch(self, url, raw=False, **opts):
        # 是否返回json格式的数据
        if raw:
            response = self._access_token.patch(url, stream=True, parse=None, **opts)
            return response, response.resp
        else:
            response = self._access_token.patch(url, **opts)
            try:
                return response, response.resp.json()
            except:
                raise ApiError(response.resp.status_code, 500, "服务器出错：\nreason: %s\nAPI地址：%s\n" % (response.resp.reason, ''))

    @check_execption
    def _delete(self, url, raw=False, **opts):
        # 是否返回json格式的数据
        if raw:
            response = self._access_token.delete(url, stream=True, parse=None, **opts)
            return response, response.resp
        else:
            response = self._access_token.delete(url, **opts)
            try:
                return response, response.resp.json()
            except:
                raise ApiError(response.resp.status_code, 500, "服务器出错：\nreason: %s\nAPI地址：%s\n" % (response.resp.reason, ''))

    @check_execption
    def _head(self, url, raw=False, **opts):
        # 是否返回json格式的数据
        if raw:
            response = self._access_token.request('HEAD', url, stream=True, parse=None, **opts)
            return response, response.resp

        else:
            response = self._access_token.request('HEAD', url, stream=True, parse=None, **opts)
            try:
                return response, response.resp.json()
            except:
                raise ApiError(response.resp.status_code, 500, "服务器出错：\nreason: %s\nAPI地址：%s\n" % (response.resp.reason, ''))
