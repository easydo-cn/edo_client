# -*- coding: utf-8 -*-
from .base import BaseApi

class AuthApi(BaseApi):

    def check_password(self, password):
        return self._get('/api/v1/auth/check_password', password=password)

    def reset_password(self, password, new_password):
        return self._get('/api/v1/auth/reset_password', password=password, new_password=new_password)

    def enable_dynamic_auth(self, secret_key, code):
        return self._get('/api/v1/auth/enable_dynamic_auth', secret_key=secret_key, code=code)

    def disable_dynamic_auth(self, code):
        return self._get('/api/v1/auth/disable_dynamic_auth', code=code)

    def is_dynamic_auth_enabled(self):
        return self._get('/api/v1/auth/is_dynamic_auth_enabled')

