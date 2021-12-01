# coding: utf-8
import os
import tempfile
import shutil
import hashlib
from fabric2 import Connection
from fabric2.transfer import Transfer
from invoke.exceptions import UnexpectedExit

from edo_client import get_client

class RemoteHost(Connection):
    """
    继承自fabric2的Connection
    wo_client:工作平台客户端
    host:远程主机,如果host为local的话则为本地主机
    platform:远程主机操作系统
    logger:记录日志的日志管理器
    """
    # 用来记录远端机器的资源缓存文件
    # - 形式：{'host': {account: {site:['resources']}}}
    # 如：{'192.168.1.32': {'zopen': {'default':{'zopen.xxx:xxxx.py':version, 'zopen.xxx:xxxx/':version} }}}
    REMOTE_CACHE = {}

    def __init__(self, wo_client, host, platform, logger, package_versions, user=None, port=None, forward_agent=None,
                 connect_timeout=None, connect_kwargs=None, inline_ssh_env=None, verify_resource=False):
        super(RemoteHost, self).__init__(
            host=host,
            user=user,
            port=port,
            config=None,
            gateway=None,
            forward_agent=forward_agent,
            connect_timeout=connect_timeout,
            connect_kwargs=connect_kwargs,
            inline_ssh_env=inline_ssh_env,
        )
        self.wo_client = wo_client
        self.host = host
        self.platform = platform
        self.logger = logger
        self.package_versions = package_versions
        self.verify_resource = verify_resource

        if platform == 'win':
            home_path = self._run(self._remote_runner(), 'cmd.exe /c "echo %HOMEDRIVE%%HOMEPATH%"', pty=True, hide=True).stdout
            self.workdir = home_path.replace('\n', '').replace('\r', '')
        elif platform == 'linux':
            self.workdir = '~'
        else:
            self.workdir = '/edo_resource'

    # 统一windows和linux的run方法,记录每次run的日志
    def run(self, command, addon_resources=[], shell=False, **kwargs):
        """
        在远端机器运行命令
        :command: 要运行的命令
        :shell: 是否直接使用shell 不使用cmd.exe， 只针对windows系统的远程主机有效
        :addon_resources: 附加的站点资源文件，如果传递则先从站点下载下来再上传到远端
        :version: command执行命令中的脚本/资源的版本
        :depend_versions: command执行命令中依赖的软件包的版本集合
        :kwargs: 关键字参数
        使用示例：
        1. 执行一条普通命令：coon.run('ls')
        2. 执行一条需要脚本的命令：
            1）执行本应用包的脚本
            conn.run(python xxx.py, shell=True, addon_resources=['zopen.test:xxx.py'])
        """
        if addon_resources:
            for resource in addon_resources:
                package = resource.split(':')[0]
                version = self.package_versions.get(package, None)
                self.download(resource, version=version)

            if self.platform:
                if self.platform == 'win':
                    code_dir = r'{0}\sites\{1}\{2}'.format(self.workdir, self.wo_client.account_name, self.wo_client.instance_name)
                else:
                    code_dir = '~/sites/{0}/{1}'.format(self.wo_client.account_name, self.wo_client.instance_name)
            else:
                code_dir = '/edo_resource'
            command = command.replace('{code_dir}', code_dir)

        try:
            if self.platform == 'win':
                if shell:
                    # shell中无法读取windows环境变量
                    if '%sikulix%' in command:
                        command = command.replace('%sikulix%', 
                        self._run(self._remote_runner(), 'cmd.exe /c "echo %sikulix%"', pty=True, hide=True, encoding='gbk', **kwargs).stdout.replace('\r', '').replace('\n', ''))
                else:
                    command = r'cmd.exe /c "cd {0} & {1}"'.format(self.workdir, command)
                result = self._run(self._remote_runner(), command, pty=True, hide=True, encoding='gbk', **kwargs)
            elif self.platform == 'linux':
                result = self._run(self._remote_runner(), command, hide=True, **kwargs)
            elif self.host == 'local':
                result = self.local(command, hide=True, **kwargs)
            else:
                raise Exception('Run/local Error, check platform/host')
            self.logger.info(result.command)
            self.logger.debug(result.stdout)
        except UnexpectedExit as e:
            self.logger.error(e.result.stderr)
            raise e
        return result

    def local(self, *args, **kwargs):
        '''
        这里local需要加上 replace_env=False,才能正常使用系统的环境变量，原因如下:
        1、官方说明local实际调用invoke.run，而未对参数默认值进行说明。
        2、虽然invoke.run中说明replace_env默认为False,实际是invoke.config中指定了默认值为False。
        3、而如果从fabric.Conneciton().loacl调用，使用的是fabric.config中的默认值。
        4、fabric.config中 replace_env=True。
        5、至于replace_env为什么要设为False, 请看http://docs.pyinvoke.org/en/latest/api/runners.html#invoke.runners.Runner.run
        '''
        kwargs['replace_env'] = False
        return super(RemoteHost, self).local(*args, **kwargs)

    def get(self, remote, local=None, preserve_mode=True):
        # windows 下 get 方法的主目录只能是 self.workdir(C:\Users\edo) 
        if 'win' in self.platform and ':' in remote:
            raise RuntimeError("远端机器为 windows，get 方法的 remote 参数只能是相对于 workdir(C:\\Users\\edo) 的路径")

        try:
            result = Transfer(self).get(remote, local, preserve_mode)
            self.logger.info('远端文件由{}下载至本地{}'.format(result.remote, result.local))
        except Exception as e:
            self.logger.error(e)
            raise e
        return result


    def put(self, local, remote=None, preserve_mode=True):
        # windows 下 get 方法的主目录只能是 self.workdir(C:\Users\edo) 
        if self.platform == 'win' and ':' in remote:
            raise RuntimeError("远端机器为 windows，put 方法的 remote 参数只能是相对于 workdir(C:\\Users\\edo) 的路径")
        
        result = None
        try:
            if os.path.isdir(local):
                for file_name in os.listdir(local):
                    with open(os.path.join(local, file_name), 'r') as local_obj:
                        result = Transfer(self).put(local_obj, 
                                remote + ('\\' if self.platform == 'win' else '/') + file_name)
                        self.logger.info('本地文件由{}上传至远端{}'.format(result.local, result.remote))
            else:
                with open(local, 'r') as local_obj:
                    result = Transfer(self).put(local_obj, remote, preserve_mode)
                    self.logger.info('本地文件由{}上传至远端{}'.format(result.local, result.remote))
        except Exception as e:
            self.logger.error(e)
            raise e
        return result


    def download(self, resource_path, version=None):
        """
        从站点下载文件到远端
        :resource_path: 站点资源文件路径
        :version: 下载的资源版本
        """
        # 获取签名信息
        if '#' in resource_path:
            resource_path, signature = resource_path.split('#')
        else:
            signature = ""

        package_name, resource_name = resource_path.split(':')

        if not version:
            version = self.wo_client.packages.get_package_obj(package_name).version
        # 先判断是否存在缓存
        if self.host in RemoteHost.REMOTE_CACHE \
            and self.wo_client.account_name in RemoteHost.REMOTE_CACHE[self.host] \
            and self.wo_client.instance_name in RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name] \
            and resource_path in RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name][self.wo_client.instance_name]:
                if version == RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name][self.wo_client.instance_name][resource_path]:
                    self.logger.info('%s 远端机器存在缓存文件: %s', self.host, resource_path)
                    self.logger.info('缓存记录为：%s', RemoteHost.REMOTE_CACHE)
                    return True
                else:
                    # 如果有旧版本的缓存需要清理
                    version_cache = RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name][self.wo_client.instance_name][resource_path]
                    if version_cache:
                        old_version_path = '{0}/sites/{1}/{2}/{3}/{4}/'.format(
                            self.workdir, self.wo_client.account_name, self.wo_client.instance_name, package_name, version_cache)
                        old_resource_path = old_version_path + resource_name
                        if self.platform == 'win':
                            old_resource_path = old_resource_path.replace('/', '\\')
                            old_version_path = old_version_path.replace('/', '\\')
                            self.run(r'if exist {0} del /s/q {0}'.format(old_resource_path))
                            # 清除资源文件后会残留一个空文件夹，当文件夹为空的时候也删除
                            dir_info = self.run('dir /a/b {}'.format(old_version_path)).stdout.replace('\n', '').replace('\r', '')
                            if dir_info == '__pycache__':
                                self.run(r'if exist {0} rd /s/q {0}'.format(old_version_path))
                        else:
                            self.run('if [ -f {0} ];then rm -f {0}; fi'.format(old_resource_path))
                            dir_info = self.run('ls {}'.format(old_version_path)).stdout.replace('\n', '').replace('\r', '')
                            if dir_info == '':
                                self.run('if [ -d {0} ];then rm -rf {0}; fi'.format(old_version_path))
                        del RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name][self.wo_client.instance_name][resource_path]
                        self.logger.info('清理%s旧版本：%s缓存',resource_path, version_cache)

        system_temp = tempfile.gettempdir()
        resource_temp = os.path.join(system_temp, 'edo_resource')
        local_resource = self.get_code_dir(package_name)
        def __put(resource):
            """
            从线上下载文件，再上传到远端
            说明：无论是下载单个文件还是整个目录，从 线上下载文件，再上传到远端 的代码都是一样的，所以提取成一个私有方法
            """
            response = self.wo_client.package.get_resource(package_name, resource)

            # 验证签名
            if self.verify_resource:
                resource_ext = os.path.splitext(resource)[-1].lower()
                # 对非图片格式进行签名认证
                if not resource_ext in ('.bmp', '.png', '.gif', '.jpg', '.jepg') and\
                        not self.verify_md5_signature(response.content, signature):
                    raise Exception('Signature verification failed.')

            resource_path = os.path.join(resource_temp, resource) if self.host != 'local' else os.path.join(local_resource, resource)
            self.logger.info('本地资源地址：%s', resource_path)
            if not os.path.exists(os.path.dirname(resource_path)):
                os.makedirs(os.path.dirname(resource_path))
                self.logger.info('创建本地资源目录')

            self.logger.info(resource_path)
            with open(resource_path, 'wb') as f:
                for block in response.iter_content(chunk_size=1024):
                    if not block:
                        break
                    f.write(block)
                    f.flush()

            # 如果是在本地执行只需要下载不需要上传
            if self.host == 'local':
                return
            # 远端资源文件保存目录
            # - windows:  C:\Users\edo\sites\{账号名}\{站点名}\{软件包名}\{版本}\{资源名}
            # - linux: /home/edo/sites/{账号名}/{站点名}/{软件包名}\{版本}\{资源名}
            # 为了统一，下面全部使用相对路径(相对于用户home目录)
            remote_path = 'sites/{0}/{1}/{2}/{3}/{4}'.format(
                    self.wo_client.account_name, self.wo_client.instance_name, package_name, version, resource)

            # 确保路径资源文件的父目录存在
            dir_path = os.path.dirname(remote_path)
            if self.platform == 'win':
                self.run(r'if not exist {0} md {0}'.format(dir_path.replace('/', '\\')))

                remote_path = remote_path.replace('/', '\\')
            else:
                self.run('mkdir -p {0}'.format(dir_path))

            self.put(resource_path, remote_path)

        # 开始上传, 判断是单个文件还是整个目录
        try:
            resources = resource_path.split(':')[-1]
            if resources.endswith('/'):
                # 上传整个目录下的资源文件
                all_resources = self.wo_client.package.list_resources(package_name)
                for resource in all_resources:
                    if resource.startswith(resources):
                        __put(resource)
            else:
                # 上传单个资源文件
                __put(resources)

            # 上传完成后需要记录一下缓存
            # 如果没有主机、账号、站点记录则初始化一个
            if self.host not in RemoteHost.REMOTE_CACHE:
                RemoteHost.REMOTE_CACHE[self.host] = {}

            if self.wo_client.account_name not in RemoteHost.REMOTE_CACHE[self.host]:
                RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name] = {}

            if self.wo_client.instance_name not in RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name]:
                RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name][self.wo_client.instance_name] = {}

            RemoteHost.REMOTE_CACHE[self.host][self.wo_client.account_name][self.wo_client.instance_name][resource_path] = version
            self.logger.info('缓存添加完毕，现有缓存为：%s', RemoteHost.REMOTE_CACHE)
        except Exception as e:
            self.logger.error('向远端 %s 机器上传 %s 文件失败, 失败原因: %s', self.host, resource_path, e, exc_info = True)
            raise e
        finally:
            if self.host != 'local':
                # 清理本机缓存目录
                shutil.rmtree(resource_temp)

    def call(self, script_name, interpreter='python', params={}, **kwargs):
        """
        线上脚本/资源执行方法
        script_name: 脚本名称
        interpreter: 执行脚本的解释器
        version: 执行脚本/资源的版本
        depend_versions: 依赖包的版本集合
        使用示例：
        1. 使用当前软件包版本的脚本
            conn.call('zopen.test:xxx', version=version_) 需要在调用的时候添加version_内置参数
        2. 使用依赖的其他软件包脚本
            conn.call('zopen.other:xxx', depend_versions=depend_versions_)
            conn.call('zopen.other1:xxx', depend_versions=depend_versions_)
            需要在附加说明中添加：depend:['zopen.other', 'zopen.other1'], 并在脚本中添加内置参数depend_versions_
        3. 不使用内置变量调用线上脚本
            conn.call('zopen.xxx:xxx'), 不使用内置变量的话会从wo_client中读取, 性能速度会受影响（不推荐）
        """
        package_name, script = script_name.split(':')
        call_params = r' '.join(['--{0} {1}'.format(key, value) for key, value in params.items()]) if params else ''

        run_cmd = '{interpreter} {code_dir}{script} {call_params}'.format(
            interpreter=interpreter,
            code_dir=self.get_code_dir(package_name),
            script=script,
            call_params=call_params)

        if self.platform == 'win':
            run_cmd = run_cmd.replace('/', '\\')
        self.run(run_cmd, addon_resources=[script_name], shell=True, **kwargs)


    def rpa(self, script_name, *args, **kwargs):
        """
        rpa 脚本执行方法
        script_name: 脚本名称
        version: 执行脚本/资源的版本
        depend_versions: 依赖包的版本集合
        args: 不定参数
        kwagrs: 关键字参数
        使用示例：
        1. 使用当前软件包版本的脚本
            conn.rpa('zopen.rpa:xxx', version=version_) 需要在调用的时候添加version_内置参数
        2. 使用依赖的其他软件包脚本
            conn.rpa('zopen.other:xxx', depend_versions=depend_versions_)
            conn.rpa('zopen.other1:xxx', depend_versions=depend_versions_)
            需要在附加说明中添加：depend:['zopen.other', 'zopen.other1'], 并在脚本中添加内置参数depend_versions_
        3. 不使用内置变量调用rpa脚本
            conn.rpa('zopen.xxx:xxx'), 不使用内置变量的话会从wo_client中读取, 性能速度会受影响（不推荐）
        注：args 和 kwargs 都将转换成 rpa 脚本在命令行运行时的参数，在 rpa 脚本中通过 sys.args 进行使用
        """
        package_name = script_name.split(':')[0]
        rpa_name = script_name.split(':')[-1]

        # 下载rpa脚本
        if not script_name.endswith('/'):
            script_name += '/'

        rpa_args = r' '.join([str(i) for i in args]) if args else ''
        rpa_kwargs = r' '.join(['{0}={1}'.format(key, value) for key, value in kwargs.items()]) if kwargs else ''
        rpa_cmd = r'java -jar %sikulix% -r {code_dir}{rpa_name} -- {args} {kwargs}'.format(
                    code_dir=self.get_code_dir(package_name),
                    rap_name=rpa_name,
                    args=rpa_args,
                    kwargs=rpa_kwargs)
        
        if self.platform == 'win':
            rpa_cmd = rpa_cmd.replace('/', '\\')

        return self.run(rpa_cmd, addon_resource=[script_name], shell=True)


    def purge(self, package=None):
        """
        清理资源文件缓存
        :package: 软件包，默认为None表示清理所有缓存，否则清理具体的软件包缓存
        """
        base_resoure_path = 'sites/{0}'.format(self.wo_client.instance_name) 
        if package:
            base_resoure_path += '/{0}'.format(package)

        if self.platform == 'win':
            resource_path = r'{0}\{1}'.format(self.workdir, base_resoure_path.replace('/', '\\'))
            clean_cmd = r'if exist {0} (rd /s/q {0})'.format(resource_path)
        else:
            # 目前固定linux下的缓存目录在edo用户下：/home/edo
            resource_path = '{0}/{1}'.format('~', base_resoure_path)
            clean_cmd = 'rm -rf {0}'.format(resource_path)

        return self.run(clean_cmd)

    def get_code_dir(self, package_name):
        code_dir = r'{workdir}/sites/{account}/{instance}/{package}/{version}/'.format(
           workdir=self.workdir, 
           account=self.wo_client.account_name, 
           instance=self.wo_client.instance_name, 
           package=package_name, 
           version=self.package_versions.get(package_name))
        if self.platform == 'win':
            code_dir = code_dir.replace('/', '\\')
        return code_dir

    @staticmethod
    def verify_md5_signature(content, signature=''):
        return hashlib.md5(content.strip()).hexdigest() == signature


