==================
易度python SDK
==================

这是整个易度平台的Python SDK，供第三方应用访问易度的各种服务。

易度开放API，基于OAuth2协议构建， `参看这里 <https://zopen.everydo.cn/platform/docs/auth/%E5%BC%80%E6%94%BEAPI%E6%A6%82%E8%A7%88.rst/@zopen.cms:view>`__

安装
=============

标准的pip安装流程::

    pip install edo_client

PyPI 上可能不是最新版本。从源代码安装最新版本::

    python setup.py install

最简使用方法
=======================

如果你知道用户名和密码，可以使用如下最简使用方法::

    from edo_client import get_client

可以直接得到工作平台的客户端, 上传文件、修改属性::

    wo_client = get_client(
        'workonline', 
        oc_api='http://192.168.1.12/oc_api', 
        account='zopen', 
        instance='instance', 
        username='admin', 
        password='admin'
    )

    wo_client.content.upload('/files', filename=ur'c:\mydoc\abc.doc')
    wo_client.content.items('/files')
    wo_client.content.update_properties('/files', fields={'subject':['Good']})

如果需要操作组织结构::

    org_client = get_client(
        'org', 
        oc_api='http://192.168.1.12/oc_api', 
        account='zopen', 
        instance='instance', 
        username='admin', 
        password='admin'
    )

    org_client.org.list_org_structure()

测试
======

测试当前没有完整覆盖，可以使用 pytest 来测试，或直接使用 setup 测试::

    pytest -v
    # 或者
    python setup.py test

如果需要详细的测试覆盖报告，推荐的测试方式是::

    # 需要安装 pytest-cov 插件: pip install pytest-cov
    pytest -vvv --cov-report html --cov=edo_client tests
    # 生成的测试覆盖报告，入口在 htmlcov/index.html

使用code认证
===============

假设你的回调url是redirect_uri::
 
    from edo_client import WoClient, OcClient

    api_host = 'http://192.168.1.12/oc_api'
    key = 'test'
    secret = '022127e182a934dea7d69s10697s8ac2'

    # 得到认证地址
    oc_client = OcClient(api_host, key, secret, redirect=redirect_uri, account='zopen', instance='default')
    authorize_url = oc_client.get_authorize_url()

你可以通过浏览器访问authorize_url，会自动附带code参数跳转到redirect_uri，继续认证过程::

    oc_client.auth_with_code(code)


