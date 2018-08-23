# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.core.updater import util
import mock


class ComponentsTest(cli_test_base.CliTestBase, sdk_test_base.WithLogCapture,
                     util.Base):

  def SetUp(self):
    self.platform = platforms.Platform(platforms.OperatingSystem.WINDOWS,
                                       platforms.Architecture.x86)
    self.real_manager = update_manager.UpdateManager(
        self.sdk_root_path, self.URLFromFile(self.Resource('parsetest.json')),
        platform_filter=self.platform)
    # This is because disable_updater is true for linux distributions which
    # causes packaging tests fo fail.
    config.INSTALLATION_CONFIG.disable_updater = False
    # This is for testListOnlyLocalState but needs to be done in SetUp because
    # once the updater patcher starts, calls to Update start throwing errors.
    self.real_manager.Update(['c1'])

    patcher = mock.patch(
        'googlecloudsdk.core.updater.update_manager.UpdateManager',
        autospec=True)
    self.addCleanup(patcher.stop)
    self.updater_mock = patcher.start()

    patcher = mock.patch('googlecloudsdk.core.util.platforms.Platform',
                         autospec=True)
    self.addCleanup(patcher.stop)
    self.platform_mock = patcher.start()
    self.platform_mock.Current.side_effect = lambda *args: args

  def testSetup(self):
    self.updater_mock.return_value.List.return_value = ([], None, None)
    self.Run('components list')
    self.updater_mock.assert_called_once_with(
        sdk_root=None, url=None, platform_filter=(None, None))

    self.updater_mock.reset_mock()
    self.Run('components list --sdk-root-override=/foo')
    self.updater_mock.assert_called_once_with(
        sdk_root='/foo', url=None, platform_filter=(None, None))

    self.updater_mock.reset_mock()
    self.Run('components list --snapshot-url-override=file:///foo')
    self.updater_mock.assert_called_once_with(
        sdk_root=None, url='file:///foo', platform_filter=(None, None))

    self.updater_mock.reset_mock()
    self.Run('components list --operating-system-override=WINDOWS')
    self.updater_mock.assert_called_once_with(
        sdk_root=None, url=None,
        platform_filter=(platforms.OperatingSystem.WINDOWS, None))

    self.updater_mock.reset_mock()
    self.Run('components list --architecture-override=x86')
    self.updater_mock.assert_called_once_with(
        sdk_root=None, url=None,
        platform_filter=(None, platforms.Architecture.x86))

    self.updater_mock.reset_mock()
    with self.assertRaisesRegex(
        exceptions.ToolException,
        r'Could not parse \[junk\] into a valid Architecture\.'):
      self.Run('components list --architecture-override=junk')

    patcher = mock.patch(
        'googlecloudsdk.core.config.INSTALLATION_CONFIG.'
        'IsAlternateReleaseChannel', return_value=True)
    self.addCleanup(patcher.stop)
    patcher.start()

    self.updater_mock.reset_mock()
    self.Run('components list')
    self.AssertErrContains('WARNING: You are using alternate release channel')

  def testList(self):
    self.updater_mock.return_value = self.real_manager
    self.platform_mock.Current.side_effect = lambda *args: self.platform

    self.Run('components list --format csv(id,is_hidden,state.name)')

    self.AssertOutputEquals("""\
id,is_hidden,status
c2,False,Not Installed
c1,False,Installed
""")

    self.AssertErrContains('Your current Cloud SDK version is: ' +
                           config.INSTALLATION_CONFIG.version)
    self.AssertErrContains('The latest available version is: 1.2.3')

  def testList_ShowHidden(self):
    self.updater_mock.return_value = self.real_manager
    self.platform_mock.Current.side_effect = lambda *args: self.platform

    self.Run('components list --format csv(id,is_hidden,state.name) '
             '--show-hidden')

    self.AssertOutputEquals("""\
id,is_hidden,status
c2,False,Not Installed
c3,True,Not Installed
c1,False,Installed
""")

  def testListOnlyLocalState(self):
    self.updater_mock.return_value = self.real_manager
    self.platform_mock.Current.side_effect = lambda *args: self.platform

    self.Run('components list --format csv(id,is_hidden,state.name) '
             '--only-local-state')

    self.AssertOutputEquals("""\
id,is_hidden,name
c1,False,
""")

  def testListEpilog(self):
    self.updater_mock.return_value = self.real_manager
    self.platform_mock.Current.side_effect = lambda *args: self.platform

    self.Run('components list')

    self.AssertErrContains('Your current Cloud SDK version is: ' +
                           config.INSTALLATION_CONFIG.version)
    self.AssertErrContains('The latest available version is: 1.2.3')
    self.AssertErrContains(
        'To install or remove components at your current SDK version '
        '[{current}], run:'.format(current=config.INSTALLATION_CONFIG.version))
    self.AssertErrContains(
        'To update your SDK installation to the latest version [1.2.3], run:')

  def testRemove(self):
    self.Run('components remove a b')
    self.updater_mock.return_value.Remove.assert_called_once_with(
        ['a', 'b'], allow_no_backup=False)

  def testRestore(self):
    self.Run('components restore')
    self.updater_mock.return_value.Restore.assert_called_once_with()

  def testUpdate(self):
    self.Run('components update')
    self.updater_mock.return_value.Update.assert_called_once_with(
        [], allow_no_backup=False, version=None)

    self.updater_mock.reset_mock()
    self.Run('components update a b')
    self.updater_mock.return_value.Update.assert_called_once_with(
        ['a', 'b'], allow_no_backup=False, version=None)

    self.WriteInput('Y\n')
    self.updater_mock.reset_mock()
    self.Run('components update a b')
    self.updater_mock.return_value.Install.assert_called_once_with(
        ['a', 'b'], allow_no_backup=False)

    self.updater_mock.reset_mock()
    self.Run('components update a b --version 1')
    self.updater_mock.return_value.Update.assert_called_once_with(
        ['a', 'b'], allow_no_backup=False, version='1')

    self.updater_mock.reset_mock()
    self.Run('components update a b --version 1')
    self.updater_mock.return_value.Update.assert_called_once_with(
        ['a', 'b'], allow_no_backup=False, version='1')

  def testInstall(self):
    self.Run('components install a')
    self.updater_mock.return_value.Install.assert_called_once_with(
        ['a'], allow_no_backup=False)

  def testReinstall(self):
    self.Run('components reinstall')
    self.updater_mock.return_value.Reinstall.assert_called_once_with()

  def testPostProcess(self):
    root = os.path.realpath(self.CreateTempDir('root'))
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value=root)
    compile_mock = self.StartPatch('compileall.compile_dir')

    self.Run('components post-process')

    self.assertEqual(compile_mock.call_count, 4)

  def testPostProcessNoResourceCache(self):
    root = os.path.realpath(self.CreateTempDir('root'))
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value=root)
    compile_mock = self.StartPatch('compileall.compile_dir')

    self.Run('components post-process')

    self.assertEqual(compile_mock.call_count, 4)

if __name__ == '__main__':
  cli_test_base.main()
