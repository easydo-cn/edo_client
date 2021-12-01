from edo_client import WoClient, OcClient

auth_host = ''
api_host = ''
key = ''
secret = ''
redirect_uri = ''
account = ''
instance = ''


# 得到认证地址
oc_client = OcClient(api_host, key, secret, auth_host, redirect_uri, account=account, instance=instance)

authorize_url = oc_client.get_authorize_url()

# 授权模式
# =========================================
# 从易度服务器上得到code
code = ''

# 认证client
oc_client.auth_with_code(code, account)

# 用户名密码模式
# =========================================
username = ''
password = ''
oc_client.auth_with_password(username, password, account)


# 从client对象中得到access_token，refresh_token
access_token = ''
refresh_token = ''

# 重用token
# =========================================
# 使用已存在的access_token认证client
oc_client = OcClient(api_host, key, secret, auth_host, redirect_uri, account=account, instance=instance)
oc_client.auth_with_token(access_token, refresh_token)

# 主动刷新access_token
# =========================================
oc_client.refresh_token(refresh_token)


# 保存access_token
# 从client对象中得到access_token，refresh_token(保存新的token信息)
access_token = oc_client.token_code()
refresh_token = oc_client.refresh_token_code()


