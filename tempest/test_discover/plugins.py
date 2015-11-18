# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc#Python本身不提供抽象类和接口机制，要想实现抽象类，可以借助abc模块。ABC是Abstract Base Class的缩写。
import logging

import six#提供了python2和3的兼容库
import stevedore#管理扩展的包
from tempest_lib.common.utils import misc


LOG = logging.getLogger(__name__)

#装饰器
@six.add_metaclass(abc.ABCMeta)
class TempestPlugin(object):
    """A TempestPlugin class provides the basic hooks for an external
    plugin to provide tempest the necessary information to run the plugin.
    """

    @abc.abstractmethod
    def load_tests(self):
        """Method to return the information necessary to load the tests in the
        plugin.

        :return: a tuple with the first value being the test_dir and the second
                 being the top_level
        :rtype: tuple
        """
        return

    @abc.abstractmethod
    def register_opts(self, conf):
        """Method to add additional configuration options to tempest. This
        method will be run for the plugin during the register_opts() function
        in tempest.config

        :param ConfigOpts conf: The conf object that can be used to register
            additional options on.
        """
        return

    @abc.abstractmethod
    def get_opt_lists(self):
        """Method to get a list of options for sample config generation

        :return option_list: A list of tuples with the group name and options
                             in that group.
        :rtype: list
        """
        return []


@misc.singleton
class TempestTestPluginManager(object):#测试插件管理
    """Tempest test plugin manager class

    This class is used to manage the lifecycle of external tempest test
    plugins. It provides functions for getting set
    """
    def __init__(self):
        self.ext_plugins = stevedore.ExtensionManager(#调用多个plugin共同处理一件事情
            'tempest.test_plugins', invoke_on_load=True,
            propagate_map_exceptions=True,
            on_load_failure_callback=self.failure_hook)

    @staticmethod
    def failure_hook(_, ep, err):
        LOG.error('Could not load %r: %s', ep.name, err)
        raise err

    def get_plugin_load_tests_tuple(self):
        load_tests_dict = {}
        for plug in self.ext_plugins:
            load_tests_dict[plug.name] = plug.obj.load_tests()
        return load_tests_dict

    def register_plugin_opts(self, conf):#config.py
        for plug in self.ext_plugins:
            try:
                plug.obj.register_opts(conf)
            except Exception:
                LOG.exception('Plugin %s raised an exception trying to run '
                              'register_opts' % plug.name)

    def get_plugin_options_list(self):#config.py
        plugin_options = []
        for plug in self.ext_plugins:
            opt_list = plug.obj.get_opt_lists()#每一个插件放到opt_list里
            if opt_list:
                plugin_options.extend(opt_list)
        return plugin_options
