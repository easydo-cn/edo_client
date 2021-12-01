# -*- coding: utf-8 -*-
import hashlib
import json
from .base import BaseApi

class ViewerApi(BaseApi):

    def get_secret(self, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/viewer/get_secret', account=account, instance=instance)

    def set_access_policy(self, policy='private', account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/viewer/set_access_policy', account=account, instance=instance, policy=policy)

    def get_access_policy(self, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/viewer/get_access_policy', account=account, instance=instance)

    def refresh_secret(self, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/viewer/refresh_secret', account=account, instance=instance)

    def remove_cache(self, device, path, mimes, expire=None, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._get('/api/v1/cache/remove', account=account, instance=instance, device=device, path=path, mimes=','.join(mimes), expire=expire)

    def transform(self, device, location, timestamp='', signcode='', targets='', callbacks=None, params=None, filenames={}, error_callbacks=None, account=None, instance=None, source_mime=None, first=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._post('/transform', device=device, location=location, account=account, instance=instance,
                         timestamp=timestamp,
                         signcode=signcode,
                         targets=targets, callbacks=json.dumps(callbacks),
                         source_mime=source_mime,
                         error_callbacks=json.dumps(error_callbacks), params=json.dumps(params), filenames=json.dumps(filenames), first=first)

    def gen_view_signcode(self, device, location, account, instance, secret, ip='', timestamp='', username='', permission=''):
        text = device + location + account + instance + ip + timestamp + username + permission + secret
        return text2signcode(text)

    def test_signcode(self, device, location, account, instance, signcode, **kwargs):
        return self._get('/api/v1/viewer/test_signcode', device=device, location=location, account=account, instance=instance,
                signcode=signcode, **kwargs)

    def create_zip(self, account=None, instance=None, files_info=[], zip_filename='', expire=600):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._post('/api/v1/viewer/create_zip',
                        account=account, instance=instance,
                        files_info=json.dumps(files_info),
                        zip_filename=zip_filename,
                        expire=expire)

    def gen_zip_signcode(self, zip_key, expire, secret, account=None, instance=None):
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return gen_zip_signcode(account, instance, zip_key, expire, secret)


def text2signcode(text):
    sign_md5 = hashlib.md5()
    sign_md5.update(text)
    signcode = sign_md5.hexdigest()
    return signcode


def gen_zip_signcode(account, instance, zip_key, expire, secret):
    text = account + instance + zip_key + secret + str(expire)
    return text2signcode(text)

