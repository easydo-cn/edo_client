# -*- coding: utf-8 -*-
from .base import BaseApi

class OAuthApi(BaseApi):

    def get_token_info(self):
        """ 当前用户的账户信息 """
        return self._get('/api/v1/oauth2/get_token_info')

    def get_auth_host(self, account):
        """ 当前用户的账户信息 """
        return self._get('/api/v1/oauth2/get_auth_host', account=account)

    def access_token(self, client_id, client_secret, account, grant_type, code='', username='', password='', refresh_token='', old_token="", **opt):
        return self._get('/api/v1/oauth2/access_token', client_id=client_id, client_secret=client_secret, account=account, grant_type=grant_type, code=code, username=username, password=password, refresh_token=refresh_token, old_token=old_token)
    
    def logout(self):
        return self._get('/api/v1/oauth2/logout')
