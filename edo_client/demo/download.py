from edo_client import WoClient, OcClient
from io import BytesIO

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


# 得到认证地址
wo_client = WoClient(api_host, key, secret, auth_host, redirect_uri, account=account, instance=instance)

wo_client.auth_with_token(access_token, refresh_token)

# 下载文件对应的信息

path = '' # path和uid任选一个作为参数传入
uid = '' # path和uid任选一个作为参数传入
mime = '' # 为空下载源文件
filepath = '/tmp/test'  # 文件下载到的路径
tmpfile = BytesIO() # 文件下载至内存

# 将文件下载到 file 或 BytesIO 对象
wo_client.content.download(stream=tmpfile, path=path, uid=uid, mime=mime)

# 将文件下载到指定路径，碰到网络错误会自动重试
wo_client.content.download(filepath, path=path, uid=uid, mime=mime)
