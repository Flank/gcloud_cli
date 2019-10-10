# -*- coding: utf-8 -*- #

# Copyright 2015 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys
import textwrap

from googlecloudsdk.command_lib import info_holder
from googlecloudsdk.core import properties
from googlecloudsdk.core.diagnostics import network_diagnostics
from googlecloudsdk.core.diagnostics import property_diagnostics
from googlecloudsdk.core.updater import update_manager
from surface import info as info_command
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class InfoTest(cli_test_base.CliTestBase,
               sdk_test_base.SdkBase):

  def testInfo(self):
    self.Run('info')
    # Just make sure it runs and is printing all sections.
    self.AssertOutputContains('Google Cloud SDK [')
    self.AssertOutputContains('Installation Root: [')
    self.AssertOutputContains('Kubectl on PATH: [')
    self.AssertOutputContains('User Config Directory: [')
    self.AssertOutputContains('Active Configuration Name: [')
    self.AssertOutputContains('Active Configuration Path: [')
    self.AssertOutputContains('Account: [')
    self.AssertOutputContains('Project: [')
    self.AssertOutputContains('Current Properties:\n')
    self.AssertOutputContains('Logs Directory: [')
    self.AssertOutputContains('Python PATH: [')
    self.AssertOutputContains('git: [')
    self.AssertOutputContains('ssh: [')

  def testInfo_PythonLocation(self):
    self.Run('info')
    self.AssertOutputContains('Python Location: [{}]'.format(sys.executable))

  def testInfo_PythonLocationUnicode(self):
    self.SetEncoding('utf8')
    unicode_path = '/skrendu/į/Italiją'
    self.StartObjectPatch(sys, 'executable', unicode_path)
    self.Run('info')
    self.AssertOutputContains('Python Location: [{}]'.format(unicode_path))

  def testInfo_NoPython(self):
    self.StartObjectPatch(sys, 'executable', None)
    self.Run('info')
    self.AssertOutputContains('Python Location: [None]')

  def testInfo_Yaml_PythonLocation(self):
    path = '/usr/local/python'
    self.StartObjectPatch(sys, 'executable', return_value=path)
    self.Run('info --format=yaml')
    self.AssertOutputContains('python_location: {}'.format(sys.executable))

  def testInfo_Yaml_NoPython(self):
    self.StartObjectPatch(sys, 'executable', None)
    self.Run('info --format=yaml')
    self.AssertOutputContains('python_location: null')

  def testInfo_Anonymize_AccountProject(self):
    properties.VALUES.core.account.Set('personal@secret.com')
    properties.VALUES.core.project.Set('my-own-project')
    result = self.Run('info --format=disable --anonymize')

    self.assertEqual('p..l@s..m', result.config.account)
    self.assertEqual('p..l@s..m', result.config.properties['core']['account'])
    self.assertEqual('m..t', result.config.project)
    self.assertEqual('m..t', result.config.properties['core']['project'])

  def testInfo_Anonymize_Proxy(self):
    properties.VALUES.proxy.username.Set('personal')
    properties.VALUES.proxy.password.Set('proxy-password')
    result = self.Run('info --format=disable --anonymize')

    self.assertEqual('p..l', result.config.properties['proxy']['username'])
    self.assertEqual('PASSWORD', result.config.properties['proxy']['password'])

  def testInfo_Anonymize_Paths(self):
    result = self.Run('info --format=disable --anonymize')
    self.assertEqual(
        os.path.join('${CLOUDSDK_CONFIG}', 'configurations', 'config_default'),
        result.config.paths['active_config_path'])
    self.assertEqual(
        '${CLOUDSDK_CONFIG}',
        result.config.paths['global_config_dir'])

  def testRunDiagnosticFlag(self):
    network_check_mock = self.StartObjectPatch(
        network_diagnostics.NetworkDiagnostic, 'RunChecks')
    property_check_mock = self.StartObjectPatch(
        property_diagnostics.PropertyDiagnostic, 'RunChecks')
    info_holder_mock = self.StartObjectPatch(info_holder, 'InfoHolder')
    self.Run('info --run-diagnostics')
    self.assertTrue(network_check_mock.called)
    self.assertTrue(property_check_mock.called)
    self.assertFalse(info_holder_mock.called)

  def testInfo_ToolLocation(self):
    git_str = 'this is my git'
    ssh_str = 'this is my ssh'
    self.StartObjectPatch(info_holder.ToolsInfo, '_GitVersion',
                          return_value=git_str)
    self.StartObjectPatch(info_holder.ToolsInfo, '_SshVersion',
                          return_value=ssh_str)
    self.Run('info')
    self.AssertOutputContains('git: [{}]'.format(git_str))
    self.AssertOutputContains('ssh: [{}]'.format(ssh_str))

  @sdk_test_base.Filters.RunOnlyInBundle
  def testInfoWithToolsOnPath(self):
    # Mock out using actual $PATH.
    self.StartObjectPatch(update_manager.UpdateManager,
                          'FindAllOldToolsOnPath',
                          return_value=set(['a.py']))
    self.StartObjectPatch(update_manager.UpdateManager,
                          'FindAllDuplicateToolsOnPath',
                          return_value=set(['b.py']))
    self.Run('info')
    # Make sure that expected messaging results from old tools on the PATH.
    self.AssertOutputContains('WARNING: There are old versions of the Google '
                              'Cloud Platform tools on your system PATH.\n'
                              '  a.py')
    self.AssertOutputContains('There are alternate versions of the following '
                              'Google Cloud Platform tools on your system '
                              'PATH.\n'
                              '  b.py')


