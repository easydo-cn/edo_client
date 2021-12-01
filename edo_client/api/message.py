# -*- coding: utf-8 -*-
import json
from .base import BaseApi
from ..error import ApiError


class MessageV2Api(BaseApi):
    ''' Message V2 APIs '''

    def trigger_notify_event(
        self,
        category='default', to=None, exclude=None,
        event_name='notify', event_data=None, event_type='persistent',
        account=None, instance=None
    ):
        ''' 触发通知事件 '''
        event_data = event_data or {}
        to = to or []
        exclude = exclude or []
        account = account or self.account_name
        instance = instance or self.instance_name
        if event_type != 'persistent':
            event_type = 'transient'
        return self._post(
            '/api/v2/message/trigger_notify_event',
            account=account, instance=instance,
            to=json.dumps(to), exclude=json.dumps(exclude),
            event_name=event_name, event_data=json.dumps(event_data),
            event_type=event_type, category=category
        )

    def trigger_private_event(
        self,
        to=None, from_user=None,
        event_name='chat', event_data=None, event_type='persistent',
        account=None, instance=None
    ):
        ''' 触发私聊事件 '''
        event_data = event_data or {}
        account = account or self.account_name
        instance = instance or self.instance_name
        if event_type != 'persistent':
            event_type = 'transient'
        return self._post(
            '/api/v2/message/trigger_private_event',
            account=account, instance=instance,
            to=to, from_user=from_user,
            event_name=event_name, event_data=json.dumps(event_data),
            event_type=event_type
        )

    def trigger_group_event(
        self,
        group_id, exclude=None,
        event_name='chat', event_data=None, event_type='persistent',
        account=None, instance=None
    ):
        ''' 触发群组事件 '''
        event_data = event_data or {}
        exclude = exclude or []
        account = account or self.account_name
        instance = instance or self.instance_name
        if event_type != 'persistent':
            event_type = 'transient'
        return self._post(
            '/api/v2/message/trigger_group_event',
            account=account, instance=instance,
            event_name=event_name, event_data=json.dumps(event_data),
            event_type=event_type, group_id=group_id,
            exclude=json.dumps(exclude)
        )
    
    def update_routes(self, routes, account=None, instance=None):
        """ 更新路由表

        路由表字典格式

        {
            name: {
                token: token,
                endpoint: endpoint,
            }
        }

        :param routes: 路由表字典
        :type routes: Dict
        :param account:
        :param instance:
        """
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post('/api/v3/gateway/update_routes',
                          account=account,
                          instance=instance,
                          routes=json.dumps(routes))
    
    def send(self, msg_type, sender, event_type, event_name, event_data, 
             token=None, group_id=None, category=None, to=None, 
             account=None, instance=None):
        """ 发送外部网关消息
        """
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._post('/api/v3/gateway/send',
                          account=account, instance=instance, msg_type=msg_type,
                          sender=sender, event_type=event_type, event_name=event_name,
                          event_data=event_data, token=token, group_id=group_id,
                          category=category, to=to)



class MessageApi(BaseApi):
    def __init__(self, *args, **kwargs):
        self.client_id = kwargs.pop('client_id', None)
        super(MessageApi, self).__init__(*args, **kwargs)

    def get_secret(self, account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
            '/api/v1/admin/get_secret', account=account, instance=instance
        )

    def refresh_secret(self, account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
            '/api/v1/admin/refresh_secret',
            account=account, instance=instance
        )

    def connect(
        self, account=None, instance=None,
        username=None, timestamp=None, signature=None, instances=None
    ):
        '''
        Connect to MessageCenter, get personal topic & client id
        '''
        account = account or self.account_name
        instance = instance or self.instance_name
        instances = instances or [self.instance_name]
        client_id = self.client_id or None
        resp = self._post(
            '/api/v1/message/connect',
            account=account, instance=instance,
            client_id=client_id, username=username,
            timestamp=timestamp, signature=signature,
            instances=json.dumps(instances)
        )
        self.client_id = resp.get('client_id', self.client_id)
        return resp

    def trigger_event(
        self, user_id,
        event_name, event_data=None, account=None, instance=None
    ):
        '''
        在指定用户的所有端上触发同一个事件
        '''
        account = account or self.account_name
        instance = instance or self.instance_name
        event_data = event_data or {}
        return self._post(
            '/api/v1/message/trigger_event', user_id=user_id,
            event_name=event_name, event_data=json.dumps(event_data),
            account=account, instance=instance
        )

    def query(
        self, account=None, instance=None,
        event_name=None, channel_type=None, channel_name=None,
        time_start=None, time_end=None, limit=50
    ):
        '''
        Query history messages
        Args:
            instance: 消息区的实例号
            time_start 起始的消息 ID，默认为第一条未读消息 ID
            time_end 最末一条消息 ID，可选
            limit 消息数量限制，默认 50
        '''
        account = account or self.account_name
        instance = instance or self.instance_name
        if not all([event_name, channel_type, channel_name]):
            raise ApiError(400, 400, 'Missing parameter')
        return self._post(
            '/api/v1/message/query',
            account=account, instance=instance,
            channel_type=channel_type, channel_name=channel_name,
            time_start=time_start, time_end=time_end,
            event_name=event_name, limit=limit
        )

    def get(self, id, account=None, instance=None):
        '''Query exact one message by given message ID.
        '''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post('/api/v1/message/get', account=account, instance=instance, id=id)  # noqa E501

    def query_count(
        self, account=None, instance=None,
        event_name=None, channel_type=None, channel_name=None,
        time_start=None, time_end=None
    ):
        '''
        Query message count within specified time range
        Args:
            instance: 消息区的实例号
            time_start 起始的消息 ID，默认为第一条未读消息 ID
            time_end 最末一条消息 ID，可选
        '''
        account = account or self.account_name
        instance = instance or self.instance_name
        if not all([event_name, channel_type, channel_name]):
            raise ApiError(400, 400, 'Missing parameter')
        return self._post(
            '/api/v1/message/query_count',
            account=account, instance=instance,
            channel_type=channel_type, channel_name=channel_name,
            time_start=time_start, time_end=time_end,
            event_name=event_name
        )

    def unread_stat(self, account=None, instance=None):
        '''
        Get statics of unread messages
        Args:
            instance: 消息区的实例号
        '''
        account = account or self.account_name
        instance = instance or self.instance_name
        unreads = self._post(
            '/api/v1/message/unread_stat',
            account=account, instance=instance
        )
        unreads.pop('errcode', None)
        return unreads

    def mark_read(
        self, channel_type, timestamp,
        account=None, instance=None,
        group_id=None, category=None, to_user=None
    ):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/message/mark_read',
            account=account, instance=instance,
            channel_type=channel_type, timestamp=timestamp,
            group_id=group_id, category=category, to_user=to_user
        )

    def join_group(self, group_id, members=None, account=None, instance=None):
        '''
        Add members to given group.
        '''
        if not members:
            return
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/group/join',
            account=account, instance=instance,
            group_id=group_id, members=json.dumps(members)
        )

    def leave_group(self, group_id, members=None, account=None, instance=None):
        if not members:
            return
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/group/leave',
            account=account, instance=instance,
            group_id=group_id, members=json.dumps(members)
        )

    def update_group(
        self, group_id, members=None, title=None,
        account=None, instance=None, archived=False,
    ):
        if not members:
            return
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/group/update',
            account=account, instance=instance,
            group_id=group_id, title=title,
            members=json.dumps(members), archived=json.dumps(archived),
        )

    def remove_group(self, group_id, account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/group/remove',
            account=account, instance=instance,
            group_id=group_id
        )
