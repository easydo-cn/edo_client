# -*- encoding:utf-8 -*-
import logging

from lru import LRUCacheDict
from client import OcClient, OrgClient, WoClient
from api import ContentApi
from edo_utils.config import get_app_url

try:
    from ztq_core import ha_delete, ha_keys, get_key, set_key
except ImportError:
    def ha_keys(system, *args, **kw):
        return []
    def ha_delete(system, *args, **kw):
        pass
    get_key = set_key = ha_delete

log = logging.getLogger(__name__)

OU_PREFIX = 'groups.tree.'
COMPANY_PREFIX = 'groups.company.'
JOB_PREFIX = 'groups.jobs.'
OLD_JOB_PREFIX = 'groups.job.'
USER_PREFIX = 'users.'
CLIENT_PREFIX = 'clients.'


def replace_prefix(users=[]):

    results = []
    for user in users:
        if user.startswith(OU_PREFIX):
            results.append('ou:%s' % user[len(OU_PREFIX):])
        elif user.startswith(COMPANY_PREFIX):
            results.append('company:%s' % user[len(COMPANY_PREFIX):])
        elif user.startswith(JOB_PREFIX):
            results.append('group:%s' % user[len(JOB_PREFIX):])
        elif user.startswith(OLD_JOB_PREFIX):
            results.append('group:%s' % user[len(OLD_JOB_PREFIX):])
        elif user.startswith(USER_PREFIX):
            results.append('person:%s' % user[len(USER_PREFIX):])
        elif user.startswith(CLIENT_PREFIX):
            results.append('person:%s' % user[len(CLIENT_PREFIX):])
        else:
            results.append('person:%s' % user)
            # raise ValueError, 'zopen.cacheorg.cacheorg.replace_prefix:ValueError:%s' % user

    return results


def remove_prefix(pid):
    if pid.startswith(OU_PREFIX):
        return pid[len(OU_PREFIX):]
    elif pid.startswith(COMPANY_PREFIX):
        return pid[len(COMPANY_PREFIX):]
    elif pid.startswith(JOB_PREFIX):
        return pid[len(JOB_PREFIX):]
    elif pid.startswith(USER_PREFIX):
        return pid[len(USER_PREFIX):]

    raise ValueError, 'zopen.cacheorg.cacheorg.remove_prefix:ValueError:%s' % pid


def add_prefix(object_type, user_name):
    if not user_name: return
    if object_type == 'ou':
        if ',' in user_name:
            return ','.join([add_prefix(object_type, x) for x in user_name.split(',')])
        else:
            return '%s%s' % (OU_PREFIX, user_name)
    elif object_type == 'group':
        return '%s%s' % (JOB_PREFIX, user_name)
    elif object_type == 'company':
        return '%s%s' % (COMPANY_PREFIX, user_name)
    elif object_type == 'person':
        return '%s%s' % (USER_PREFIX, user_name)


def DenyCacheKeysForMember(account, principal_id, parents='', children=''):
    # 个人的详细资料
    principalinfo_key = "pinfo:%s:%s.%s"
    # 用户所在的组的信息
    listusergroups_key = "gusers:%s:%s"
    # 组成员信息
    listgroupmembers_key = "gmembers:%s:%s:%s"
    listouonelevelmembersdetail_key = "oudetail:%s:%s:%s"
    listorgstructure_key = "orgstr:%s:%s"

    # 删除自身
    keys = []
    if principal_id.startswith('users.'):
        object_type = 'person'
        uid = principal_id.split('.', 1)[-1]
    elif principal_id.startswith('groups.jobs.'):
        object_type = 'group'
        uid = principal_id.split('.', 2)[-1]
    elif principal_id.startswith('groups.tree.'):
        object_type = 'ou'
        uid = principal_id.split('.', 2)[-1]
    elif principal_id.startswith('groups.company.'):
        object_type = 'company'
        uid = principal_id.split('.', 2)[-1]
    else:
        raise ValueError(
            "principal_id is not person、group、ou, %s" % principal_id)

    keys.append(principalinfo_key % (account, object_type, uid))
    keys.append(listorgstructure_key)
    # 部门添加
    if object_type != 'person':
        keys.append(listouonelevelmembersdetail_key %
                    (account, principal_id.split('.', 2)[-1], 'True'))
        keys.append(listouonelevelmembersdetail_key %
                    (account, principal_id.split('.', 2)[-1], 'False'))
        keys.append(listorgstructure_key %
                    (account, principal_id.split('.', 2)[-1]))
    # 删除父节点
    if parents:
        parents = replace_prefix(parents)
        keys.append(listusergroups_key % (account, uid))
        for group_id in parents:
            keys.append(listgroupmembers_key % (account, group_id, 'True'))
            keys.append(listgroupmembers_key % (account, group_id, 'False'))
            keys.append(listouonelevelmembersdetail_key %
                        (account, group_id.split(':')[-1], 'True'))
            keys.append(listouonelevelmembersdetail_key %
                        (account, group_id.split(':')[-1], 'False'))
            keys.append(listorgstructure_key %
                        (account, group_id.split(':')[-1]))

    # 删除子节点
    if children:
        keys.append(listgroupmembers_key % (account, replace_prefix([principal_id])[0], 'True'))
        keys.append(listgroupmembers_key % (account, replace_prefix([principal_id])[0], 'False'))
        for child in children:
            keys.append(principalinfo_key %
                        (account, 'person', child.split('.', 1)[-1]))
            keys.append(listusergroups_key %
                        (account, child.split('.', 1)[-1]))

    ha_delete('cache', *keys)


