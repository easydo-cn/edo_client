# coding: utf-8

import sys
import time
import json
import logging
import traceback
import certifi
import paho.mqtt.client as mqtt

from datetime import datetime
from .client import MessageClient, WoClient

MSG_QOS = 1
MSG_KEEPALIVE = 60
COMMAND_CATEGORY = 'command'
MSG_HANDLERS = {}


def get_logger(level=logging.DEBUG, logconsole=False, logfile=None):
    '''
    Easy way to get a logger
    Args: name, logconsole=False, level=logging.DEBUG, logfile=None
    '''
    name = 'RtcClient'
    if level not in ():
        level = logging.DEBUG

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler is always attached
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    console_handler.setLevel(level)

    stream_handled = False
    for i in logger.handlers:
        if isinstance(i, (logging.StreamHandler, )):
            stream_handled = True
    if logconsole and not stream_handled:
        logger.addHandler(console_handler)
    # Attach file handler if file path provided
    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


def msg_handler(evt):
    '''Register a function as a handler to event `evt`'''
    def actual_decorator(func):
        global MSG_HANDLERS
        if not MSG_HANDLERS.get(evt, []):
            MSG_HANDLERS[evt] = [func]
        else:
            MSG_HANDLERS[evt].append(func)
        return func
    return actual_decorator


def extract_traceback():
    e_type, e_value, tb = sys.exc_info()
    return '{0} - Uncaught exception: {1}: {2}\n{3}'.format(
        datetime.strftime(datetime.now(), '%H:%M:%S'),
        str(e_type), str(e_value), ''.join(traceback.format_tb(tb))
    )


def on_connect(client, userdata, flags, return_code):
    client_ref = userdata['ref']
    client_ref.mqtt_online = True
    # 订阅自己的 topic
    client_ref.logger.debug(u'已经连接到 MQTT 服务器，返回码 %d，flags：%s',
                            return_code, flags)
    for topic in userdata['topics'].values():
        client_ref.logger.debug(u'正在订阅 %s', topic)
        result, mid = client.subscribe(str(topic), qos=MSG_QOS)
        if result == mqtt.MQTT_ERR_SUCCESS:
            userdata['ref'].subscriptions.update({
                mid: [{'topic': topic, 'qos': -1}, ]
            })


def on_message(client, userdata, mqtt_msg):
    try:
        payload = json.loads(mqtt_msg.payload)
        userdata['ref'].handle_json_message(
            userdata,
            payload,
            topic=mqtt_msg.topic
        )
    except Exception:
        userdata['ref'].logger.error(
            u'在处理消息时发生异常：%s\n，消息：%s',
            extract_traceback(), mqtt_msg.payload
        )


def on_subscribe(client, userdata, mid, granted_qoses):
    # 发送上线消息
    self = userdata['ref']

    self.logger.debug(
        u'Granted QoS-es: %s for subscription: %s with mid of %d',
        granted_qoses,
        self.subscriptions.get(mid, None),
        mid
    )
    # Shrotcut
    FAIL = self.SUBSCRIPTION_FAILED

    # 发送订阅命令时记录下的当时请求订阅的所有 topic
    subscription = self.subscriptions.get(mid, None)
    assert subscription is not None

    for i in xrange(len(granted_qoses)):
        # 128 indicates this subscription failed (and the broker knows it)
        if granted_qoses[i] == FAIL:
            # Failed twice already, reconnect
            if subscription[i]['qos'] == FAIL:
                self.logger.warn(
                    u'topic %s 两次订阅失败，将尝试重连',
                    subscription[i]['topic']
                )
                self.online = False
                self.reconnect()
            # Failed the one and only time
            # try re-subscribe this topic once more
            else:
                self.logger.warn(
                    u'topic %s 首次订阅失败，将尝试重新订阅',
                    subscription[i]['topic']
                )
                self.subscriptions[mid][i].update({
                    'qos': FAIL
                })
                _topic = self.subscriptions[mid][i]['topic']
                result, _mid = client.subscribe(
                    str(_topic),
                    qos=MSG_QOS
                )
                if result == mqtt.MQTT_ERR_SUCCESS:
                    self.subscriptions[_mid] = [
                        {'topic': _topic, 'qos': FAIL}
                    ]
                    self.subscriptions.pop(mid, None)
                else:
                    self.logger.error(
                        u'第二次尝试订阅 %s 失败，返回值 %d，直接重连',
                        _topic,
                        result
                    )
                    self.online = False
                    self.reconnect()
        else:
            self.subscriptions[mid][i].update({
                'qos': granted_qoses[i]
            })

    self.send_connection_msg(True, userdata)
    self.logger.debug(u'上线消息已经发送')


