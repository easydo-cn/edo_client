# coding: utf-8


class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status = status
        self.code = code
        self.message = message

    def __str__(self):
        return "status: %s, code: %s, \nerror message: %s" % (
            self.status, self.code, self.message
        )


class DownloadError(ApiError):
    '''下载错误'''
    pass


class UploadError(Exception):
    '''上传错误'''
    pass

class UploadTokenExpired(Exception):
    '''上传凭证错误'''
    pass

class UploadDupException(Exception):
    def __init__(self, upload_sign):
        self.upload_sign = upload_sign

class AbortOperation(ApiError):
    '''取消一个操作'''
    pass


class AbortUpload(AbortOperation):
    '''取消上传操作'''
    pass


class AbortDownload(AbortOperation):
    '''取消下载操作'''
    pass
