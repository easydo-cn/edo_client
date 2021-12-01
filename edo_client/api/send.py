# -*- coding: utf-8 -*-
import json
from .base import BaseApi

class SendApi(BaseApi):

    def qiniu(self, account=None, instance=None, locations=[], qiniu_upload_token="", qiniu_key="", secret="", callback_body={}, callback=""):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/send/qiniu', account=account, instance=instance, locations=json.dumps(locations),\
                                                      qiniu_upload_token=qiniu_upload_token, qiniu_key=qiniu_key,\
                                                      secret=secret, callback_body=json.dumps(callback_body), callback=callback)

