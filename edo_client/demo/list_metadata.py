from edo_client import WoClient, OcClient
import StringIO
"""
这里主要展示如果使用API下载一个文件。
假设你已经对如何认证了解清楚，已经得到了有效的access_token和refresh_token。
如果你对如何获取有效的token信息，请参照auth.py
"""

auth_host = ''
api_host = ''  # 使用wo的api地址
key = ''
secret = ''
redirect_uri = ''
account = ''
instance = ''
access_token = ''
refresh_token = ''


# 得到client
wo_client = WoClient(api_host, key, secret, auth_host, redirect_uri, account=account, instance=instance)

wo_client.auth_with_token(access_token, refresh_token)

# 得到文件夹下子文件和子文件夹的metadata
path = '' # path和uid任选一个作为参数传入
uid = '' # path和uid任选一个作为参数传入
start = 0
limit = ''
metadatas = wo_client.content.items(uid=uid, start=start, limit=limit)
 
# 得到文件的metadata
# 对应的path或者uid是文件的
path = '' # path和uid任选一个作为参数传入
uid = '' # path和uid任选一个作为参数传入
metadata = wo_client.content.metadata(uid=uid)

