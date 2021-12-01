#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Monkey patch oss2 library.
'''
import functools
import json
import logging
import os

import oss2
from oss2 import defaults
from oss2.compat import to_unicode
from oss2.exceptions import ServerError
from oss2.resumable import _ResumableUploader
from oss2.task_queue import TaskQueue
from oss2.utils import SizedFileAdapter
from oss2.models import PartInfo

from ..error import UploadError, AbortUpload, UploadTokenExpired

log = logging.getLogger(__name__)


# Notice: as of 2016.12.20, the util class oss2.resumable._ResumableUploader
# does not return any response, making it useless in scenarios where
# callback headers are set and response from application server is expected.
# This is just an ugly monkey patch. They're using too many private methods. :(
def _patched_upload(self):
    self._ResumableUploader__load_record()

    parts_to_upload = self._ResumableUploader__get_parts_to_upload(
        self._ResumableUploader__finished_parts
    )
    parts_to_upload = sorted(parts_to_upload, key=lambda p: p.part_number)

    q = TaskQueue(
        functools.partial(
            self._ResumableUploader__producer, parts_to_upload=parts_to_upload
        ),
        [
            self._ResumableUploader__consumer
        ] * self._ResumableUploader__num_threads
    )
    try:
        q.run()
    except ServerError as e:
        if e.status == 403 and e.details.get('Code', '') == 'SecurityTokenExpired':
            raise UploadTokenExpired()
        else:
            raise

    self._report_progress(self.size)

    # callback headers are required for OSS callback in
    # `complete_mulripart_upload` API call.
    resp = self.bucket.complete_multipart_upload(
        self.key,
        self._ResumableUploader__upload_id,
        self._ResumableUploader__finished_parts,
        headers=self._ResumableUploader__headers
    )
    self._del_record()
    return resp


def _patched__upload_part(self, part):
    with open(to_unicode(self.filename), 'rb') as f:
        self._report_progress(self._ResumableUploader__finished_size)
        f.seek(part.start, os.SEEK_SET)
        _now_stat = os.stat(to_unicode(self.filename))
        if self._ResumableUploader__mtime != _now_stat.st_mtime or self.size != _now_stat.st_size:  # noqa E501
            raise AbortUpload(419, 419, u'上传期间文件被修改')
        result = self.bucket.upload_part(
            self.key, self._ResumableUploader__upload_id, part.part_number,
            SizedFileAdapter(f, part.size)
        )
        self._ResumableUploader__finish_part(
            PartInfo(part.part_number, result.etag, size=part.size)
        )


_ResumableUploader.upload = _patched_upload
_ResumableUploader._ResumableUploader__upload_part = _patched__upload_part
oss2.resumable._ResumableUploader.upload = _patched_upload
oss2.resumable._ResumableUploader._ResumableUploader__upload_part = _patched__upload_part  # noqa E501


def resumable_upload(bucket, key, filename,
                     store=None,
                     headers=None,
                     multipart_threshold=None,
                     part_size=None,
                     progress_callback=None,
                     num_threads=None):
    """断点上传本地文件。

    实现中采用分片上传方式上传本地文件，缺省的并发数是 `oss2.defaults.multipart_num_threads` ，并且在
    本地磁盘保存已经上传的分片信息。如果因为某种原因上传被中断，下次上传同样的文件，即源文件和目标文件路径都
    一样，就只会上传缺失的分片。

    缺省条件下，该函数会在用户 `HOME` 目录下保存断点续传的信息。当待上传的本地文件没有发生变化，
    且目标文件名没有变化时，会根据本地保存的信息，从断点开始上传。

    :param bucket: :class:`Bucket <oss2.Bucket>` 对象
    :param key: 上传到用户空间的文件名
    :param filename: 待上传本地文件名
    :param store: 用来保存断点信息的持久存储，参见 :class:`ResumableStore`
        的接口。如不指定，则使用 `ResumableStore` 。
    :param headers: 传给 `put_object` 或 `init_multipart_upload` 的HTTP头部
    :param multipart_threshold: 文件长度大于该值时，则用分片上传。
    :param part_size: 指定分片上传的每个分片的大小。如不指定，则自动计算。
    :param progress_callback: 上传进度回调函数。参见 :ref:`progress_callback` 。
    :param num_threads: 并发上传的线程数，如不指定则使用
        `oss2.defaults.multipart_num_threads` 。
    """
    size = os.path.getsize(filename)
    multipart_threshold = defaults.get(
        multipart_threshold, defaults.multipart_threshold
    )

    if size >= multipart_threshold:
        uploader = _ResumableUploader(bucket, key, filename, size, store,
                                      part_size=part_size,
                                      headers=headers,
                                      progress_callback=progress_callback,
                                      num_threads=num_threads)
        result = uploader.upload()
        try:
            return json.loads(result.resp.response.content)
        except ValueError:
            # log error and raise UploadError
            log.error(
                u'Failed to parse callback response as JSON:\n%s',
                result.resp.response.content, exc_info=True
            )
            raise UploadError(
                'Failed to parse OSS response as JSON document:\n' +
                result.resp.response.content
            )
    else:
        with open(to_unicode(filename), 'rb') as f:
            put_result = bucket.put_object(
                key, f,
                headers=headers,
                progress_callback=progress_callback
            )
        try:
            return json.loads(put_result.resp.response.content)
        except ValueError:
            # log error and raise UploadError
            log.error(
                u'Failed to parse callback response as JSON:\n%s',
                put_result.resp.response.content, exc_info=True
            )
            raise UploadError(
                'Failed to parse OSS response as JSON document:\n' +
                put_result.resp.response.content
            )
