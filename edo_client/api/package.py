# -*- coding: utf-8 -*-
import json
from .base import BaseApi
from collections import OrderedDict

class PackageApi(BaseApi):

    def list(self, account=None, instance=None, in_memory=None):
        """ 取得所有的软件包"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/list', raw=True, account=account, instance=instance, in_memory=json.dumps(in_memory))
        return json.loads(resp.text, object_pairs_hook=OrderedDict)

    def get(self, package_name, detail=False, account=None, instance=None):
        """ 取得软件包的信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get', raw=True, package_name=package_name, detail=json.dumps(detail), account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)

    def new(self, package_name, info, account=None, instance=None):
        """ 取得软件包的信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/new', package_name=package_name, info=json.dumps(info), account=account, instance=instance)

    def install(self, package_name, upgrade=True, is_temp=False, account=None, instance=None):
        """ 安装软件包"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
        return self._post('/api/v1/package/install', package_name=package_name, upgrade=json.dumps(upgrade), 
                        is_temp=json.dumps(is_temp), account=account, instance=instance)

    def set(self, package_name, info, account=None, instance=None):
        """ 取得软件包的信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/set', package_name=package_name, info=json.dumps(info), account=account, instance=instance)


    def remove(self, package_name, account=None, instance=None):
        """ 取得软件包的信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove', package_name=package_name, account=account, instance=instance)


    def register_form(self, name, form_def, overwrite=False, account=None, instance=None):
        """ 注册表单"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/register_form', name=name, form_def=json.dumps(form_def), overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_forms(self, package_name, account=None, instance=None):
        """ 列出所有表单"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_forms', package_name=package_name, account=account, instance=instance)


    def get_form(self, name, account=None, instance=None):
        """ 取得表单信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get_form', raw=True, name=name, account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)


    def remove_form(self, name, account=None, instance=None):
        """ 删除表单"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_form', name=name, account=account, instance=instance)



    def register_script(self, name, script_def, overwrite=False, account=None, instance=None):
        """ 注册脚本"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/register_script', name=name, code_def=json.dumps(script_def), overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_scripts(self, package_name, account=None, instance=None):
        """ 列出所有脚本"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_scripts', package_name=package_name, account=account, instance=instance)


    def get_script(self, name, account=None, instance=None):
        """ 取得脚本信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get_script', raw=True, name=name, account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)


    def remove_script(self, name, account=None, instance=None):
        """ 删除脚本"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_script', name=name, account=account, instance=instance)


    def register_rule(self, name, rule_def, overwrite=False, account=None, instance=None):
        """ 注册规则"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/register_rule', name=name, rule_def=json.dumps(rule_def), overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_rules(self, package_name, account=None, instance=None):
        """ 列出所有规则"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_rules', package_name=package_name, account=account, instance=instance)


    def get_rule(self, name, account=None, instance=None):
        """ 取得规则信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get_rule', raw=True, name=name, account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)


    def remove_rule(self, name, account=None, instance=None):
        """ 删除规则"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_rule', name=name, account=account, instance=instance)


    def register_template(self, name, template_def, overwrite=False, account=None, instance=None):
        """ 注册模板"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/register_template', name=name, template_def=json.dumps(template_def), overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_templates(self, package_name, account=None, instance=None):
        """ 列出所有模板"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_templates', package_name=package_name, account=account, instance=instance)


    def get_template(self, name, account=None, instance=None):
        """ 取得模板信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get_template', raw=True, name=name, account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)


    def remove_template(self, name, account=None, instance=None):
        """ 删除模板"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_template', name=name, account=account, instance=instance)


    def register_mdset(self, name, mdset_def, overwrite=False, account=None, instance=None):
        """ 注册属性集"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/register_mdset', name=name, mdset_def=json.dumps(mdset_def), overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_mdsets(self, package_name, account=None, instance=None):
        """ 列出所有属性集"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_mdsets', package_name=package_name, account=account, instance=instance)


    def get_mdset(self, name, account=None, instance=None):
        """ 取得属性集信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get_mdset', raw=True, name=name, account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)


    def remove_mdset(self, name, account=None, instance=None):
        """ 删除属性集"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_mdset', name=name, account=account, instance=instance)



    def register_stage(self, name, stage_def, overwrite=False, account=None, instance=None):
        """ 注册阶段"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/register_stage', name=name, stage_def=json.dumps(stage_def), overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_stages(self, package_name, account=None, instance=None):
        """ 列出所有阶段"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_stages', package_name=package_name, account=account, instance=instance)


    def get_stage(self, name, account=None, instance=None):
        """ 取得阶段信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get_stage', raw=True, name=name, account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)


    def remove_stage(self, name, account=None, instance=None):
        """ 删除阶段"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_stage', name=name, account=account, instance=instance)



    def register_workflow(self, name, workflow_def, overwrite=False, account=None, instance=None):
        """ 注册流程"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/register_workflow', name=name, workflow_def=json.dumps(workflow_def), overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_workflows(self, package_name, account=None, instance=None):
        """ 列出所有流程"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_workflows', package_name=package_name, account=account, instance=instance)


    def get_workflow(self, name, account=None, instance=None):
        """ 取得流程信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get_workflow', raw=True, name=name, account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)


    def remove_workflow(self, name, account=None, instance=None):
        """ 删除流程"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_workflow', name=name, account=account, instance=instance)


    def register_skin(self, name, skin_def, overwrite=False, account=None, instance=None):
        """ 注册皮肤"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/register_skin', name=name, skin_def=json.dumps(skin_def), overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_skins(self, package_name, account=None, instance=None):
        """ 列出所有皮肤"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_skins', package_name=package_name, account=account, instance=instance)


    def get_skin(self, name, account=None, instance=None):
        """ 取得皮肤信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        resp = self._get('/api/v1/package/get_skin', raw=True, name=name, account=account, instance=instance)
        return json.loads(resp.text, object_pairs_hook=OrderedDict)


    def remove_skin(self, name, account=None, instance=None):
        """ 删除皮肤"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_skin', name=name, account=account, instance=instance)


    def add_resource(self, package_name, res_path, stream, overwrite=False, account=None, instance=None):
        """ 注册资源"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._post('/api/v1/package/add_resource', package_name=package_name, res_path=res_path, files={'stream':('resource', stream)}, overwrite=json.dumps(overwrite), account=account, instance=instance)

    def list_resources(self, package_name, account=None, instance=None):
        """ 列出所有资源"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/list_resources', package_name=package_name, account=account, instance=instance)


    def get_resource(self, package_name, res_path='/', account=None, instance=None):
        """ 取得资源信息"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name

        resp = self._get('/api/v1/package/get_resource', raw=True, package_name=package_name, res_path=res_path, account=account, instance=instance)
        return resp

    def remove_resource(self, package_name, res_path, account=None, instance=None):
        """ 删除资源"""
        if not account: account = self.account_name
        if not instance: instance = self.instance_name
 
        return self._get('/api/v1/package/remove_resource', package_name=package_name, res_path=res_path, account=account, instance=instance)