def on_disconnect(client, userdata, return_code):
    # 重新连接
    self = userdata['ref']
    self.online = self.mqtt_online = False
    self.logger.debug(u'消息客户端已经断开连接，返回码：%d', return_code)
    self.emit('disconnected', {})
    self.reconnect()


class MessageContext(object):
    '''Just a plain object'''
    def __init__(self, **kwargs):
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])


class RtcClient(object):
    SUBSCRIPTION_FAILED = 128
    sys_topic = 'msgcenter'
    action_translations = {
        'share': '分享',
        'edit': '编辑',
        'new': '新建',
        'upload': '上传',
        'comment': '评论',
        'remind': '催办',
        'new_revision': '更新版本',
        'fix_revision': '定版',
        'workflow_sign': '触发流程',
        'publish': '存档',
        'workflow_resign': '更改流程',
    }

    def __init__(self, *args, **kwargs):
        '''
        Create a RtcClient object.
        Args:
            Required keyword arguments:
                server: message server URL
                account: account name
                instance: instance name
                token: user token
                pid: user id with `users.` prefix
            Optional keyword arguments:
                use_ssl: use SSL encrypted connection or not, defaults to False
                clean_session: use new session upon connection or not
                keepalive: heartbeat interval in seconds, defaults to 60
                qos: Quality of Service, defaults to 1 (only 1 is supported currently)
                wo_server: optional WO API server (UNUSED)
                allow_script: allow command message or not (UNUSED)
        '''
        self.token = kwargs.pop('token')
        self.server = kwargs.pop('server')
        self.wo_server = kwargs.pop('wo_server', None)
        self.account = kwargs.pop('account')
        self.instance = kwargs.pop('instance')
        self.clean_session = kwargs.pop('clean_session', False)
        self.use_ssl = kwargs.pop('use_ssl', False)
        self.pid = kwargs.pop('pid')
        self.logger = get_logger(logconsole=True)
        self.keepalive = kwargs.pop('keepalive', MSG_KEEPALIVE)
        self.qos = kwargs.pop('qos', MSG_QOS)
        # 使用这个参数来确定是否查询指令消息，以及是否执行
        self.allow_script = kwargs.pop('allow_script', False)
        self.appname = kwargs.pop('appname', 'Python client')

        # TESTING
        self.APP_KEY = kwargs.pop('APP_KEY')
        self.APP_SECRET = kwargs.pop('APP_SECRET')

        self.online = False
        self.mqtt_online = False

        if self.wo_server:
            self.wo_client = WoClient(
                self.wo_server,
                self.APP_KEY, self.APP_SECRET,
                account=self.account, instance=self.instance
            )
            self.wo_client.auth_with_token(self.token)

        self.message_client = MessageClient(
            self.server,
            self.APP_KEY, self.APP_SECRET,
            account=self.account, instance=self.instance
        )
        self.message_client.auth_with_token(self.token)

        self.COMMAND_CHANNEL = '<>'.join([COMMAND_CATEGORY, self.pid])
        self.subscriptions = {}

        self.logger.debug(u'消息客户端初始化完成')

    def start(self):
        conenction_data = self.message_client.message.connect()
        self.logger.debug(u'从消息中心获取到的连接凭证：%s', conenction_data)
        self.use_ssl = conenction_data.get(
            'use_ssl',
            ('https://' in conenction_data['tcp_broker'])
        )
        self.mqtt_host, self.mqtt_port = conenction_data['tcp_broker']\
            .replace('https://', '').replace('http://', '').split(':')
        self.mqtt_port = int(self.mqtt_port)
        self.userdata = conenction_data
        self.userdata.update({
            'user_id': self.pid,
            'account': self.account,
            'instance': self.instance,
        })
        self.__connect()

    def __connect(self):
        data = self.userdata
        data.update({'ref': self})
        self.client = mqtt.Client(client_id=self.userdata['client_id'],
                                  clean_session=self.clean_session,
                                  protocol=mqtt.MQTTv31)
        if self.use_ssl:
            self.client.tls_set(certifi.where())

        # Callbacks
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.on_subscribe = on_subscribe
        self.client.on_disconnect = on_disconnect

        self.client.user_data_set(data)
        self.client.will_set(topic=self.sys_topic,
                             payload=json.dumps(
                                 self.gen_connection_msg(self.userdata, False)
                             ),
                             qos=self.qos,
                             retain=False)
        self.logger.debug(u'last will 和连接相关数据设置完毕')
        try:
            self.client.connect(self.mqtt_host,
                                self.mqtt_port,
                                keepalive=self.keepalive)
            self.logger.debug(u'消息客户端已经发起连接，将进入网络循环')
            self.client.loop_forever()
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            self.online = self.mqtt_online = False
            self.logger.error(u'保持网络循环时出错：%s', extract_traceback())
            return self.reconnect()

    def reconnect(self):
        '''重连'''
        # 如果底层已经连接，并且应用层在线，直接返回
        # TESTING 如果底层已连接但应用层不在线，尝试发送上线消息
        # 如果底层未连接，清除自身相关参数并重新开始连接
        if self.online:
            self.logger.debug(u'已经在线，无需重连')
            return
        else:
            if self.mqtt_online:
                try:
                    self.logger.debug(u'尝试复用已有客户端进行重连')
                    self.__connect()
                except Exception:
                    self.logger.error(u'尝试复用已有客户端进行重连时失败：%s',
                                      extract_traceback())
                    self.start()
            else:
                self.logger.debug(u'尝试完全重新连接')
                self.start()

    def emit(self, evt, msg):
        '''触发一个时间（就是调用注册到这个事件的回调）'''
        context = MessageContext(
            rtc_client=self,
            message_client=self.message_client
        )
        callbacks = MSG_HANDLERS.get(evt, [])
        [call(msg, context) for call in callbacks if callable(call)]

    def handle_json_message(self, userdata, msg, topic=None):
        '''处理 JSON 消息'''
        # 连接消息：
        # 上线消息：已经连接
        # 下线消息：断开重连 / 连接失败（没有许可）
        # 业务消息：消息提示
        if not msg.get('event_data', None) or not msg.get('event_name'):
            return
        if msg.get('user_id', userdata['user_id']) != userdata['user_id']:
            return

        if msg['event_name'] == 'connection':
            # 严格区分不属于这个客户端的连接消息
            # 以下两种连接消息都属于这个客户端：
            # 客户端 ID 严格匹配，或消息是对所有客户端群发的（没有客户端 ID）
            if msg.get('client_id', userdata['client_id']) != userdata['client_id']:
                return
            if msg['event_data']['status'] == 'online':
                self.online = True
                self.logger.debug(u'消息客户端上线')
                return self.emit('connected', msg)
            elif msg['event_data']['status'] == 'offline':
                self.client.disconnect()
                self.logger.debug(u'消息客户端已经离线')
                return self.emit('disconnected', msg)
        return self.emit(msg['event_name'], msg)

    def gen_connection_msg(self, userdata, online):
        '''生成连接消息'''
        return {
            'event_name': 'connection',
            'account': userdata['account'],
            'client_id': userdata['client_id'],
            'user_id': userdata['user_id'],
            'instance': userdata['instance'],
            'event_data': {
                'status': 'online' if online else 'offline',
                'instances': userdata['topics'].keys(),
                'timestamp': time.time(),
                'appname': self.appname,
            }
        }

    def send_connection_msg(self, online, userdata=None):
        '''发送连接消息'''
        self.client.publish(
            topic=self.sys_topic,
            payload=json.dumps(
                self.gen_connection_msg(
                    self.client._userdata, online
                )
            ),
            qos=MSG_QOS, retain=False
        )
