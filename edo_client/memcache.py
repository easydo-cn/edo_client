#! coding=utf-8
import collections
from itertools import ifilterfalse

import time

"""
    内存式缓存:
    内部维护一个支持失效时间的字典，从字典取数据会判断是不是过期了。
    通过双链表实现LRU算法。

    @lru_cache(namespace='NAME', maxsize=20, expire=2)
    def f(x, y):
        return 3*x+y

    maxsize: 以参数为键值保存在一个内部维护的字典中，键值数量会小于maxsize
    expire : 秒为单位，过了多少秒这个键值就失效
"""

class Expire(dict):
    """支持timeout的dict"""
    def __init__(self, expire, *args, **kw):
        super(Expire, self).__init__(*args, **kw)
        self.expire = float(expire)

    def __getitem__(self, key):
        value, time_out= super(Expire, self).__getitem__(key)
        if time.time() > time_out:
            raise KeyError # 过期了，抛出KeyError，会自动取得新的value并保存
        else:
            return value

    def __setitem__(self, key, value):
        super(Expire, self).__setitem__(key, (value, time.time() + self.expire))

class Counter(dict):
    'Mapping where default values are zero'
    def __missing__(self, key):
        return 0

class LRUCache(object):
    """ """
    def __init__(self, maxsize=5000, expire=3600):
        self.maxsize = maxsize
        self.maxqueue = maxsize * 10
        self.cache = Expire(expire=expire) # mapping of args to results
        self.refcount = Counter()        # times each key is in the queue
        self.sentinel = object()         # marker for looping around the queue
        queue = self.queue = collections.deque() # order that keys have been used

        # lookup optimizations (ugly but fast)
        self.queue_append, self.queue_popleft = queue.append, queue.popleft
        self.queue_appendleft, self.queue_pop = queue.appendleft, queue.pop

    def clear(self):
        self.cache.clear()
        self.queue.clear()
        self.refcount.clear()

    def get(self, key):
        # record recent use of this key
        self.queue_append(key)
        self.refcount[key] += 1
        return self.cache[key] # raise KeyError if key not exists

    def put(self, key, value):
        #result = user_function(*args, **kwds)
        self.cache[key] = value

        # purge least recently used cache entry
        if len(self.cache) > self.maxsize:
            key = self.queue_popleft()
            self.refcount[key] -= 1
            while self.refcount[key]:
                key = self.queue_popleft()
                self.refcount[key] -= 1
            del self.cache[key], self.refcount[key]

        # periodically compact the queue by eliminating duplicate keys
        # while preserving order of most recent access
        if len(self.queue) > self.maxqueue:
            self.refcount.clear()
            self.queue_appendleft(self.sentinel)
            for key in ifilterfalse(self.refcount.__contains__,
                                    iter(self.queue_pop, self.sentinel)):
                self.queue_appendleft(key)
                self.refcount[key] = 1

__CACHE = {}
def lru_cache(namespace='default', maxsize=5000, expire=3600):
    '''Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    '''
    if namespace not in __CACHE:
        __CACHE[namespace] = LRUCache(maxsize, expire)
    return __CACHE[namespace]

if __name__ == '__main__':
    from random import choice

    def f(x, y):
        return 3*x+y

    cache = lru_cache(namespace='TEST', maxsize=100, expire=2)
    hits = misses = 0

    domain = range(10)
    for i in range(1000):
        key = (choice(domain), choice(domain))
        try:
            cache.get(key)
            hits += 1
        except:
            value = f(choice(domain), choice(domain))
            cache.put(key, value)
            misses += 1

    #time.sleep(3)
    #for i in range(1000):
    #    key = (choice(domain), choice(domain))
    #    try:
    #        cache.get(key)
    #        hits += 1
    #    except:
    #        value = f(choice(domain), choice(domain))
    #        cache.put(key, value)
    #        misses += 1

    print(hits, misses)
