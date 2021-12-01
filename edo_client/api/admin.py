# -*- coding: utf-8 -*-
from .base import BaseApi
import time
from hashlib import md5


class AdminApi(BaseApi):
    """内部充值接口"""

    def create_account(self, account_name, account_title, username, fullname, password, timestamp, signcode, email='', phone='', lang='zh', setup='', login_name=''):
        return self._get('/api/v1/admin/create_account', account_name=account_name, account_title=account_title, 
                            username=username, fullname=fullname, password=password, timestamp=timestamp, signcode=signcode, email=email, phone=phone, lang=lang, setup=setup, login_name=login_name)

    def list_accounts(self, start='', end=''):
        return self._get('/api/v1/admin/list_accounts', start=start, end=end)

    def new_code(self, score, deadline, creator, description, secret, account_name=''):
        timestamp = int(time.time()) + 100
        format = "%Y-%m-%d %H:%M:%S" 
        deadline = deadline.strftime(format)
        text = '%s%s%s%s%s%s' % (score, deadline, creator, description, timestamp, secret)
        signcode = md5(text).hexdigest()
        return self._get('/api/v1/admin/new_code', score=score, deadline=deadline, creator=creator, description=description, timestamp=timestamp, signcode=signcode, account_name=account_name)

    def remove_code(self, code, secret):
        timestamp = int(time.time()) + 100
        text = "%s%s%s" % (code, timestamp, secret)
        signcode = md5(text).hexdigest()
        return self._get('/api/v1/admin/remove_code', code=code, timestamp=timestamp, signcode=signcode)

    def list_codes(self, secret):
        timestamp = int(time.time()) + 100
        text = "%s%s" % (timestamp, secret)
        signcode = md5(text).hexdigest()
        return self._get('/api/v1/admin/list_codes',timestamp=timestamp, signcode=signcode)

    def get_code(self, code, secret):
        timestamp = int(time.time()) + 100
        text = "%s%s%s" % (code, timestamp, secret)
        signcode = md5(text).hexdigest()
        return self._get('/api/v1/admin/get_code', timestamp=timestamp, code=code, signcode=signcode)

    def use_code(self, code, secret, account=None):
        if not account:
            account = self.account_name
        timestamp = int(time.time()) + 100
        text = "%s%s%s" % (code, timestamp, secret)
        signcode = md5(text).hexdigest()
        return self._get('/api/v1/admin/use_code', timestamp=timestamp, code=code, signcode=signcode, account=account)

    def upgrade(self, account_name):
        return self._get('/api/v1/admin/upgrade', account_name=account_name)

    def register_operator(self, operator_id, title, wo_api_url, wo_url, secret):
        '''想中心运营点OC服务器，注册或更新一个分运营点
        - operator_id: 分运营点的编号
        - title: 分运营点的名字
        - wo_api_url: 分运营点的 WO API 访问地址（需要可达，否则无法管理分运营点站点）
        - wo_url: 分运营点 WO 的用户访问地址（需要可达，否则用户无法从界面跳转）
        - secret: 运营中心通信密钥
        '''
        signcode = md5(operator_id + title + wo_api_url + wo_url + secret).hexdigest()
        return self._post(
            '/api/v2/admin/register_operator',
            operator_id=operator_id, title=title,
            wo_api_url=wo_api_url, wo_url=wo_url,
            signcode=signcode,
        )
