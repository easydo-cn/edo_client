from edo_client import WoClient, UploadClient
import os

auth_host = 'http://192.168.1.115:62901/oc_api'
api_host = 'http://192.168.1.115:62900'
key = 'test'
secret = '022127e182a934dea7d69s10697s8ac2'
redirect_uri = ''
account = 'zopen'
instance = 'default'
access_token = 'f2ba47a69c2837aa3ccbc20d097d5c1c'
refresh_token = ''

wo_client = WoClient(api_host, key, secret, auth_host, redirect_uri, account=account, instance=instance)
wo_client.auth_with_token(access_token, refresh_token)
uid = '1680183990'
path = r'C:\Users\lousl\Downloads\upload.png'

size = os.path.getsize(path)
upload_sign = wo_client.content.get_upload_signcode(uid=uid, filename='upload')
upload_server = upload_sign.pop('upload_server')

upload_client = UploadClient(upload_server, key, secret, auth_host, account=account, instance=instance)
upload_client.auth_with_token(access_token)

print upload_sign
session_url = upload_client.upload.create_session(filename='upload.png', size=size, parent_rev=None, suffix='.png',
                                                  **upload_sign)

f = open(path, 'rb')
offset = upload_client.upload.get_offset(session_url)
while offset is not None:
    resp = upload_client.upload.put_chunk(
        session_url, f, offset, chunk_size=2*2**20
    )
    offset = resp.get('offset')
    rate = offset * 100.0 / size if offset else 100
    print rate
f.close()
