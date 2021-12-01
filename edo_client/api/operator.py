# -*- coding: utf-8 -*-
from .base import BaseApi
import json
import socket

timeout = 20


class OperatorApi(BaseApi):

    def create_instance(self, account_name, instance_name, instance_title, admin_uid, init_options):
        params = {'instance_name':instance_name,
                'account_name':account_name,
                'instance_title':instance_title,
                'admin_uid':admin_uid,
                'init_options':json.dumps(init_options)
                }
        timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(20)
        try:
            try:
                return self._get('/api/v1/operator/create_instance', **params)
            except socket.timeout:
                # 超时再试
                return self._get('/api/v1/operator/create_instance', **params)
        finally:
            socket.setdefaulttimeout(timeout)

    def update_options(self, account_name, instance_name,\
                               operation_options, removed_options, do_check):
        params = {'instance_name':instance_name,
                'account_name':account_name,
                'operation_options':json.dumps(operation_options),
                'removed_options':json.dumps(removed_options),
                'do_check':json.dumps(do_check)
                }

        timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(20)
        try:
            try:
                return self._get('/api/v1/operator/update_options', **params)
            except socket.timeout:
                return self._get('/api/v1/operator/update_options', **params)
        finally:
            socket.setdefaulttimeout(timeout)

    def list_options(self, account_name, instance_name):
        params = {'instance_name':instance_name,
                'account_name':account_name,
                'timeout': timeout,
                }
        return self._get('/api/v1/operator/list_options', **params)

    def check_quotas(self, account_name, instance_name, quotas):
        params = {'instance_name':instance_name,
                'account_name':account_name,
                'quotas':json.dumps(quotas),
                'timeout': timeout,
                }
        return self._get('/api/v1/operator/check_quotas', **params)

    def update_title(self, account_name, instance_name, title):
        params = {'instance_name':instance_name,
                'account_name':account_name,
                'title': title,
                'timeout': timeout,
                }
        return self._get('/api/v1/operator/update_title', **params)


    def destroy_instance(self, account_name, instance_name):
        params = {'instance_name':instance_name,
                'account_name':account_name,
                'timeout': 60 * 3,
                }
        return self._get('/api/v1/operator/destroy_instance', **params)

    def upgrade(self, account_name, instance_name):
        params = {'instance_name':instance_name,
                'account_name':account_name,
                'timeout': 60,
                }
        return self._get('/api/v1/operator/upgrade', **params)

    def refresh_org_cache(self, keys, account=None, instance=None):
        account = self.account_name if account is None else account
        instance = self.instance_name if instance is None else instance

        return self._post(
            '/api/v1/operator/refresh_org_cache',
            account=account, instance=instance, keys=json.dumps(keys),
            timeout=timeout
        )
