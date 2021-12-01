# -*- coding: utf-8 -*-
import json
from .base import BaseApi
from copy import deepcopy

class OrgApi(BaseApi):

    def list_org_structure(self, account=None, root='default', include_groups=True):
        account = self.account_name if account is None else account
        return self._get('/api/v1/org/list_org_structure', account=account, root=root, include_groups=json.dumps(include_groups))

    def list_person_ougroups(self, person, account=None):
        account = self.account_name if account is None else account
        return self._get('/api/v1/org/list_person_ougroups', account=account, person=person)

    def get_objects_info(self, objects, account=None):
        account = self.account_name if account is None else account
        objects=','.join(objects)
        return self._post('/api/v1/org/get_objects_info', account=account, objects=objects)

    def get_ou_detail(self, ou_id, include_disabled=False, account=None):
        account = self.account_name if account is None else account
        return self._get('/api/v1/org/get_ou_detail', account=account, ou_id=ou_id, include_disabled=json.dumps(include_disabled))

    def search(self, account=None, ou='', q='', scope='onelevel', object_type='', include_disabled=True, fields=[], **kwargs):
        account = self.account_name if account is None else account
        # 分段搜索
        if 'batch_size' not in kwargs and 'batch_start' not in kwargs:
            size = 1000
            params = deepcopy(kwargs)
            params['batch_size'] = size
            params['batch_start'] = 0
            qs = self._get('/api/v1/org/search', account=account, ou=ou, q=q, scope=scope,\
                object_type=object_type, include_disabled=json.dumps(include_disabled),
                fields=json.dumps(fields), params=json.dumps(params))
            count, result = qs['count'], qs['result']
            results = {
                'count': count,
                'result': result,
            }
            if count > len(results):
                num = count / size
                if count % size:
                    num += 1
                for index in range(1, num):
                    params['batch_start'] = index*size
                    qs = self._get('/api/v1/org/search', account=account, ou=ou, q=q, scope=scope,\
                        object_type=object_type, include_disabled=json.dumps(include_disabled),
                        fields=json.dumps(fields), params=json.dumps(params))
                    count, result = qs['count'], qs['result']
                    results['result'].extend(result)
            return results
        else:
            return self._get('/api/v1/org/search', account=account, ou=ou, q=q, scope=scope,\
                object_type=object_type, include_disabled=json.dumps(include_disabled),
                fields=json.dumps(fields), params=json.dumps(kwargs))

    def sync(self, objects_detail, send_mail, new_user_password='', by='', account=None, site_url=''):
        account = self.account_name if account is None else account
        return self._post('/api/v1/org/sync', account=account, objects_detail=json.dumps(objects_detail), send_mail=json.dumps(send_mail), new_user_password=new_user_password, by=by, site_url=site_url)

    def remove_objects(self, objects, by='', account=None):
        account = self.account_name if account is None else account
        objects = ','.join(objects)
        return self._get('/api/v1/org/remove_objects', account=account, objects=objects, by=by)

    def list_groups_members(self, groups, account=None):
        account = self.account_name if account is None else account
        groups = ','.join(groups)
        return self._get('/api/v1/org/list_groups_members',  account=account, groups=groups)

    def add_group_members(self, group_id, users, by='', account=None):
        account = self.account_name if account is None else account
        users = ','.join(users)
        return self._get('/api/v1/org/add_group_members',  account=account, group_id=group_id, users=users, by=by)
    # OLD
    def add_group_users(self, group_id, users, by='', account=None):
        account = self.account_name if account is None else account
        users = ','.join(users)
        return self._get('/api/v1/org/add_group_users',  account=account, group_id=group_id, users=users, by=by)

    def remove_group_members(self, group_id, users, by='', account=None):
        account = self.account_name if account is None else account
        users = ','.join(users)
        return self._get('/api/v1/org/remove_group_members',  account=account, group_id=group_id, users=users, by=by)
    # OLD
    def remove_group_users(self, group_id, users, by='', account=None):
        account = self.account_name if account is None else account
        users = ','.join(users)
        return self._get('/api/v1/org/remove_group_users',  account=account, group_id=group_id, users=users, by=by)

    def set_order(self, ou_id, order, account=None):
        account = self.account_name if account is None else account
        order = ','.join(order)
        return self._get('/api/v1/org/set_order',  account=account, ou_id=ou_id, order=order)

    def unset_role_principals(self, ou, role, principals, account=None):
        account = self.account_name if account is None else account
        return self._get('/api/v1/org/unset_role_principals',  account=account, ou=ou, role=role, principals=principals)

    def grant_role_principals(self, ou, role, principals, account=None):
        account = self.account_name if account is None else account
        return self._get('/api/v1/org/grant_role_principals',  account=account, ou=ou, role=role, principals=principals)

    def list_role_principals(self, ou, role, inherit=True, account=None):
        account = self.account_name if account is None else account
        return self._get('/api/v1/org/list_role_principals', account=account, ou=ou, role=role, inherit=json.dumps(inherit))
