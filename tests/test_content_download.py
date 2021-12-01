# coding: utf-8
import io
import os
import shutil
import tempfile
import unittest

from edo_client import WoClient


class ContentApi_DownloadTestCase(unittest.TestCase):
    '''
    - Basically this is to ensure
      all the facilities related to HTTP range headers are working properly;
    '''

    @classmethod
    def setUpClass(cls):
        cls.file_size = 10 * (2 ** 20)
        cls.download_url = 'http://192.168.1.115/docker/unittest/10mb.test'
        cls.api_url = 'https://httpbin.org/redirect-to?url={}'.format(
            cls.download_url
        )
        cls.empty_file_url = 'http://192.168.1.115/docker/unittest/empty_file.bin'
        # We're just testing some basic util functions,
        # and don't want a real WoClient instance
        cls.client = WoClient(
            cls.api_url + '#',
            '', '', '', '',
            account='', instance=''
        )
        cls.tmpdir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def test_01_get_download_url(self):
        self.assertEqual(
            self.client.content.get_download_url(uid=''),
            self.download_url,
            'Should be able to extract direct download URL from 302 redirect'
        )

    def test_11_download_to_stream_all(self):
        '''测试：下载完整文件到流'''
        stream = io.BytesIO()
        self.client.content.download_to_stream(
            stream, url=self.download_url
        )

        self.assertEqual(
            self.file_size,
            stream.tell(),
            'Cursor should be at the end of stream after download'
        )

        stream.seek(0, os.SEEK_SET)
        self.assertEqual(
            self.file_size,
            len(stream.read()),
            'File length should be 10240 bytes'
        )

    def test_12_download_stream_first_byte(self):
        '''测试：下载第一个字节到流'''
        stream = io.BytesIO()
        self.client.content.download_to_stream(
            stream, url=self.download_url, start=0, end=0,
        )
        self.assertEqual(1, stream.tell(), 'Download first byte of file')

    def test_13_download_stream_head_part(self):
        '''测试：从头下载一部分到流'''
        stream = io.BytesIO()
        self.client.content.download_to_stream(
            stream, url=self.download_url, start=0, end=(5 * (2 ** 20) - 1),
        )
        self.assertEqual(5 * (2 ** 20), stream.tell())

    def test_14_download_stream_tail_part(self):
        '''测试：从中间开始，下载文件后半部分到流'''
        stream = io.BytesIO()
        self.client.content.download_to_stream(
            stream, url=self.download_url, start=(5 * (2 ** 20)), end=None,
        )
        self.assertEqual(5 * (2 ** 20), stream.tell())

    def test_15_download_partial(self):
        '''测试：从中间开始，下载一部分到流'''
        stream = io.BytesIO()
        start, end = 1234, 54321
        self.client.content.download_to_stream(
            stream, url=self.download_url, start=start, end=end,
        )
        self.assertEqual(stream.tell(), end - start + 1)

    def test_21_get_data_full_size(self):
        '''测试：完整读取文件内容'''
        self.assertEqual(
            self.file_size,
            len(self.client.content.get_data(url=self.download_url)),
            '.get_data shoule be able to download the whole file by default',
        )

    def test_22_get_data_first_byte(self):
        '''测试：读取文件第一个字节'''
        self.assertEqual(
            1,
            len(self.client.content.get_data(url=self.download_url, size=1)),
            '.get_data should be able to download the 1st byte of given file',
        )

    def test_23_get_data_head_part(self):
        '''测试：从头读取文件的一部分内容'''
        size = 5432
        self.assertEqual(
            size,
            len(self.client.content.get_data(url=self.download_url, size=size)),  # noqa E501
            '.get_data should download the first {} bytes'.format(size),
        )

    def test_24_get_data_tail_part(self):
        '''测试：从中间开始，读取文件后半部分内容'''
        start = 12345
        size = self.file_size - start
        self.assertEqual(
            size,
            len(self.client.content.get_data(
                url=self.download_url,
                offset=start, size=size
            )),
            '.get_data shoule download last {} bytes'.format(size),
        )

    def test_25_get_data_partial(self):
        '''测试：从中间开始，读取文件一部分的内容'''
        start = 23451
        size = self.file_size - start
        self.assertEqual(
            size,
            len(self.client.content.get_data(
                url=self.download_url,
                offset=start, size=size,
            )),
            '.get_data should download {} bytes starting from offset {}'.format(size, start),  # noqa E501
        )

    def test_31_download_to_file(self):
        '''测试：完整下载文件到本地'''
        fd, fpath = tempfile.mkstemp(dir=self.tmpdir)
        os.close(fd)
        self.client.content.download_to_file(destination=fpath, url=self.download_url)
        self.assertEqual(self.file_size, os.stat(fpath).st_size)

    def test_41_download_empty_file(self):
        '''测试：下载空文件到本地'''
        fd, fpath = tempfile.mkstemp(dir=self.tmpdir)
        os.close(fd)
        self.client.content.download_to_file(destination=fpath, url=self.empty_file_url)
        self.assertEqual(0, os.stat(fpath).st_size)
