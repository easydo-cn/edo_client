# -*- coding: utf-8 -*-
import time

from edo_client import MessageClient

auth_host = ''
api_host = ''  # 使用wo的api地址
key = ''
secret = ''
redirect_uri = ''
account = ''
instance = ''
access_token = ''
refresh_token = ''

msg_client = MessageClient(api_host, key, secret, auth_host, redirect_uri, account=account, instance=instance)
msg_client.auth_with_token(access_token, refresh_token)

# 连接消息中心
msgapi = msg_client.message
msgapi.connect()

# 发送一个通知
result = msgapi.send(type='notify', 
                                 body={
                                     'type': 'notify', 
                                     'to': 'users.admin', 
                                     'content': 'Hi'
                                 })

# 查询指定时间段内消息记录的数量
count_info = msgapi.query_count(time_start=time.time() - 600, 
                                            time_end=time.time())

# 查询十分钟前开始的前 100 条消息记录
msgs = msgapi.query(time_start=time.time() - 600, 
                                time_end=time.time(), 
                                limit=100)

# 查询未读消息数
unread_info = msgapi.unread_stat()