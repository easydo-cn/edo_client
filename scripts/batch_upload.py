#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
将指定的本地文件夹内容上传到指定的线上文件夹中
'''
import argparse
import calendar
from datetime import datetime
import hashlib
import logging
import os
import sys
import time

import edo_client

reload(sys)
sys.setdefaultencoding('utf-8')


__prog__ = 'edo_upload'
log = logging.getLogger(__prog__)
log.setLevel(logging.DEBUG)
logging.basicConfig(format='{} %(levelname)s %(message)s'.format(__prog__))
# shandler = logging.StreamHandler()
# shandler.setFormatter(logging.Formatter('edo_upload %(levelname)s %(message)s'))
# log.addHandler(shandler)


def parse_args():
    '''解析参数'''
    parser = argparse.ArgumentParser(
        prog=__prog__,
        description=u'上传指定目录内容（或指定的单一文件）到文档系统'
    )
    # positional 参数
    parser.add_argument('local_folder')
    parser.add_argument('remote_folder_uid', type=int)

    # 选项
    parser.add_argument(
        '-r', '--recursive',
        action='store_true', dest='recursive',
        help=u'上传指定文件夹的所有内容，包括子文件夹，不能与 -s 共同使用'
    )
    parser.add_argument(
        '-s', '--single-file',
        action='store_true', dest='single_file',
        help=u'只上传指定的一个文件，不能与 -r 共同使用'
    )
    parser.add_argument(
        '--debug',
        action='store_true', default=False, dest='debug', help=u'调试模式'
    )
    parser.add_argument(
        '--skip-ssl-verify',
        action='store_true', default=False, dest='skip_ssl_verify',
        help=u'不检查SSL证书'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true', default=False, dest='no_progress',
        help=u'关闭文件上传进度条'
    )
    parser.add_argument(
        '--max-retry',
        type=int, default=5, dest='max_retry',
        help=u'每个文件中断后重试的最大次数，失败次数超过这个值后会跳过这个文件'
    )

    # 登录凭证参数
    parser.add_argument(
        '--oc_server', dest='oc_server', metavar=u'OC_API地址', required=True
    )
    parser.add_argument(
        '--account', default='zopen', dest='account', metavar=u'帐号'
    )
    parser.add_argument(
        '--instance', dest='instance', metavar=u'站点', required=True
    )
    parser.add_argument(
        '--token', dest='token', metavar='token',
        help=u'与 用户名+密码 二选一'
    )
    parser.add_argument(
        '--username', default='', dest='username', metavar=u'用户名',
        help=u'如果不传入 token，则必须传入 username 和 password'
    )
    parser.add_argument(
        '--password', dest='password', metavar=u'用户密码',
        help=u'如果不传入 token，则必须传入 username 和 password'
    )

    args = parser.parse_args(sys.argv[1:])

    if all([args.recursive, args.single_file, ]):
        log.critical(u'-r 不能与 -s 选项共同使用')
        sys.exit(1)

    if not any([args.token, (args.username and args.password), ]):
        log.critical(u'必须指定 token，或使用 用户名+密码')
        sys.exit(1)

    if args.max_retry < 0:
        log.critical(u'最大重试次数必须大于或等于 0')
        sys.exit(1)

    # 忽略 SSL 证书校验
    if args.skip_ssl_verify:
        log.warn(u'将不验证SSL证书')

        import requests
        import urllib3
        urllib3.disable_warnings()
        _original_request = requests.api.request

        def _patched_request(method, url, **kwargs):
            kwargs.update({'verify': False})
            return _original_request(method, url, **kwargs)

        requests.api.request = requests.request = _patched_request

        reload(edo_client)

    return args


def get_ticket_expiration(ticket):
    if ticket['upload_service'] == 'aliyun_oss':
        return calendar.timegm(
            datetime.strptime(
                ticket['Expiration'], '%Y-%m-%dT%H:%M:%SZ'
            ).timetuple()
        )
    return time.time() + 3600


def get_upload_ticket(wo_client, upload_client, fpath, path, uid):
    '''
    加载上次保存的上传 ticket，或申请一个新的
    逻辑：
        - 加载保存的信息；
        - 验证凭证的有效性；
            - 如果有效，直接使用；
            - 如果无效，调用 renew_ticket 接口去申请一个新的凭证；
    这个逻辑只对直传到云服务起作用。
    凭证有效性验证的逻辑：
        - 如果文件发生变化（mtime or fsize）那么无效；
        - 如果剩余有效时间超过 10 秒，认为是有效的；
    '''
    session_key = hashlib.md5(
        fpath + upload_client.api_host + wo_client.api_host +
        wo_client.content.account_name + wo_client.content.instance_name
    ).hexdigest()
    store = upload_client.upload.get_session_store()
    saved_session = store.load(session_key, default={})

    if not saved_session:
        log.debug(u'没有保存的 ticket，开始申请新的 ticket')
        ticket = wo_client.content.get_upload_ticket(
            path=path, uid=uid,
            filename=os.path.basename(fpath), maxsize=os.path.getsize(fpath)
        )
        saved_session = {
            'ticket': ticket,
            'expires_at': get_ticket_expiration(ticket),
            'fsize': os.path.getsize(fpath),
            'mtime': os.path.getmtime(fpath),
        }
        # 保存
        store.save(session_key, **saved_session)
        return saved_session['ticket']

    # Validate saved session
    valid = True
    if not os.path.isfile(fpath)\
            or saved_session.get('fsize') != os.path.getsize(fpath)\
            or saved_session.get('mtime') != os.path.getmtime(fpath)\
            or saved_session.get('expires_at') - time.time() <= 10:
        valid = False

    if not valid:
        log.debug(u'保存的 ticket 已经失效，正在续期')
        new_ticket = wo_client.content.renew_upload_ticket(
            path=path, uid=uid,
            filename=os.path.basename(fpath), maxsize=os.path.getsize(fpath)
        )
        saved_session['ticket'].update(new_ticket)

        saved_session.update({
            'fsize': os.path.getsize(fpath),
            'mtime': os.path.getmtime(fpath),
            'expires_at': get_ticket_expiration(new_ticket),
        })

        # 保存
        store.save(session_key, **saved_session)
        log.debug(
            u'续期后的 ticket 已经保存，有效期至 %s 秒后',
            saved_session['expires_at'] - time.time()
        )
    else:
        log.debug(
            u'保存的 ticket 有效，有效期至 %s 秒后，将直接使用',
            saved_session['expires_at'] - time.time()
        )

    return saved_session['ticket']


def remove_upload_ticket(wo_client, upload_client, fpath, path, uid):
    '''
    删除一个保存的 ticket 缓存。在上传完毕一个文件时调用。
    '''
    session_key = hashlib.md5(
        fpath + upload_client.api_host + wo_client.api_host +
        wo_client.content.account_name + wo_client.content.instance_name
    ).hexdigest()
    upload_client.upload.get_session_store().remove(session_key)


def upload_file(
    wo_client, upload_client, fpath,
    remote_folder_path=None, remote_folder_uid=None, fpath_u=None,
    show_progress=True, max_retry=5
):
    '''
    Upload a single file to given remote folder path.
    Returns `True` for a successful upload, else `False`.
    '''
    if not fpath_u:
        fpath_u = fpath.decode(sys.getfilesystemencoding())

    if show_progress:
        def print_progress(uploaded_bytes, total_bytes, fpath):
            '''更新上传进度条'''
            sys.stdout.write(
                u'{:.2f}% ["{}"]\r'.format(
                    (uploaded_bytes * 100.0 / total_bytes), fpath
                )
            )
            sys.stdout.flush()  # not necessary for all platforms
    else:
        print_progress = None

    retried = 0
    while retried <= max_retry:
        if retried > 0:
            log.info(u'"%s" 正在进行第 %s 次重试', fpath_u, retried)

        try:
            upload_ticket = get_upload_ticket(
                wo_client, upload_client, fpath_u,
                remote_folder_path, remote_folder_uid
            )
        except edo_client.error.ApiError as e:
            if e.code == 409:  # TODO 重命名
                log.info(u'"%s" 文件名已经存在，跳过', fpath_u)
            log.debug(u'"%s" 申请上传失败', fpath_u, exc_info=True)
            log.info(u'"%s" 申请上传失败', fpath_u)
            if retried == max_retry:
                return False
            retried += 1
            continue

        try:
            log.debug(upload_ticket)
            upload_client.upload.upload(
                fpath_u, upload_ticket, on_progress=print_progress
            )
        except Exception as e:
            log.debug(u'"%s" 上传失败', fpath_u, exc_info=True)
            log.error(u'"%s" 上传失败', fpath_u)
            if retried == max_retry:
                return False
            continue
        else:
            remove_upload_ticket(
                wo_client, upload_client, fpath_u,
                remote_folder_path, remote_folder_uid
            )
            log.info(u'"%s" 上传成功', fpath_u)
            return True
            # break
        finally:
            retried += 1


def main():
    '''命令行工具入口'''
    try:
        execute()
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.stdout.flush()
        log.info(u'操作被用户取消')


def execute():
    # 解析参数，设置日志级别
    args = parse_args()
    log_level = logging.DEBUG if args.debug else logging.INFO
    log.setLevel(log_level)
    log.debug(args)

    local_root = os.path.abspath(args.local_folder)
    show_progress = not args.no_progress

    # 检查路径合法性
    if args.single_file and not os.path.isfile(local_root):
        log.critical(u'指定的本地路径 "%s" 不存在，或不是一个文件', local_root)
        sys.exit(1)
    if not args.single_file and not os.path.isdir(local_root):
        log.critical(u'指定的本地路径 "%s" 不存在，或不是一个文件夹', local_root)
        sys.exit(1)

    try:
        wo_client = edo_client.get_client(
            'workonline', args.oc_server,
            args.account, args.instance,
            username=args.username, password=args.password, token=args.token
        )
        upload_client = edo_client.get_client(
            'upload', args.oc_server,
            args.account, args.instance,
            username=args.username, password=args.password, token=args.token
        )
    except:
        log.debug(u'连接指定站点失败', exc_info=True)
        log.info(u'连接指定站点失败')
        sys.exit(1)

    # 获取线上站点的信息
    remote_root_folder = wo_client.content.properties(uid=args.remote_folder_uid)
    failed_files = []

    # 上传单一文件
    if args.single_file:
        if not upload_file(
            wo_client, upload_client,
            local_root, remote_folder_uid=remote_root_folder['uid'],
            show_progress=show_progress, max_retry=args.max_retry
        ):
            failed_files.append(local_root)
    else:
        # 遍历文件夹，上传文件
        for root, dirs, files in os.walk(local_root):
            # 对子文件夹内容
            if os.path.abspath(root) != local_root:
                # 默认不上传子文件夹内容
                if not args.recursive:
                    log.info(u'跳过文件夹 "%s"', root)
                    continue
                else:
                    # 如果要上传，先尝试创建文件夹
                    local_folder_path = os.path.relpath(
                        os.path.abspath(root), local_root
                    ).decode(sys.getfilesystemencoding())
                    try:
                        log.info(u'创建文件夹 "%s"', local_folder_path)
                        remote_folder_path = '/'.join([
                            remote_root_folder['path'], local_folder_path.replace(os.path.sep, '/')
                        ])
                        wo_client.content.create_folder(
                            path=os.path.dirname(remote_folder_path),
                            name=os.path.basename(remote_folder_path)
                        )
                        log.info(u'文件夹 "%s" 创建完成', local_folder_path)
                    except edo_client.error.ApiError as e:
                        if e.code == 409:
                            log.info(u'文件夹 "%s" 已经存在', local_folder_path)
                        else:
                            log.debug(u'文件夹 "%s" 创建失败', local_folder_path, exc_info=True)
                            log.info(u'文件夹 "%s" 创建失败，跳过', local_folder_path)
                            failed_files.append(local_folder_path)
                            continue
            else:
                remote_folder_path = remote_root_folder['path']

            # 上传文件
            for file in files:
                fpath = os.path.join(os.path.abspath(root), file)
                # FIXME
                if not upload_file(
                    wo_client, upload_client,
                    fpath, remote_folder_path=remote_folder_path,
                    show_progress=show_progress, max_retry=args.max_retry
                ):
                    failed_files.append(fpath)

    if len(failed_files) > 0:
        sys.stdout.write(u'以下内容上传失败：\n')
        for f in failed_files:
            fu = f if isinstance(f, unicode) else f.decode(sys.getfilesystemencoding())
            sys.stdout.write(u'\t{}\n'.format(fu))
        sys.stdout.flush()  # not necessary for all platforms
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