def DenyCacheKeysForInstance(account_name):
    ha_delete('cache', 'instanceinfo:%s' % (account_name))


oc_cache = LRUCacheDict(max_size=10000, expiration=24 * 3600, concurrent=True)
login_properties_cache = LRUCacheDict(expiration=120, concurrent=True)

class CachedOcClient(OcClient):

    def __init__(self, server_url, app_id, secret, account=None, instance=None, verify=None):
        OcClient.__init__(self, server_url, app_id, secret,
                          account=account, instance=instance, verify=verify)

    def get_token_info(self):
        """ 得到用户的token_info """
        token_info = None
        try:
            token_info = oc_cache[self.token_code]
        except KeyError:
            token_info = self.oauth.get_token_info()
            if token_info:
                oc_cache[self.token_code] = token_info
        return token_info

    def get_login_properties(self, account):
        try:
            data = login_properties_cache[account]
        except KeyError:
            data = self.account.get_login_properties(account)
            account_url = get_app_url('account', account=account)
            logo_url = data['login_box']['logo_url']
            bgimg_url = data['background']['image_url']
            if logo_url:
                data['login_box']['logo_url'] = account_url + logo_url
            if bgimg_url:
                data['background']['image_url'] = account_url + bgimg_url
            login_properties_cache[account] = data
        return data

class CachedOrgClient(OrgClient, OcClient):
    """ 支持缓存的admin接口 """

    def __init__(self, server_url, app_id, secret, account=None, instance=None, maxsize=5000, expire=120, verify=None):
        OrgClient.__init__(self, server_url, app_id, secret,
                           account=account, instance=instance, verify=verify)
        self.cache = LRUCacheDict(max_size=maxsize, expiration=expire, concurrent=True)

    def _get_cache(self, cache_key, skip_memcached=False):
        # 从内存中取
        if not skip_memcached and cache_key in self.cache:
            try:
                return self.cache[cache_key]
            except KeyError:
                pass

        # 从redis上取
        result = get_key(cache_key, 'cache_slave')
        if result is not None:
            self.cache[cache_key] = result
            return result

    def get_user_roles(self, user, account):
        """ 得到用户的角色"""
        key = "roles:%s:%s" % (account, user)
        try:
            roles = self.cache[key]
        except KeyError:
            roles = self.account.get_user_roles(user=user, account=account)
            self.cache[key] = roles
        return roles

    def refresh_cache(self, keys=[], mem_only=False):
        """ mem_only: 只清除内存缓存，方便测试 """
        if not keys:
            if not mem_only:
                del_keys = []
                for key_prefix in ('pinfo', 'gusers', 'gmembers', 'oudetail', 'orgstr'):
                    del_keys.extend(list(ha_keys('cache_slave', key_prefix + '*')))

                if del_keys:
                    ha_delete('cache', *del_keys)
            self.cache.clear()
            oc_cache.clear()
            login_properties_cache.clear()
        else:
            for info in keys:
                del_type = info.pop('type')
                if del_type == 'DeleteOrg':
                    DenyCacheKeysForMember(**info)
                elif del_type == 'DeleteInstance':
                    DenyCacheKeysForInstance(**info)

    def _getValueUseCache(self, cache_key, func, skip_cache=False, **params):
        """ 根据key从redis得到值，否则从rpc调用得到值并放入redis """

        # 从内存和redis上查找缓存
        cache = self._get_cache(cache_key, skip_cache)
        if cache:
            return cache

        # 从服务器上取 
        result = func(**params)
        if result is None:
            return None

        # 放入redis
        set_key(cache_key, result, 'cache')
        self.cache[cache_key] = result

        return result

    def get_objects_info(self, account, pids, skip_cache=False):
        """ 批量得到人员和组的信息 """
        users = []
        values = []
        for pid in pids:
            object_type, name = pid.split(':')
            key = "pinfo:%s:%s.%s" % (account, object_type, name)

            # 从内存和redis上查找缓存
            value = self._get_cache(key, skip_cache)
            if value is None:
                users.append(pid)
            else:
                values.append(value)

        if not users:
            return values

        infos = self.org.get_objects_info(account=account, objects=users)
        for info in infos:
            key = "pinfo:%s:%s.%s" % (account, info['object_type'], info['id'])
            self.cache[key] = info
            set_key(key, info, 'cache')
            values.append(info)
        return values

    def list_person_groups(self, account, user_id, skip_cache=False):
        key = "gusers:%s:%s" % (account, user_id)
        remote_groups = self._getValueUseCache(
            key, self.org.list_person_ougroups, person=user_id, account=account, skip_cache=skip_cache) or {}
        return remote_groups

    def get_ou_detail(self, account, ou_id, include_disabled=False, skip_cache=False):
        key = 'oudetail:%s:%s:%s' % (account, ou_id, str(include_disabled))
        return self._getValueUseCache(key, self.org.get_ou_detail, ou_id=ou_id, include_disabled=include_disabled, account=account, skip_cache=skip_cache)

    def list_groups_members(self, account, group_ids, skip_cache=False, include_disabled=False):
        """ 批量得到组的人员列表 """
        if isinstance(group_ids, basestring):
            group_ids = [group_ids]

        groups = []
        result = []
        for group_id in group_ids:
            key = "gmembers:%s:%s:%s" % (account, group_id, str(include_disabled))
            value = self._get_cache(key) if not skip_cache else None
            if value is None:
                groups.append(group_id)
            else:
                result.extend(value)
        if not groups:
            return list(set(result))

        for group in groups:
            g_type, g_id = group.split(':')
            if g_type == 'group':
                filters = {'ou': '', 'jobs': [g_id]}
            else:
                filters = {'ou': g_id}
            filters['object_type'] = 'person'
            filters['scope'] = 'subtree'
            filters['include_disabled'] = include_disabled
            size = 1000
            qs = self.org.search(account=account, batch_size=size, batch_start=0, **filters)
            count, persons = qs['count'], qs['result']
            g_value = []
            for person in persons:
                g_value.append(person['id'])
            # 分段搜索
            if count > len(persons):
                num = count / size
                if count % size:
                    num += 1
                for index in range(1, num):
                    qs = self.org.search(account=account, batch_size=size, batch_start=index*size, **filters)
                    count, persons = qs['count'], qs['result']
                    for person in persons:
                        g_value.append(person['id'])
            result.extend(g_value)
            # 添加缓存
            key = "gmembers:%s:%s:%s" % (account, group, str(include_disabled))
            self.cache[key] = g_value
            set_key(key, g_value, 'cache')

        return list(set(result))

    def list_org_structure(self, account, root='default', skip_cache=False, include_groups=True):
        key = "orgstr:%s:%s:%s" % (account, root, str(include_groups))
        org_structure = self._getValueUseCache(
            key, self.org.list_org_structure, account=account, root=root, skip_cache=skip_cache, include_groups=include_groups) or {}

        return org_structure

    def list_instances(self, account, application, skip_cache=False):
        key = "instanceinfo:%s" % (account)
        value = self._getValueUseCache(
            key, self.account.list_instances, account=account, application=application, skip_cache=skip_cache)
        return value


