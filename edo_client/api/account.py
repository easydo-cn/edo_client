# -*- coding: utf-8 -*-
from .base import BaseApi
import json

class AccountApi(BaseApi):

    # OC提供的API
    def list_instances(self, application, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/list_instances', application=application, account=account)

    def get_instance(self, application, instance, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/get_instance', application=application, account=account, instance=instance)

    def get_user_roles(self, user, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/get_user_roles', account=account, user=user)

    def set_user_roles(self, user, roles, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/set_user_roles', user=user, roles=roles, account=account)

    def get_role_users(self, role, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/get_role_users', account=account, role=role)

    def set_role_users(self, role, users, account=None):
        if not account: account = self.account_name
        users = json.dumps(users)
        return self._get('/api/v1/account/set_role_users', role=role, users=users, account=account)

    def get_license_members(self, license, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/get_license_members', account=account, license=license)

    def get_remaining(self, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/get_remaining', account=account)

    def list_tickets(self, application, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/account/list_tickets', account=account, application=application, instance=instance)

    def get_ticket(self, application, ticket, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/account/get_ticket', account=account, application=application, instance=instance, ticket=ticket)

    def update_ticket(self, application, ticket, levels, quotas, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/account/update_ticket', account=account, application=application, instance=instance, ticket=ticket, levels=json.dumps(levels), quotas=json.dumps(quotas))

    def pay_ticket(self, application, ticket, fee, amount=0, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/account/pay_ticket', account=account, application=application, instance=instance, ticket=ticket, fee=fee, amount=amount)

    def list_application_options(self, application, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/list_application_options', account=account, application=application)

    def list_service_levels(self, service, account):
        if not account: account = self.account_name
        return self._get('/api/v1/account/list_service_levels', account=account, service=service)

    def list_custom_roles(self, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/list_custom_roles', account=account)

    def set_custom_roles(self, roles, account=None):
        if not account: account = self.account_name
        return self._get('/api/v1/account/set_custom_roles', account=account, roles=json.dumps(roles))

    def get_login_properties(self, account=None):
        account = self.account_name if account is None else account
        return self._get('/api/v1/account/get_login_properties', account=account)