def get_host(host_string=None, host=None, platform=None, port=22, user='edo', password=None, verify_resource=False,
        __worker_db=None, __logger=None, __wo_client=None, __package_versions=None, *args, **kwargs):
    # 只能够在联机脚本中使用
    if not host and not host_string:
        raise KeyError('Two parameters (host, host_string) select to pass at least one')

    # 判断 host_string 的合法性：
    # 0. 必须是local或以下两点
    # 1. 必须以 win:// 或者 linux:// 开头
    # 2. 必须包含 @ 字符
    if host_string:
        if host_string.startswith('local'):
            host = host_string
        else:
            if not host_string.startswith('win://') and not host_string.startswith('linux://'):
                raise KeyError('host_string must start with "win://" or "linux://"')
            elif '@' not in host_string:
                raise KeyError('host_string must contain "@"')
            else:
                platform, host_info = host_string.split('://')
                user_password, host_port = host_info.split('@')

                if ':' in user_password:
                    user, password = user_password.split(':')
                else:
                    user = user_password

                if ':' in host_port:
                    host, port = host_port.split(':')
                    port = int(port)
                else:
                    host = host_port

    if not __wo_client:
        worker_db = __worker_db
        wo_client = get_client(
            'workonline', worker_db['oc_server'], worker_db['account'], worker_db['instance'],
            token=worker_db['token']
        )
    else:
        wo_client = __wo_client

    if not __logger:
        import logging
        __logger = logging.getLogger('RemoteHost')

    connect_kwargs = {'password': password} if password else {}

    return RemoteHost(wo_client=wo_client, host=host, platform=platform, port=port, user=user,verify_resource=verify_resource,
        connect_kwargs=connect_kwargs, logger=__logger, package_versions=__package_versions, *args, **kwargs)


