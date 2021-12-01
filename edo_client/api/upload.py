# -*- coding: utf-8 -*-
import copy
import os
import base64
import hashlib
import httplib
import json
import logging
import sys

from .base import BaseApi
from .session_store import SessionStore
from ..error import ApiError, AbortUpload, UploadError

# Aliyun OSS support
import oss2
from .aliyun_oss import resumable_upload

log = logging.getLogger(__name__)


class UploadApi(BaseApi):
    '''
    Unified client interface for resumable uploading files / streams.
    '''

    tus_version = '1.0.0'  # This is only used for EDO UPLOAD service.

    def get_session_store(self, store=None):
        if store is None or not os.path.isdir(os.path.abspath(store)):
            return SessionStore(
                os.path.expanduser(
                    os.path.join('~', '.edo', 'upload_progress')
                )
            )
        else:
            return SessionStore(os.path.abspath(store))

    def get_session_key(self, fpath, upload_sign):
        '''
        Generate a session key based on:
        - absolute path of local file
        - upload_sign, which is a dict returned by WO
        - upload server address
        Notice: signcode and other one-time values in upload_sign is ignored.
        '''
        sign_copy = copy.deepcopy(upload_sign)
        for key in ('signcode', 'deadline', 'expire', 'maxsize', ):
            sign_copy.pop(key, None)

        return hashlib.md5(
            fpath + json.dumps(sign_copy, sort_keys=True) + self.client.api_host  # noqa
        ).hexdigest()

    def upload_aliyun_oss(
        self, fpath, upload_sign,
        store=None, on_progress=None,
        chunk_size=2**20
    ):
        '''
        Upload a local file to Aliyun OSS service.
        Please see docstring of .upload() for detailed documentation.
        Notice: This is an underlayer util function for Aliyun OSS service.
        '''
        # honor `store` value
        if store is None or not os.path.isdir(os.path.abspath(store)):
            store = os.path.expanduser(
                os.path.join('~', '.edo', 'aliyun_oss_upload_progress')
            ).decode(sys.getfilesystemencoding())
            if not os.path.exists(store):
                os.makedirs(store)
        store_root = os.path.dirname(store)
        store_dir = os.path.basename(store)
        store = oss2.ResumableStore(root=store_root, dir=store_dir)

        # Prepare callback function wrapper
        if callable(on_progress):
            def progress_callback(offset, fsize):
                try:
                    callable(on_progress) and on_progress(
                        fsize if offset is None else offset, fsize, fpath
                    )
                except AbortUpload:
                    log.debug(
                        u'Upload aborted by `on_progress` callback,'
                        u' %d bytes uploaded, local file: %s',
                        offset, fpath
                    )
                    raise
                except:
                    log.debug(
                        u'`on_progress` callback error after %s bytes uploaded',  # noqa
                        offset, exc_info=True
                    )
        else:
            progress_callback = None

        sts_auth = oss2.StsAuth(
            upload_sign['AccessKeyId'],
            upload_sign['AccessKeySecret'],
            upload_sign['SecurityToken']
        )
        bucket = oss2.Bucket(
            sts_auth, upload_sign['endpoint'], upload_sign['bucket_name']
        )

        # Prepare callback url and data
        # 阿里云的回调有特定格式需求，参考文档
        # https://help.aliyun.com/document_detail/32030.html
        callback = {
            'callbackUrl': upload_sign['callbackUrl'],
            'callbackBody': upload_sign['callbackBody'],
            'callbackBodyType': upload_sign['callbackBodyType'],
        }
        headers = {
            'x-oss-callback': base64.b64encode(json.dumps(callback).strip()),
        }
        # 如果申请上传时带了 hash，ticket 里也会有 hash，这个 hash 是文件内容的 MD5 散列值
        # 此时要把 md5 设置到阿里云 Object 的 meta 属性上。
        # 注意：阿里云分片上传，并不支持md5检验
        if 'hash' in upload_sign:
            # hash 这里是一个 hexdigest，需要转为 base64 编码的 digest
            # 参考 https://yq.aliyun.com/articles/27523
            headers['x-oss-meta-content-md5'] = base64.b64encode(upload_sign['hash'].decode('hex'))

        return resumable_upload(
            bucket,
            upload_sign['key'],  # mdfs_key
            fpath,  # local file path
            store=store,
            headers=headers,
            multipart_threshold=chunk_size,  # Or another reasonable size?
            part_size=chunk_size,
            num_threads=1,  # Single thread would be fine
            progress_callback=progress_callback
        )

    def upload(
        self, fpath, upload_sign,
        store=None, on_progress=None,
        chunk_size=2**20
    ):
        '''
        Upload a local file.
        Support:
            - EDO UPLAOD service.
            - Aliyun OSS service. (Under construction)
        Args:
            - fpath <string>: path of local file.
            - upload_sign <dict>: upload sign returned by
              WoClient.content.get_upload_signcode.
            - store <string>: which folder to store progress information to.
            - on_progress <callable>: a callable which will be called per chunk
            uploaded (`on_progress(uploaded_bytes, total_bytes, fpath)`).
            - chunk_size <int>: how many bytes a chunk contains, (each chunk
              is uploaded using a single HTTP request) defaults to 2MB.
        Returns: metadata of created new file / new revision of file.
        Notice:
            Upload progress information is saved to a hidden folder
              (~/.edo/upload_progress), and automatically deleted after
              uploading succeeds or fails. You can specify it via the
              `store` keyword arg.
        '''
        # Drop unused values
        upload_sign.pop('upload_server', None)

        # Identify upload service to use
        upload_service = upload_sign.get('upload_service', 'upload')
        if upload_service == 'aliyun_oss':
            # Upload directly to Aliyun OSS service
            result = self.upload_aliyun_oss(
                fpath, upload_sign,
                store=store, on_progress=on_progress,
                chunk_size=chunk_size
            )
            errcode = result.get("errcode", None)
            if errcode is not None and errcode != 0:
                raise ApiError(errcode, errcode, result.get("errmsg", ""))
            else:
                return result
        elif upload_service == 'upload':
            upload_sign.pop('upload_service', 'upload')
            # By default we'll use edo upload service

        # === 以下都是处理通过 upload 服务上传的逻辑 ===

        # upload 服务现在（2019.01.06）只能处理预先可确定大小的文件
        total_filesize = int(upload_sign['maxsize'])
        end = total_filesize - 1 if total_filesize > 0 else 0
        fsize = os.path.getsize(fpath)
        fname = os.path.basename(fpath)
        if fsize != total_filesize:
            log.warn(
                u'Expected to upload %dbytes via upload service, but current file size is %dbytes',
                total_filesize, fsize,
            )
            raise AbortUpload(421, 421, u'文件大小与预期不符')

        # Get any saved upload session from SessionStore
        if not callable(on_progress):
            on_progress = None
        store = self.get_session_store(store)

        if 'upload_server' in upload_sign:
            upload_sign.pop('upload_server', None)

        session_key = self.get_session_key(fpath, upload_sign)
        log.debug(
            u'Prepare to upload "%s" (%d bytes), progress stores in %s',
            fpath, fsize, store,
        )
        saved_session = store.load(session_key, default={})
        upload_session = saved_session.get('session', None)
        upload_mtime = saved_session.get('mtime', os.stat(fpath).st_mtime)
        log.debug(u'Previous saved upload session: %s', saved_session)
        if upload_mtime != os.stat(fpath).st_mtime:
            upload_session = None
            store.remove(session_key)

        # Validate saved upload session
        if upload_session is not None:
            try:
                uploaded = self.get_offset(upload_session)
                if uploaded is None:  # offset=None 表示已经全部上传完成
                    uploaded = total_filesize
                log.debug(u'Previous bytes uploaded: %s', uploaded)
                try:
                    callable(on_progress) and on_progress(uploaded, fsize, fpath)
                except AbortUpload:
                    log.debug(
                        u'Upload aborted by `on_progress` callback,'
                        u' %d bytes uploaded, local file: %s,'
                        u' upload session: %s.',
                        uploaded, fpath, upload_session
                    )
                    store.remove(session_key)
                    raise
            except ApiError as e:
                if e.code == 404:
                    log.info(u'Previous saved session expired or is invalid')
                    upload_session = None
                else:
                    raise

        # Create new upload session if necessary
        if upload_session is None:
            upload_session = self.create_session(
                fsize, filename=fname, **upload_sign
            )
            log.debug(
                u'Acquired new upload upload session: "%s"', upload_session
            )
            uploaded = self.get_offset(upload_session)
            log.debug(u'Newly created session uploaded %d bytes', uploaded or 0)
            _stat = os.stat(fpath)
            upload_mtime = _stat.st_mtime
            store.save(
                session_key, session=upload_session, mtime=upload_mtime, size=fsize
            )

        # Upload file content by chunk
        with open(fpath, 'rb') as rf:
            log.debug(u'File %s opened for reading', fpath)
            while uploaded <= end:
                rf.seek(uploaded, os.SEEK_SET)
                chunk = rf.read(chunk_size)
                _now_stat = os.stat(fpath)
                if upload_mtime != _now_stat.st_mtime or fsize != _now_stat.st_size:
                    log.debug(
                        u'File modified during uploading: %s => %s, aborting',
                        upload_mtime, os.stat(fpath).st_mtime
                    )
                    store.remove(session_key)
                    raise AbortUpload(419, 419, u'上传期间文件被修改')

                # 没有上传完，并且 os.stat 检查没有发现文件修改，但却无法从文件中读取到更多数据了
                if not chunk and uploaded < end:
                    log.warn(
                        u'Expected to upload %dbytes, but could not read any more data from offset %d of file %s. os.stat reported file size: initial %d / now %d.',
                        total_filesize, uploaded, fpath, fsize, _now_stat.st_size,
                    )
                    store.remove(session_key)
                    raise AbortUpload(420, 420, u'文件大小与预期不符')

                response = self.put_raw_chunk(upload_session, chunk, uploaded)
                uploaded = response.get('offset', total_filesize)  # offset=None 表示已经全部上传完成
                log.debug(u'Chunk put done, new offset %s', uploaded)
                try:
                    callable(on_progress) and on_progress(uploaded, fsize, fpath)
                except AbortUpload:
                    log.debug(
                        u'Upload aborted by `on_progress` callback,'
                        u' %d bytes uploaded, local file: %s,'
                        u' upload session: %s.',
                        uploaded, fpath, upload_session
                    )
                    raise
                except Exception:
                    log.debug(
                        u'`on_progress` callback error after %s bytes uploaded',  # noqa
                        uploaded, exc_info=True
                    )
                # 上传空文件是种特殊情况：uploaded=total_filesize=0
                if uploaded == total_filesize == 0:
                    log.debug(
                        u'Upload loop breaked by empty file exit, total filesize %dbytes, uploaded %dbytes, %dbytes on disk',
                        total_filesize, uploaded, fsize,
                    )
                    break

            log.debug(u'File upload finished')
            store.remove(session_key)
            log.debug(u'Session removed')
            return response

    def create_session(
        self, size, callback_url,
        deadline, expire, maxsize, signcode,
        filename=None, device='', prefix='', suffix='',
        hash=None, **others
    ):
        '''
        Create an UPLOAD session with given information.
        These information should be extracted from upload_signcode given by WO.
        Notice: This is an underlayer util function for UPLOAD service.
        '''
        metadata = dict(callback_url=callback_url)
        if filename:
            metadata['filename'] = filename

        headers = {
            'Tus-Resumable': self.tus_version,
            'Upload-Length': str(size),
            'Upload-Metadata': ','.join([
                '%s %s' % (k, base64.standard_b64encode(v))
                for k, v in metadata.items()
            ])
        }
        data = dict(
            deadline=deadline,
            expire=expire,
            maxsize=maxsize,
            signcode=signcode,
            device=device,
            prefix=prefix,
            suffix=suffix,
            hash=hash or '',
        )
        resp = self._post(
            '/api/v1/upload/upload_resumable',
            headers=headers, raw=True, **data
        )
        log.debug('create_session reponse headers: %s', resp.headers)
        if resp.status_code != httplib.CREATED:
            raise UploadError('%s, %s' % (resp.status_code, resp.reason))
        location = resp.headers.get('Location')
        if not location:
            raise UploadError('Missing header: Location')

        return location

    def put_raw_chunk(self, upload_path, data, offset):
        '''
        Send raw bytes `data` via HTTP PATCH request.
        Notice: This is an underlayer util function for UPLOAD service.
        '''
        checksum = hashlib.md5(data).digest()
        headers = {
            'Tus-Resumable': self.tus_version,
            'Content-Type': 'application/offset+octet-stream',
            'Upload-Offset': str(offset),
            'Upload-Checksum': 'md5 ' + base64.standard_b64encode(checksum)
        }
        resp = self._patch(upload_path, data=data, headers=headers, raw=True)
        # todo: 加入 https 支持
        # resp = requests.patch(upload_path, data=data, headers=headers)
        offset = resp.headers.get('upload-offset')
        if offset:
            return {'offset': int(offset)}
        else:
            data = resp.json()
            errcode = data.get('errcode', None)
            if errcode is not None and errcode != 0:
                raise ApiError(errcode, errcode, data.get('errmsg'))
            else:
                return data

    def put_chunk(self, upload_path, stream, offset, chunk_size=20*2**10):
        '''
        Send bytes read from `stream` to given `upload_path`.
        Notice: This is an underlayer util function for UPLOAD service.
        '''
        stream.seek(offset, os.SEEK_SET)
        data = stream.read(chunk_size)
        return self.put_raw_chunk(upload_path, data, offset)

    def get_offset(self, upload_path):
        '''
        Get the offset of your previous upload.
        Notice: This is an underlayer util function for UPLOAD service.
        '''
        headers = {
            'Tus-Resumable': self.tus_version,
        }
        resp = self._head(upload_path, headers=headers, raw=True)
        if resp.status_code != httplib.OK:
            raise UploadError('%s, %s' % (resp.status_code, resp.reason))
        return int(resp.headers.get('Upload-Offset'))
