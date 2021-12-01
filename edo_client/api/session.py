# -*- coding: utf-8 -*-
import json
from .base import BaseApi
from ..error import ApiError


class SessionApi(BaseApi):
    def __init__(self, *args, **kwargs):
        super(SessionApi, self).__init__(*args, **kwargs)

    def online_users(self, account=None, instance=None, count_only=True):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._post('/api/v1/session/online_users', account=account, instance=instance, count_only=json.dumps(count_only))

    def connections(self, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._post('/api/v1/session/connections', account=account, instance=instance)

    def user_state(self, users, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._post('/api/v1/session/user_state', users=json.dumps(users),
                          account=account, instance=instance)

    def detail(self, user_id, account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        try:
            return self._post(
                '/api/v2/session/detail',
                user_id=user_id, account=account, instance=instance,
            )['connections']
        except ApiError as e:
            if e.code == 404:
                return self._post(
                    '/api/v1/session/detail',
                    user_id=user_id, account=account, instance=instance,
                )
            else:
                raise

    def kill_connection(self, user_id, client_id, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._post('/api/v1/session/kill_connection',
                          user_id=user_id, client_id=client_id,
                          account=account, instance=instance)

    def kill_user(self, user_id, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._post('/api/v1/session/kill_user', user_id=user_id, account=account, instance=instance)