class CachedContentApi(ContentApi):
    '''
    A cached ContentApi class.
    Instances of this class actually use dict-like cache object passed in by caller.
    '''

    def __init__(self, *args, **kwargs):
        self._cache = kwargs.pop('cache')
        super(CachedContentApi, self).__init__(*args, **kwargs)

    def items(
        self, path='', uid='',
        fields=[], start=0, limit=1000, sort='-modified',
        account=None, instance=None
    ):
        account = account or self.account_name
        instance = instance or self.instance_name

        cache_key = u'items:{}|{}.{}.{}-l{}.{}.{}.{}'.format(
            path, uid, sorted(fields), start, limit, sort, account, instance
        )

        try:
            results = self._cache[cache_key]
            log.debug(u'"%s" hit cache', cache_key)
            return results
        except KeyError:
            log.debug(u'"%s" missed cache, fetch from live API', cache_key)
            self._cache[cache_key] = super(CachedContentApi, self).items(
                path=path, uid=uid,
                fields=fields, start=start, limit=limit, sort=sort,
                account=account, instance=instance
            )
            return self._cache[cache_key]

    def properties(
        self, path='', uid='',
        fields=[], settings=[],
        account=None, instance=None
    ):
        account = account or self.account_name
        instance = instance or self.instance_name

        cache_key = u'props:{}|{}.{}.{}.{}.{}'.format(
            path, uid, sorted(fields), sorted(settings), account, instance
        )

        try:
            results = self._cache[cache_key]
            log.debug(u'"%s" hit cache', cache_key)
            return results
        except KeyError:
            log.debug(u'"%s" missed cache, fetch from live API', cache_key)
            self._cache[cache_key] = super(CachedContentApi, self).properties(
                path=path, uid=uid,
                fields=fields, settings=settings,
                account=account, instance=instance
            )
            return self._cache[cache_key]


class CachedWoClient(WoClient):
    '''
    A cached WoClient class.
    '''

    def __init__(self, *args, **kwargs):
        self._cache = LRUCacheDict(
            max_size=kwargs.pop('maxsize', 10000),
            expiration=kwargs.pop('expiration', 60),
            concurrent=True
        )
        super(CachedWoClient, self).__init__(*args, **kwargs)

    @property
    def content(self):
        return CachedContentApi(
            self, self._access_token, self.refresh_hook,
            self.account_name, self.instance_name,
            cache=self._cache
        )