class InfoModeTests(cli_test_base.CliTestBase):

  def SetUp(self):
    self.run_diagnostics = self.StartObjectPatch(
        info_command, '_RunDiagnostics')

  def testInfo(self):
    self.Run('info')
    self.AssertOutputContains('Platform:')
    self.AssertOutputNotContains('Contents of log file:')
    self.run_diagnostics.not_called()

  def testInfoShowLog(self):
    contents = 'test log contents'
    info = info_holder.InfoHolder()
    info.logs.last_log = 'test.log'
    info.logs.LastLogContents = lambda: contents
    self.StartObjectPatch(info_holder, 'InfoHolder', return_value=info)
    self.Run('info --show-log')
    self.AssertOutputNotContains('Platform:')
    self.AssertOutputContains('Contents of log file:')
    self.AssertOutputContains(contents)
    self.run_diagnostics.not_called()

  def testInfoRunDiagnostics(self):
    self.Run('info --run-diagnostics')
    self.AssertOutputNotContains('Platform:')
    self.AssertOutputNotContains('Contents of log file:')
    self.run_diagnostics.called_once()

  def testModeMutex(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --run-diagnostics: At most one of --run-diagnostics | '
        '--show-log may be specified.'):
      self.Run('info --run-diagnostics --show-log')


class InfoWithProxyFromEnvironmentTests(cli_test_base.CliTestBase):

  def testInfo(self):
    self.StartDictPatch(
        'os.environ',
        {'http_proxy': 'https://baduser:badpassword@badproxy.com:8080',
         'https_proxy': 'https://baduser:badpassword@badproxy.com:8081'})
    self.Run('info')
    self.AssertOutputContains(textwrap.dedent("""\
        Environmental Proxy Settings:
          type: [http]
          address: [badproxy.com]
          port: [8081]
          username: [baduser]
          password: [badpassword]"""))

  def testInfoWithJsonOutput(self):
    self.StartDictPatch(
        'os.environ',
        {'http_proxy': 'https://baduser:badpassword@badproxy.com:8080',
         'https_proxy': 'https://baduser:badpassword@badproxy.com:8081'})
    self.Run(['info', '--format=json'])
    self.AssertOutputContains("""\
  "env_proxy": {
    "address": "badproxy.com",
    "password": "badpassword",
    "port": 8081,
    "type": "http",
    "username": "baduser"
  },""")


if __name__ == '__main__':
  test_case.main()
