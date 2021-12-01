======================
SDK使用介绍
======================

准备工作
=================

- 开发应用申请

应用的开发者，首先向易度（developer@everydo.com）申请注册一个应用，易度会提供如下2个信息用于开发：

    - client_id: 应用的ID
    - client_secret: 应用的密钥，这个需要妥善保存

- 回调地址

你需要提供一个回调地址来接收认证后返回的code


使用SDK
=============

准备你的应用ID、秘钥、回调地址、API地址、认证站点地址（没有可以为空） ::

    callback_url = 'http://127.0.0.1/callback'
    api_host = 'http://oc.api.everydo.cn'

    app_id = 'test_id'
    app_screct = 'test_screctxxxxxxxxxxxxxxxx'


建立一个client,获取认证地址 ::

    from client import OcClient

    client = OcClient(api_host, app_id, app_screct, callback_url, account='zopen')


    # 得到认证地址
    authorize_url = client.get_authorize_url()  
    
从回调地址中得到code，使用code来认证这个client::

    # 从回调中得到code之后
    code = '129128192'
    client = OcClient(api_host, app_id, app_screct, callback_url, account='zopen')

    client.auth_with_code(code)

将token信息保存到数据库中 ::

    # 从client中得到access_token,refresh_token
    access_token = client.token_code()
    refresh_token = client.refresh_token_code()

直接使用数据库中的access_token来认证客户端 ::

    # 使用access_token来生成client

    client = OcClient(api_host, app_id, app_screct, callback_url)
    client.auth_with_token(access_token, refresh_token)
