# -*- coding: utf-8 -*-
import io
import os
from shutil import move
import time
import json
import logging
import urlparse
from hashlib import md5

from requests import get as http_get

from .base import BaseApi
from ..error import AbortDownload, ApiError, DownloadError

log = logging.getLogger(__name__)


class ContentV2Api(BaseApi):

    def upload(
        self, path='', uid='',
        file=None, filename='',
        account=None, instance=None
    ):
        '''上传文件'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v2/content/upload',
            account=account, instance=instance,
            path=path, uid=uid,
            filename=filename, data=file
        )

    def upload_rev(
        self, path='', uid='',
        parent_rev='', file=None, filename='',
        account=None, instance=None,
        auto_fork=False, notify_subscribers=False
    ):
        '''上传文件'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v2/content/upload_rev',
            account=account, instance=instance,
            path=path, uid=uid,
            filename=filename, data=file,
            auto_fork=json.dumps(auto_fork),
            notify_subscribers=json.dumps(notify_subscribers)
        )

    def upload_attachment(
        self, path='', uid='',
        file=None, filename='',
        account=None, instance=None
    ):
        '''上传文件'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v2/content/upload_attachment',
            account=account, instance=instance,
            path=path, uid=uid,
            filename=filename, data=file
        )


class ContentApi(BaseApi):

    def properties(
        self, path='', uid='',
        fields=[], settings=[],
        account=None, instance=None
    ):
        ''' 取得文件或者文件夹的元数据'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/properties',
            fields=','.join(fields), settings=','.join(settings),
            account=account, instance=instance,
            uid=uid, path=path
        )

    def items(
        self, path='', uid='',
        fields=[], start=0, limit=1000, sort=None,
        account=None, instance=None
    ):
        ''' 获取文件夹下所有文件和文件夹的元数据'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/items',
            fields=','.join(fields), sort=sort,
            account=account, instance=instance,
            uid=uid, path=path,
            start=start, limit=limit
        )

    def lock(self, path='', uid='', account=None, instance=None, shared=False):
        ''' 将对象加锁'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/lock',
            account=account, instance=instance,
            uid=uid, path=path, shared=json.dumps(shared)
        )

    def unlock(
        self, path='', uid='', force=False,  account=None, instance=None,
        notify_subscribers=False
    ):
        ''' 将对象加锁'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/unlock',
            account=account, instance=instance,
            uid=uid, path=path, force=json.dumps(force),
            notify_subscribers=json.dumps(notify_subscribers)
        )

    def get_lock(self, path='', uid='',  account=None, instance=None):
        ''' 将对象加锁'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/get_lock',
            account=account, instance=instance, uid=uid, path=path
        )

    def search(
        self,
        queries=[], fields=[], start=0, limit=1000, sort='-modified', sort_field_type='',
        account=None, instance=None, include_history=False,
    ):
        ''' 获取文件夹下所有文件和文件夹的元数据'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/search',
            queries=json.dumps(queries), fields=','.join(fields),
            sort=sort, sort_field_type=sort_field_type, start=start, limit=limit,
            account=account, instance=instance, include_history=json.dumps(include_history),
        )

    def list_tag_groups(self, path='', uid='', account=None, instance=None):
        ''' 获取标签组设置信息'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/list_tag_groups',
            account=account, instance=instance, uid=uid, path=path
        )

    def acl_grant_role(
        self, path='', uid='', role='', pids=[], account=None, instance=None
    ):
        ''' 角色授权'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/acl_grant_role',
            role=role, pids=','.join(pids),
            account=account, instance=instance,
            uid=uid, path=path
        )

    def acl_deny_role(
        self, path='', uid='', role='', pids=[], account=None, instance=None
    ):
        ''' 禁用用户角色'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/acl_deny_role',
            role=role, pids=','.join(pids),
            account=account, instance=instance,
            uid=uid, path=path
        )

    def acl_unset_role(
        self, path='', uid='', role='', pids=[], account=None, instance=None
    ):
        ''' 取消用户角色'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/acl_unset_role',
            role=role, pids=','.join(pids),
            account=account, instance=instance,
            uid=uid, path=path
        )

    def delete(self, path='', uid='', account=None, instance=None):
        ''' 删除文件或文件夹'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/delete',
            account=account, instance=instance, uid=uid, path=path
        )

    def move(
        self, path='', uid='',
        to_uid='', to_path='', name='',
        account=None, instance=None
    ):
        ''' 移动文件或文件夹'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/move',
            account=account, instance=instance,
            uid=uid, path=path,
            to_uid=to_uid, to_path=to_path, name=name
        )

    def copy(
        self, path='', uid='',
        to_uid='', to_path='', name='',
        account=None, instance=None
    ):
        ''' 移动文件或文件夹'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/copy',
            account=account, instance=instance,
            uid=uid, path=path,
            to_uid=to_uid, to_path=to_path, name=name
        )

    def create_folder(
        self, path='', uid='',
        name='', description='', order_limit=300,
        account=None, instance=None
    ):
        ''' 创建文件夹'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/create_folder',
            account=account, instance=instance,
            uid=uid, path=path,
            name=name, description=description, order_limit=order_limit
        )

    def create_shortcut(
        self, path='', uid='',
        origin_path='', origin_uid=None, origin_rev='', name='',
        account=None, instance=None
    ):
        ''' 创建文件夹'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/create_shortcut',
            account=account, instance=instance, uid=uid, path=path,
            origin_path=origin_path, origin_uid=origin_uid,
            origin_rev=origin_rev, name=name
        )

    def upload(
        self, path='', uid='',
        file=None, filename='',
        account=None, instance=None
    ):
        '''上传文件'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._post(
            '/api/v1/content/upload',
            account=account, instance=instance,
            path=path, uid=uid,
            files={'file': (filename, file)}
        )

    def upload_rev(
        self, path='', uid='',
        file=None, parent_rev='',
        account=None, instance=None
    ):
        '''上传文件'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/content/upload_rev',
            account=account, instance=instance,
            path=path, uid=uid,
            parent_rev=parent_rev, files={'file': file}
        )

    def list_relation(
        self, path='', uid='', relation='', account=None, instance=None
    ):
        '''查找关系'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/content/list_relation',
            account=account, instance=instance,
            path=path, uid=uid, relation=relation
        )

    def list_attachments(self, path='', uid='', account=None, instance=None):
        '''查找关系'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/content/list_attachments',
            account=account, instance=instance, path=path, uid=uid
        )

    def set_relation(
        self, path='', uid='',
        relation='', target_uids=[], target_paths=[],
        account=None, instance=None
    ):
        '''设置关系'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v1/content/set_relation',
            account=account, instance=instance,
            path=path, uid=uid,
            relation=relation,
            target_uids=json.dumps(target_uids),
            target_paths=json.dumps(target_paths)
        )

    def __request_range(
        self, url, start=0, end=None, timeout=60, **kwargs
    ):
        '''
        Request a given range of file and return response along with length information.
        Notice:
            - This method will follow redirects, which might lead to URL
              provided by external services.
            - This util is built on top of requests.get
        Args:
            `url` is the URI of desired file, FQDN or IP address with full path
            `start` int to indicate which byte to start downloading
            `end` int / None to indicate which byte to stop downloading
            `block_size` size of data yield each time
            `timeout` int to indicate timeout of downloading connection
            `kwargs` parameters passed to requests.get
        Returns:
            `response` where:
                - `response` is the raw streamed response returned by requests.get
        Notice:
            HTTP Range headers are closed intervals, meaning they work like this: [start, end].
            Thus "Range: bytes=0-0" returns the first ONE byte, and so on.
            Ref doc: https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests
        '''
        # Prepare keyword arguments for requests.get
        kw = {
            'timeout': int(timeout),
            'params': kwargs,
            'stream': True,
        }
        # Deal with range header
        start = 0 if start < 0 else start
        end = '' if end is None else end
        kw['headers'] = {
            'Range': 'bytes={}-{}'.format(start, end),
            'Accept-Encoding': 'identity',  # disable any compression
        }
        log.debug(u'Requesting URL %s', url)

        # Fetch response
        response = http_get(url, **kw)
        log.debug(u'Request headers: %s', response.request.headers)
        log.debug(
            u'Got response from %s, status code: %s',
            response.url, response.status_code
        )
        log.debug(u'Response headers: %s', response.headers)

        if response.status_code == 416:
            if start == 0 and end == '':
                kw['headers'].pop('Range')
                return http_get(url, **kw)
            raise DownloadError(416, 416, u'请求范围不合要求')
        elif response.status_code not in (200, 206, ):
            try:
                data = response.json()
            except ValueError:
                data = {
                    'code': response.status_code,
                    'message': response.text,
                }
            raise ApiError(
                response.status_code, data['code'],
                {
                    404: '404 Not Found',
                }.get(response.status_code, data['message'])
            )

        # Check response range header
        range_value = response.headers.get('content-range', '')
        if not range_value:
            # 如果响应头里没有 content-range 这一个字段，而 content-length 字段为 0
            # 并且本次请求指定了从 0 开始，以及没有指定结尾，也就是下载整个文件，
            # 那么可以将 response 返回。
            length = int(response.headers.get('content-length', 0))
            if start == 0 and end == '' and length == 0:
                return response
        if not range_value.lower().startswith('bytes {0}-'.format(start)):
            raise DownloadError(response.status_code, 505, u'服务器不支持分块下载')

        return response

    def __get_response_length(self, response):
        '''
        Get content length in bytes from headers of given response.
        Notice: using the following order:
            - Get from Content-Range
            - Fallback to Content-Length
        '''
        # In the form of "bytes 0-1023/1024"
        range_str = response.headers.get('content-range', '').replace('bytes ', '')
        try:
            # Range string format: start-end/total
            range_str, total_size = range_str.split('/')
            start, end = range_str.split('-')

            start, end, total_size = int(start), int(end), int(total_size)
            if end - start != total_size - 1:
                raise ValueError(u'Range mismatch: {}'.format(range_str))
        except Exception:
            total_size = int(response.headers.get('content-length', '0'))
        finally:
            return total_size

    def get_data(self, url, offset=0, size=-1):
        '''
        Get raw bytes of given range from given URL.
        '''
        stream = io.BytesIO()
        end = None if size == -1 else (offset + size - 1)
        self.download_to_stream(stream, url=url, start=offset, end=end)
        stream.seek(0)
        return stream.read()

    def download_to_stream(
        self, stream, url=None,
        resumable=True, retry=10,
        start=0, end=None, calc_hash=False,
        on_progress=None, **others
    ):
        '''
        Download file content into given stream
        Args:
          - stream: 供写入数据的流对象
          - url: 下载地址
          - resumable: 是否使用断点下载
          - retry: 对网络错误的重试次数
          - start: 从何处开始下载。即首个字节的位置。
          - end: 到何处结束下载。即最后一个字节的位置。
          - calc_hash: 是否在下载的同时计算 MD5 hash
          - on_progress: 回调函数，每下载一定数据调用一次。func(downloaded, total)
        Notice:
            - 外部调用者需要自行负责 stream 对象的关闭。这个方法不会修改 stream 的状态。
            - 下载范围是闭区间 [start, end]，亦即下载的字节包括 start 和 end。
            - 对于 ApiError 不会进行重试。
        '''
        # Backward compatability issue
        url = url or self.get_download_url(**others)
        filename = getattr(stream, 'name', None)

        # 确定服务端文件的实际总大小
        log.debug(u'Sending a request to detect file size')
        if resumable:
            response = self.__request_range(url)
        else:
            response = http_get(url, stream=True)
        total_size = self.__get_response_length(response)
        log.debug(u'Detected file size: %d bytes', total_size)

        # 注意：因为传入的 end 可能超出实际文件大小，这里需要做个修正，如果超出就以服务端实际文件大小为准
        if end is None or end >= total_size:
            end = total_size - 1
            log.debug(u'Request range adjusted to [%d, %d]', start, end)

        def progress_callback(offset, total):
            if callable(on_progress):
                try:
                    on_progress(offset, total, filename=filename)
                except AbortDownload:
                    log.debug(u'[Download callback] cancelled downloading')
                    raise
                except Exception:
                    log.debug(u'[Download callback] erred', exc_info=True)

        # end == -1: 说明下载的是空文件
        if -1 < end < start:
            raise ValueError(u'`end` must >= `start` ({} !>= {})'.format(end, start))  # noqa E501

        # (Optional) Init hash object
        if calc_hash:
            hash_obj = md5()
            stream.seek(0)
            hash_obj.update(stream.read())

        # Seek to the end of stream
        stream.seek(0, os.SEEK_END)

        # 首次回调（尚未开始下载）
        downloaded = start
        log.debug(u'Call download callback the 1st time at %s/%s', downloaded, total_size)
        progress_callback(downloaded, total_size)

        # 需要下载的总长
        download_size = total_size - start  # 共需要下载的大小，可能等于或小于文件总大小
        log.debug(
            u'Requested to download range %s-%s (%s bytes in total) to stream',
            start, end, download_size,
        )

        while downloaded <= end:
            log.debug(u'Connection cursor at %s, opening new connection', downloaded)  # noqa E501
            if resumable:
                response = self.__request_range(url, start=downloaded, end=end)
            else:
                response = http_get(url, stream=True)

            try:
                # Iterate and write chunks into stream
                bytes_per_callback = 2 ** 20  # Call callback every 1MB
                flushed_chunk_length = 0
                # First callback
                for chunk in response.iter_content(4096):
                    stream.write(chunk)
                    stream.flush()
                    if calc_hash:
                        hash_obj.update(chunk)
                    flushed_chunk_length += len(chunk)
                    downloaded += len(chunk)
                    if flushed_chunk_length > bytes_per_callback:
                        flushed_chunk_length = 0
                        log.debug(u'Call download callback at %s/%s', downloaded, total_size)
                        progress_callback(downloaded, total_size)
                log.debug(u'Content iterating done, connection closed')
            except DownloadError as e:
                log.debug(
                    u'Encountered DownloadError during downloading, code: %s',
                    e.code, exc_info=True
                )
                # Should we code 416 too?
                if e.code in (505,):
                    # Redownload with none-resumable parameters
                    if resumable and start == 0:
                        stream.seek(0)
                        stream.truncate()
                        stream.flush()
                        return self.download_to_stream(
                            stream, url=url,
                            resumable=False, retry=retry,
                            calc_hash=calc_hash, on_progress=on_progress,
                            **others
                        )
                raise
            except (AbortDownload, ApiError):
                raise
            except Exception:
                log.debug(
                    u'Exception during downloading, remaining retry count: %s',
                    retry, exc_info=True
                )
                # Retry for `retry` times, raise if exceeded
                retry -= 1
                if retry < 0:
                    raise
                time.sleep(10 / (retry + 1))
                continue

        # Final callback
        log.debug(u'Call download callback the last time at %s/%s', downloaded, total_size)
        progress_callback(downloaded, total_size)

        # Downloaded successfully
        if calc_hash and hash_obj:
            return {'hash': hash_obj.hexdigest()}
        else:
            return {}

    def download_to_file(
        self, destination, url=None,
        resumable=True, retry=10,
        tempfilepath=None, calc_hash=False,
        on_progress=None, **others
    ):
        '''
        Download a file by `uid` or `path`
        Args:
          - destination: 文件的本地路径
          - url: 下载地址
          - resumable: 是否使用断点下载
          - retry: 对网络错误的重试次数
          - tempfilepath: 临时文件存放位置，不指定则使用同目录下的 .目标文件名
          - calc_hash: 是否在下载的同时计算 MD5 hash
          - on_progress: 回调函数，每下载一定数据调用一次。func(download, total)
        Notice:
            - Internally this opens the `tempfilepath`
              and calls `download_to_stream` to write into it.
            - This method will take care of opened file object.
            - 对于 ApiError 不会进行重试。
        '''
        # Backward compatability issue
        url = url or self.get_download_url(**others)

        if not tempfilepath:
            dirname = os.path.dirname(destination)
            basename = os.path.basename(destination)
            tempfilepath = os.path.join(dirname, '.{}'.format(basename))

        # Open tempfile for writing
        open_mode = 'ab+' if os.path.isfile(tempfilepath) else 'wb+'
        stream = open(tempfilepath, open_mode)

        # Download into tempfile stream
        try:
            returned = self.download_to_stream(
                stream, url,
                resumable=resumable, retry=retry,
                calc_hash=calc_hash, on_progress=on_progress
            )
        except Exception:
            stream.close()
            os.remove(tempfilepath)
            raise
        else:
            stream.close()
            move(tempfilepath, destination)
            return returned

    def __raise_error_from_response(self, response):
        '''
        Raise ApiError based on given requests.model.Response object.
        Notice on internal logic:
        - Try parsing JSON data from given response;
        - If JSON data available, raise ApiError with its `code` and `message`;
        - If not, raise ApiError with status code of response;
          - status code < 400 =>  normal, do nothing;
          - status code in [400, 500) => client error;
          - status code >= 500 => server error;
        '''
        try:
            data = response.json()
        except ValueError:
            messages = {
                404: u'404 Not Found',
            }
            status_code = response.status_code
            if status_code < 400:
                return
            elif 400 <= status_code < 500:
                raise ApiError(
                    status_code,
                    status_code,
                    messages.get(response.status_code, u'客户端未知错误')
                )
            elif status_code >= 500:
                raise ApiError(
                    status_code,
                    status_code,
                    messages.get(response.status_code, u'服务端未知错误')
                )
        else:
            raise ApiError(response.status_code, data['code'], data['message'])

    def get_download_url(
        self, uid=None, path=None, revision=None,
        account=None, instance=None, mime='', subfile='',
        expires_time=None, disposition=None
    ):
        '''
        Get direct download link from EDO system.
        '''
        download_api_endpoint = '/api/v1/content/download'
        dlink_response = http_get(
            self.client.api_host + download_api_endpoint,
            params=dict(
                uid=uid,
                mime=mime,
                subfile=subfile,
                path=path,
                revision=revision,
                expires_time=expires_time,
                disposition=disposition,
                account=account or self.account_name,
                instance=instance or self.instance_name
            ),
            allow_redirects=False,
            headers={
                # Auth header
                'Authorization': 'Bearer {}'.format(self.client.token_code)
            }
        )
        log.debug(u'Requesting download URL from %s', dlink_response.url)
        # Check for status code and raise error if necessary
        # Desired status code is 302
        if dlink_response.status_code != 302:
            # Server already raised the error
            if dlink_response.status_code >= 400:
                self.__raise_error_from_response(dlink_response)
            elif dlink_response.status_code < 302\
                    or 'Location' not in dlink_response.headers:
                # We don't want this status code, treat it as error
                raise ApiError(
                    dlink_response.status_code,
                    400,
                    u'无法获取文件下载地址'
                )

        # dlink response is a 302 redirect, get link from Location header
        url = dlink_response.headers['Location']
        log.debug(u'Got download URL: %s', url)
        return url

    def download(
        self, dst_path=None, stream=None,
        retry=10, calc_hash=False, tmppath=None,
        resumable=True, uid=None, path=None, revision=None,
        account=None, instance=None, mime='', subfile='',
        on_progress=None
        # FIXME we should group the parameter list like this:
        # self, account=None, instance=None,
        # revision=None, path=None, uid=None, subfile=None, mime=None,
        # resumable=True, retry=10,
        # dst_path=None, tmppath=None,
        # stream=None, calc_hash=False
    ):
        '''
        Download a file by `uid` or `path`, to `dst_path` or `stream`
        Args:
          - dst_path: 如果下载文件到本地，通过这个参数指定文件的本地路径。与 stream 参数二选一
          - stream: 如果下载文件到流对象中，通过这个参数指定流。与 dst_path 参数二选一
          - retry: 对网络错误的重试次数
          - calc_hash: 是否在下载的同时计算 MD5 hash
          - tmppath: 临时文件的存放位置。仅在传递 dst_path 时有效。不指定则使用 .文件名.uid.revision
          - resumable: 是否使用断点下载
          - uid: 要下载的文件的 uid，与 path 参数二选一
          - path: 要下载的文件的服务端 path，与 uid 参数二选一
          - revision: 要下载的文件的版本号
          - account: 文件所在站点的 account
          - instance: 文件所在站点 ID
          - mime: 要下载哪种 MIME 的转换文件。不指定则下载原始文件
          - subfile: 要下载哪个子文件。不指定则下载主文件
          - on_progress: 回调函数，每下载一定数据调用一次。func(downloaded, total)
        Notice:
        - This method does two things:
          - Get the direct download URL from EDO system;
          - Download from the URL into given file path or stream;
          - 对于 ApiError 不会进行重试
        '''
        # Prepare & check arguments
        # TODO we should really use these human-readable names as parameters
        destination = dst_path
        tempfilepath = tmppath
        if stream is None and destination is None:
            raise DownloadError(
                400, 400, u'destination 和 stream 至少指定一个'
            )

        # Get direct download link
        direct_download_link = self.get_download_url(
            uid=uid, path=path, revision=revision,
            account=account, instance=instance,
            mime=mime, subfile=subfile
        )
        # Download into stream or file
        if stream:
            return self.download_to_stream(
                stream, url=direct_download_link,
                resumable=resumable, retry=retry,
                start=0, end=None, calc_hash=calc_hash,
                on_progress=on_progress
            )
        else:
            # Get tempfile path
            if not tempfilepath:
                basepath, extension = os.path.split(destination)
                tempfilepath = os.path.join(
                    basepath,
                    '.{}.{}.{}'.format(extension, uid, revision or '')
                )

            return self.download_to_file(
                destination, url=direct_download_link,
                resumable=resumable, retry=retry,
                tempfilepath=tempfilepath, calc_hash=calc_hash,
                on_progress=on_progress
            )

    def download_shell_script(self, name, account=None, instance=None):
        return self._get(
            '/api/v1/content/download_shell_script',
            account=account or self.account_name,
            instance=instance or self.instance_name,
            name=name
        )

    def view_url(self, path='', uid='', account=None, instance=None):
        '''下载文件'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
            '/api/v1/content/view_url',
            account=account, instance=instance, path=path, uid=uid
        )

    def assistent_info(self, account=None, instance=None):
        '''下载文件'''
        account = account or self.account_name
        instance = instance or self.instance_name

        resp = self._get(
            '/api/v1/content/assistent_info',
            raw=True, account=account, instance=instance
        )
        info = resp.json()
        for i in info.values():
            if isinstance(i, dict) and 'filename' in i:
                i['url'] = urlparse.urljoin(resp.url, './%s' % i['filename'])

        return info

    def notify(
        self, account=None, instance=None,
        path='', uid='', from_pid='', action='',
        body='', title='', to_pids=[], exclude_me=True, excldue_pids=[],
        attachments=None, methods=None,
        title_msg_id='', body_msg_id='',
        title_msg_mapping=None, body_msg_mapping=None
    ):
        '''通知接口'''
        account = account or self.account_name
        instance = instance or self.instance_name
        attachments = attachments or []
        methods = methods or []
        title_msg_mapping = title_msg_mapping or {}
        body_msg_mapping = body_msg_mapping or {}

        return self._get(
            '/api/v1/content/notify',
            account=account, instance=instance,
            path=path, uid=uid, action=action,
            body=body, title=title,
            title_msg_id=title_msg_id, body_msg_id=body_msg_id,
            title_msg_mapping=json.dumps(title_msg_mapping),
            body_msg_mapping=json.dumps(body_msg_mapping),
            from_pid=from_pid, to_pids=','.join(to_pids),
            exclude_me=json.dumps(exclude_me),
            excldue_pids=','.join(excldue_pids),
            attachments=','.join([str(a) for a in attachments]),
            methods=','.join(methods)
        )

    def update_properties(
        self, path='', uid='',
        fields={}, settings={},
        account=None, instance=None, trigger_update=False
    ):
        '''更新metadata'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
            '/api/v1/content/update_properties',
            account=account, instance=instance,
            path=path, uid=uid,
            fields=json.dumps(fields), settings=json.dumps(settings),
            trigger_update=json.dumps(trigger_update)
        )

    def new_mdset(
        self, path='', uid='', mdset='', account=None, instance=None
    ):
        '''更新metadata'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
            '/api/v1/content/new_mdset',
            account=account, instance=instance,
            path=path, uid=uid, mdset=mdset
        )

    def remove_mdset(
        self, path='', uid='', mdset='', account=None, instance=None
    ):
        '''更新metadata'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
            '/api/v1/content/remove_mdset',
            account=account, instance=instance,
            path=path, uid=uid, mdset=mdset
        )

    def set_state(
        self, path='', uid='',
        state='', do_check=False,
        account=None, instance=None
    ):
        '''更新metadata'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
            '/api/v1/content/set_state',
            account=account, instance=instance,
            path=path, uid=uid,
            state=state, do_check=json.dumps(do_check)
        )

    def revision_ids(
        self, path='', uid='', include_temp=True, account=None, instance=None
    ):
        ''' 取得文件的历史版本清单'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/revision_ids',
            include_temp=json.dumps(include_temp),
            account=account, instance=instance,
            uid=uid, path=path
        )

    def revision_info(
        self, path='', uid='', revision='', account=None, instance=None
    ):
        ''' 取得文件版本信息'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/revision_info',
            account=account, instance=instance,
            uid=uid, path=path, revision=revision
        )

    def revision_tag(
        self, path='', uid='',
        revision='', major_version='', minor_version='', comment='',
        account=None, instance=None
    ):
        '''文件定版'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/revision_tag',
            revision=revision,
            major_version=major_version,
            minor_version=minor_version,
            comment=comment,
            account=account, instance=instance,
            uid=uid, path=path
        )

    def revision_remove(
        self, path='', uid='', revision='', account=None, instance=None
    ):
        '''删除版本'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/revision_remove',
            account=account, instance=instance,
            uid=uid, path=path, revision=revision
        )

    def submit_mdset(
        self, path='', uid='', mdset='', data={}, account=None, instance=None
    ):
        '''删除版本'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/submit_mdset',
            mdset=mdset, data=json.dumps(data),
            account=account, instance=instance,
            uid=uid, path=path
        )

    def submit_md(self, path='', uid='', data={}, account=None, instance=None):
        '''删除版本'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/submit_md',
            data=json.dumps(data),
            account=account, instance=instance,
            uid=uid, path=path
        )

    def add_dataitem(
        self, path='', uid='', data={}, name='', account=None, instance=None
    ):
        '''add the dataitem'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/add_dataitem',
            data=json.dumps(data), name=name,
            account=account, instance=instance,
            uid=uid, path=path
        )

    def action_workitem(
        self, path='', uid='',
        data={}, workitem_name='', action_name='',
        account=None, instance=None
    ):
        '''删除版本'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/action_workitem',
            workitem_name=workitem_name,
            action_name=action_name,
            data=json.dumps(data),
            account=account, instance=instance,
            uid=uid, path=path
        )

    def get_workitem(
        self, path='', uid='', workitem_name='', account=None, instance=None
    ):
        '''删除版本'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/get_workitem',
            workitem_name=workitem_name,
            account=account, instance=instance,
            uid=uid, path=path
        )

    def workflow_inputs(self, path='', uid='', account=None, instance=None):
        '''删除版本'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/workflow_inputs',
            account=account, instance=instance,
            uid=uid, path=path
        )

    def workitems(
        self, path='', uid='', pid='', stati='', account=None, instance=None
    ):
        '''删除版本'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
            '/api/v1/content/workitems',
            pid=pid, stati=stati,
            account=account, instance=instance,
            uid=uid, path=path
        )

    def get_site_public_key(self, account=None, instance=None):
        '''获取站点公钥'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/get_site_public_key',
            account=account, instance=instance
        )

    def get_member_public_key(self, member=None, account=None, instance=None):
        '''获取成员公钥'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/get_member_public_key',
            member=member, account=account, instance=instance
        )

    def get_my_private_key(self, account=None, instance=None):
        '''获取自己的私钥'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/get_my_private_key',
            account=account, instance=instance
        )

    def gen_download_certification(
        self, path='', uid='', account=None, instance=None
    ):
        '''生成下载证书'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/gen_download_certification',
            account=account, instance=instance, uid=uid, path=path
        )

    def get_upload_ticket(
        self, path='', uid='',
        filename='', parent_rev=None,
        expire=60*60*24*2, maxsize=1024*1024*1024*1024,
        account=None, instance=None,
        auto_fork=False, notify_subscribers=False, setprivate=False,
        hash=None,
    ):
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/get_upload_ticket',
            account=account, instance=instance,
            uid=uid, path=path,
            parent_rev=parent_rev, expire=expire, maxsize=maxsize,
            filename=filename, auto_fork=json.dumps(auto_fork),
            notify_subscribers=json.dumps(notify_subscribers),
            setprivate=json.dumps(setprivate), hash=hash,
        )

    get_upload_signcode = get_upload_ticket

    def renew_upload_ticket(
        self, path='', uid='',
        filename='', parent_rev=None,
        expire=60*60*24*2, maxsize=1024*1024*1024*1024,
        account=None, instance=None,
        auto_fork=False, notify_subscribers=False
    ):
        '''Renew upload ticket'''
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/renew_upload_ticket',
            account=account, instance=instance,
            uid=uid, path=path,
            parent_rev=parent_rev, expire=expire, maxsize=maxsize,
            filename=filename, auto_fork=json.dumps(auto_fork),
            notify_subscribers=json.dumps(notify_subscribers)
        )

    def ping(self, account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/ping', account=account, instance=instance
        )

    def list_api_urls(self, account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v1/content/list_api_urls', account=account, instance=instance
        )


class ContentV3Api(BaseApi):

    def upload(
        self, path='', uid='',
        file=None, filename='',
        account=None, instance=None
    ):
        '''上传文件'''
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._post(
            '/api/v3/content/upload',
            account=account, instance=instance,
            path=path, uid=uid,
            filename=filename, data=file
        )

    def add_favorite(self, path='', uid='', account=None, instance=None, title=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get('/api/v3/content/add_favorite', path=path, uid=uid, account=account, instance=instance, title=title)

    def remove_favorite(self, path='', uid='', account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get('/api/v3/content/remove_favorite', path=path, uid=uid, account=account, instance=instance)

    def add_subscribe(self, path='', uid='', account=None, instance=None, notify_methods=None):
        account = account or self.account_name
        instance = instance or self.instance_name

        if notify_methods:
            notify_methods = json.dumps(notify_methods)

        return self._get('/api/v3/content/add_subscribe', path=path, uid=uid, account=account, instance=instance, notify_methods=notify_methods)

    def remove_subscribe(self, path='', uid='', account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get('/api/v3/content/remove_subscribe', path=path, uid=uid, account=account, instance=instance)

    def add_comment(self, body, path='', uid='', account=None, instance=None, attachments=None, notify=True):
        account = account or self.account_name
        instance = instance or self.instance_name
        if attachments:
            attachments = json.dumps(attachments)
        else:
            attachments = json.dumps([])

        return self._get(
            '/api/v3/content/add_comment',
            path=path, uid=uid, account=account, instance=instance,
            body=body, attachments=attachments, notify=json.dumps(notify)
        )

    def remove_comment(self, comment_id, path='', uid='', account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get(
                '/api/v3/content/remove_comment',
                path=path, uid=uid, account=account, instance=instance, comment_id=comment_id)

    def search_comment(self, path='', uid='', account=None, instance=None, author=None, text=None, start=None, end=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        author = json.dumps(author)

        return self._get(
                '/api/v3/content/search_comment',
                path=path, uid=uid, account=account, instance=instance, author=author, text=text, start=start, end=end)

    def share(self, pids, notify_methods, permission=None, path='', uid='', account=None, instance=None, message='', subscribe=True):
        account = account or self.account_name
        instance = instance or self.instance_name
        pids = json.dumps(pids)
        notify_methods = json.dumps(notify_methods)

        return self._get(
            '/api/v3/content/share',
            path=path, uid=uid, account=account, instance=instance, pids=pids, notify_methods=notify_methods,
            permission=permission, message=message, subscribe=json.dumps(subscribe)
        )

    def query_logs(
            self, action, path='', uid='', account=None, instance=None, start=None, end=None, text=None, principal_id=None,
            person=None, batch_start=0, size=20):
        account = account or self.account_name
        instance = instance or self.instance_name
        action = json.dumps(action)
        return self._get(
            '/api/v3/content/query_logs',
            path=path, uid=uid, account=account, instance=instance, action=action, start=start,
            end=end, text=text, principal_id=principal_id, person=person, batch_start=batch_start, size=size)

    def search_workitems(
            self, path='', uid='', account=None, instance=None, queries=None, start=0, size=50,
            limit=1000, sort='-modified', fields=''):
        account = account or self.account_name
        instance = instance or self.instance_name
        queries = json.dumps(queries)
        return self._get(
            '/api/v3/content/search_workitems',
            path=path, uid=uid, account=account, instance=instance, queries=queries, start=start, size=size,
            limit=limit, sort=sort, fields=fields)

    def check_permission(self, permission_id, path='', uid='', account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name
        return self._get('/api/v3/content/check_permission',
            permission_id=permission_id, path=path, uid=uid, account=account, instance=instance)

    def start_workflow(self, path='', uid='', workflow='', account=None, instance=None):
        account = account or self.account_name
        instance = instance or self.instance_name

        return self._get(
            '/api/v3/content/start_workflow',
            path=path, uid=uid, account=account, instance=instance, workflow=workflow)
