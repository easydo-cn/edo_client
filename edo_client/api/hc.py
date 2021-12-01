import json
import httplib
import requests

from ..error import ApiError


class HcApi(object):
    def __init__(self, api_host, token,
                 src_oc_api, src_instance, src_account, src_username, src_password,
                 dst_oc_api, dst_instance, dst_account, dst_username, dst_password,
                 is_proxy_mode=False):

        self.api_host = api_host
        self.token = token,

        self.src_oc_api = src_oc_api
        self.src_instance = src_instance
        self.src_account = src_account
        self.src_username = src_username
        self.src_password = src_password

        self.dst_oc_api = dst_oc_api
        self.dst_instance = dst_instance
        self.dst_account = dst_account
        self.dst_username = dst_username
        self.dst_password = dst_password

        self.is_proxy_mode = is_proxy_mode

    def sync_files(self,
                   src_base_path, dst_base_path,
                   rpaths, fields=[],
                   callback_url='', error_callback_url=''):
        url = self.api_host + ('/api/sync_files_by_proxy' if self.is_proxy_mode else '/api/sync_files')
        req = requests.post(
            url,
            data={
                'token': self.token,
                'src_oc_api': self.src_oc_api,
                'src_instance': self.src_instance,
                'src_account': self.src_account,
                'src_username': self.src_username,
                'src_password': self.src_password,

                'dst_oc_api': self.dst_oc_api,
                'dst_instance': self.dst_instance,
                'dst_account': self.dst_account,
                'dst_username': self.dst_username,
                'dst_password': self.dst_password,

                'src_base_path': src_base_path,
                'dst_base_path': dst_base_path,
                'rpaths': json.dumps(rpaths),
                'fields': json.dumps(fields),

                'callback_url': callback_url,
                'error_callback_url': error_callback_url
            }
        )
        status = req.json()['status']
        if status['code'] != httplib.OK:
            raise ApiError(status['code'], status['code'], status['detail'])

    def send_to_qiniu(
        self, paths, qiniu_token, qiniu_key, encry_secret='',
        callback_url='', callback_body=''
    ):
        """send the files to qiniu

        """
        url = self.api_host + '/api/send_to_qiniu'
        req = requests.post(
            url,
            data={
                'token': self.token,
                'src_oc_api': self.src_oc_api,
                'src_instance': self.src_instance,
                'src_account': self.src_account,
                'src_username': self.src_username,
                'src_password': self.src_password,

                'paths': json.dumps(paths),
                'qiniu_token': qiniu_token,
                'qiniu_key': qiniu_key,
                'encry_secret': encry_secret,
                'callback_url': callback_url,
                'callback_body': callback_body
            }
        )
        status = req.json()['status']
        if status['code'] != httplib.OK:
            raise ApiError(status['code'], status['code'], status['detail'])

    def sync_dataitems(
        self, src_base_path, dst_base_path, rpaths, fields=[],
        callback_url='', error_callback_url=''
    ):
        url = self.api_host + ('/api/sync_dataitems_by_proxy' if self.is_proxy_mode else '/api/sync_dataitems')
        req = requests.post(
            url,
            data={
                'token': self.token,
                'src_oc_api': self.src_oc_api,
                'src_instance': self.src_instance,
                'src_account': self.src_account,
                'src_username': self.src_username,
                'src_password': self.src_password,

                'dst_oc_api': self.dst_oc_api,
                'dst_instance': self.dst_instance,
                'dst_account': self.dst_account,
                'dst_username': self.dst_username,
                'dst_password': self.dst_password,

                'src_base_path': src_base_path,
                'dst_base_path': dst_base_path,
                'rpaths': json.dumps(rpaths),
                'fields': json.dumps(fields),

                'callback_url': callback_url,
                'error_callback_url': error_callback_url
            }
        )
        status = req.json()['status']
        if status['code'] != httplib.OK:
            raise ApiError(status['code'], status['code'], status['detail'])

    def sync_shortcuts(self,
        src_base_path, dst_base_path, rpaths, fields='[]',
        callback_url='', error_callback_url=''
    ):
        url = self.api_host + ('/api/sync_shortchuts_by_proxy' if self.is_proxy_mode else '/api/sync_shortcuts')
        req = requests.post(
            url,
            data={
                'token': self.token,
                'src_oc_api': self.src_oc_api,
                'src_site': self.src_site,
                'src_account': self.src_account,
                'src_username': self.src_username,
                'src_password': self.src_password,

                'dst_oc_api': self.dst_oc_api,
                'dst_site': self.dst_site,
                'dst_account': self.dst_account,
                'dst_username': self.dst_username,
                'dst_password': self.dst_password,

                'src_base_path': src_base_path,
                'dst_base_path': dst_base_path,
                'rpaths': json.dumps(rpaths),
                'fields': json.dumps(fields),

                'callback_url': callback_url,
                'error_callback_url': error_callback_url
            }
        )
        status = req.json()['status']
        if status['code'] != httplib.OK:
            raise ApiError(status['code'], status['code'], status['detail'])

    def remove(
        self, paths,
        callback_url='', error_callback_url=''
    ):
        url = self.api_host + ('/api/remove_by_proxy' if self.is_proxy_mode else '/api/remove')
        req = requests.post(
            url,
            data={
                'token': self.token,
                'oc_api': self.dst_oc_api,
                'instance': self.dst_instance,
                'account': self.dst_account,
                'username': self.dst_username,
                'password': self.dst_password,

                'paths': json.dumps(paths),

                'callback_url': callback_url,
                'error_callback_url': error_callback_url
            }
        )
        status = req.json()['status']
        if status['code'] != httplib.OK:
            raise ApiError(status['code'], status['code'], status['detail'])

    def action_workitem(
        self, path, data, workitem_name, action_name,
        callback_url='', error_callback_url=''
    ):
        url = self.api_host + ('/api/action_workitem_by_proxy' if self.is_proxy_mode else '/api/action_workitem')
        req = requests.post(
            url,
            data={
                'token': self.token,
                'oc_api': self.dst_oc_api,
                'instance': self.dst_instance,
                'account': self.dst_account,
                'username': self.dst_username,
                'password': self.dst_password,

                'path': path,
                'data': data,
                'workitem_name': workitem_name,
                'action_name': action_name,

                'callback_url': callback_url,
                'error_callback_url': error_callback_url
            }
        )
        status = req.json()['status']
        if status['code'] != httplib.OK:
            raise ApiError(status['code'], status['code'], status['detail'])

if __name__ == '__main__':
    hc = HcApi(
        api_host='http://192.168.1.115:63522',
        token='123123123123123',

        src_oc_api='http://192.168.1.115:63501',
        src_instance='default',
        src_account='zopen',
        src_username='admin',
        src_password='admin123',

        dst_oc_api='http://192.168.1.115:63501',
        dst_instance='default',
        dst_account='zopen',
        dst_username='admin',
        dst_password='admin123',

    )

    hc.sync_files(
        src_base_path='desks/users.admin/files/',
        dst_base_path='desks/users.admin/files/Daily/',
        rpaths=['1.md']
    )

    hc.sync_dataitems(
        src_base_path='common_flow/document_borrow',
        dst_base_path='common_flow/document_borrow',
        rpaths=['703173']
    )

    hc.remove(
        paths=['desks/users.admin/files/Daily/1.md'],
    )
