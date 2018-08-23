# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
import re
import tempfile

from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import runtime_registry
from googlecloudsdk.command_lib.app import staging
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock


def _FakeExec(return_code=0):
  def _Exec(args, no_exit=False, out_func=None, err_func=None):
    unused_args = args
    unused_no_exit = no_exit
    out_func('out\n')
    err_func('err\n')
    return return_code
  return _Exec


class StagerRegistryTest(sdk_test_base.WithLogCapture):
  """Ensure that default- and beta staging registries works as intended."""

  # Use fake command strings in order to easier compare for equality
  _DEFAULT_REGISTRY = {
      runtime_registry.RegistryEntry('intercal', {env.FLEX}):
          'fake-intercal-command',
      runtime_registry.RegistryEntry('x86-asm', {env.STANDARD}):
          'fake-x86-asm-command',
  }

  _REGISTRY_BETA = {
      runtime_registry.RegistryEntry('intercal', {env.FLEX}):
          'fake-intercal-beta-command',
      runtime_registry.RegistryEntry('chicken', {env.STANDARD}):
          'fake-chicken-beta-command',
  }

  def _MockDefaultRegistries(self):
    self.StartObjectPatch(staging, '_STAGING_REGISTRY',
                          new=self._DEFAULT_REGISTRY)
    self.StartObjectPatch(staging, '_STAGING_REGISTRY_BETA',
                          new=self._REGISTRY_BETA)

  def SetUp(self):
    self.staging_area = '/staging-area'

  def testRegistry_DefaultMappings(self):
    """Ensures the default registry works is what it was originally set to."""
    self._MockDefaultRegistries()
    expected = {
        ('intercal', env.FLEX): 'fake-intercal-command',
        ('x86-asm', env.STANDARD): 'fake-x86-asm-command',
        ('chicken', env.STANDARD): staging.NoopCommand(),
    }
    registry = staging.GetRegistry()
    for key, value in expected.items():
      self.assertEqual(registry.Get(*key), value)

  def testRegistry_BetaMappings(self):
    """Ensures entries in beta- overrides entries in default-registry."""
    self._MockDefaultRegistries()
    expected = {
        ('intercal', env.FLEX): 'fake-intercal-beta-command',
        ('x86-asm', env.STANDARD): 'fake-x86-asm-command',
        ('chicken', env.STANDARD): 'fake-chicken-beta-command',
    }
    registry = staging.GetBetaRegistry()
    for key, value in expected.items():
      self.assertEqual(registry.Get(*key), value)

  def testRegistry_FlexGoRegexp(self):
    """Tests that the regexp for the Go staging entry does the right thing."""
    registry = staging.GetRegistry()

    def Good(runtime):
      command = registry.Get(runtime, env.FLEX)
      self.assertFalse(isinstance(command, staging.NoopCommand))
    def Bad(runtime):
      command = registry.Get(runtime, env.FLEX)
      self.assertTrue(isinstance(command, staging.NoopCommand))

    Good('go')
    Good('go1.7')
    Good('go1.8')
    Good('go1.8.9')
    Good('go1.8a')
    Good('go1.9')
    Good('go1.10')
    Good('go1.abc')
    Bad('go1')
    Bad('go2')
    Bad('go2.')
    Bad('go10')
    Bad('go1.')
    Bad('something-ends-with-go1.8')
    Bad('gs://my-bucket/go1.8')

  def testRegistry_StandardGoRegexp(self):
    """Tests that the regexp for the Go staging entry does the right thing."""
    registry = staging.GetRegistry()

    def Good(runtime):
      command = registry.Get(runtime, env.STANDARD)
      self.assertFalse(
          isinstance(command, staging.NoopCommand),
          '\'%s\' should be valid' % runtime)
    def Bad(runtime):
      command = registry.Get(runtime, env.STANDARD)
      self.assertTrue(
          isinstance(command, staging.NoopCommand),
          '\'%s\' should be invalid' % runtime)

    Good('go')
    Good('go1.7')
    Good('go1.8')
    Good('go1.8.9')
    Good('go1.8a')
    Good('go1.9')
    Good('go1.10')
    Good('go1.abc')
    Good('go110')
    Good('go111')
    Good('go111beta1')
    Good('go111rc2')
    Bad('go1')
    Bad('go2')
    Bad('go2.')
    Bad('go10')
    Bad('go1.')
    Bad('something-ends-with-go1.8')
    Bad('gs://my-bucket/go1.8')


def _GermanMapper(command_path, descriptor, app_dir, staging_dir):
  """Used as a custom mapper from parameters to invocation."""
  return [command_path, '-dir', staging_dir, '-yaml', descriptor, app_dir]


class StagerMockExecTest(sdk_test_base.WithLogCapture):
  """Tests the staging code by mocking executables."""

  _REGISTRY = runtime_registry.Registry({
      runtime_registry.RegistryEntry('intercal', {env.FLEX}):
          staging._BundledCommand('intercal-flex', 'intercal-flex.exe'),
      runtime_registry.RegistryEntry('x86-asm', {env.STANDARD}):
          staging._BundledCommand('x86-asm-standard', 'x86-asm-standard.exe',
                                  'app-engine-x86-asm'),
      runtime_registry.RegistryEntry('german', {env.STANDARD}):
          staging._BundledCommand('german-standard', 'german-standard.exe',
                                  mapper=_GermanMapper),
  }, default=staging.NoopCommand())

  _OUTPUT_PATTERN = (r'-+ STDOUT -+\n'
                     r'out\n'
                     r'-+ STDERR -+\n'
                     r'err\n'
                     r'-+')

  _SUCCESS_MESSAGE = 'Executing staging command: [{command}]'

  _ERROR_MESSAGE = (
      'Staging command [{command}] failed with return code [{code}].')

  def SetUp(self):
    self.staging_area = '/staging-area'
    self.stager = staging.Stager(self._REGISTRY, self.staging_area)
    self.exec_mock = self.StartObjectPatch(execution_utils, 'Exec',
                                           side_effect=_FakeExec())
    self.sdk_root_mock = self.StartPropertyPatch(
        config.Paths, 'sdk_root', return_value='sdk_root_dir')
    self.mkdtemp_mock = self.StartObjectPatch(
        tempfile, 'mkdtemp', autospec=True, return_value='tmp_dir')
    self.StartObjectPatch(platforms.OperatingSystem, 'Current',
                          return_value=platforms.OperatingSystem.LINUX)

  def testStage_StagingDir(self):
    """Ensures that the staging dir is created properly."""
    app_dir = self.stager.Stage('app.yaml', 'dir', 'intercal',
                                env.FLEX)
    self.assertEqual(app_dir, 'tmp_dir')
    self.mkdtemp_mock.assert_called_once_with(dir='/staging-area')

  def testStage_MismatchedRuntime(self):
    self.assertIsNone(
        self.stager.Stage('app.yaml', 'dir', 'intercal',
                          env.STANDARD))
    self.AssertOutputEquals('')
    self.AssertLogNotContains('err')  # Log will have debug messages
    self.exec_mock.assert_not_called()
    self.mkdtemp_mock.assert_not_called()

  def testStage_MismatchedEnvironment(self):
    self.assertIsNone(
        self.stager.Stage('app.yaml', 'dir', 'intercal',
                          env.STANDARD))
    self.AssertOutputEquals('')
    self.AssertLogNotContains('err')  # Log will have debug messages
    self.exec_mock.assert_not_called()
    self.mkdtemp_mock.assert_not_called()

  def testStage_NoSdkRoot(self):
    self.sdk_root_mock.return_value = None
    with self.assertRaises(staging.NoSdkRootError):
      self.stager.Stage('app.yaml', 'dir', 'intercal',
                        env.FLEX)
    self.exec_mock.assert_not_called()

  def testStage_StagingCommandFailed(self):
    self.exec_mock.side_effect = _FakeExec(return_code=1)
    args = [os.path.join('sdk_root_dir', 'intercal-flex'), 'app.yaml',
            'dir', 'tmp_dir']
    command = ' '.join(args)
    expected_pattern = (
        re.escape(self._ERROR_MESSAGE.format(command=command, code=1)) +
        '\n\n' + self._OUTPUT_PATTERN)
    with self.assertRaisesRegex(staging.StagingCommandFailedError,
                                expected_pattern):
      self.stager.Stage('app.yaml', 'dir', 'intercal',
                        env.FLEX)
    self.exec_mock.assert_called_once_with(
        args, no_exit=True, out_func=mock.ANY, err_func=mock.ANY)

  def testStage_Success(self):
    args = [os.path.join('sdk_root_dir', 'intercal-flex'), 'app.yaml',
            'dir', 'tmp_dir']
    self.stager.Stage('app.yaml', 'dir', 'intercal',
                      env.FLEX)
    self.exec_mock.assert_called_once_with(
        args, no_exit=True, out_func=mock.ANY, err_func=mock.ANY)
    command = ' '.join(args)
    self.AssertLogMatches(
        re.escape(self._SUCCESS_MESSAGE.format(command=command)))
    self.AssertLogMatches(self._OUTPUT_PATTERN)
    self.mkdtemp_mock.assert_called_once_with(dir='/staging-area')

  def testStage_SuccessWindows(self):
    self.StartObjectPatch(platforms.OperatingSystem, 'Current',
                          return_value=platforms.OperatingSystem.WINDOWS)
    args = [os.path.join('sdk_root_dir', 'intercal-flex.exe'),
            'app.yaml', 'dir', 'tmp_dir']
    self.stager.Stage('app.yaml', 'dir', 'intercal',
                      env.FLEX)
    self.exec_mock.assert_called_once_with(
        args, no_exit=True, out_func=mock.ANY, err_func=mock.ANY)
    command = ' '.join(args)
    self.AssertLogMatches(
        re.escape(self._SUCCESS_MESSAGE.format(command=command)))
    self.AssertLogMatches(self._OUTPUT_PATTERN)
    self.mkdtemp_mock.assert_called_once_with(dir='/staging-area')

  def testStage_SuccessInstalledComponent(self):
    ensure_installed_mock = self.StartObjectPatch(update_manager.UpdateManager,
                                                  'EnsureInstalledAndRestart')
    args = [os.path.join('sdk_root_dir', 'x86-asm-standard'),
            'app.yaml', 'dir', 'tmp_dir']
    self.stager.Stage('app.yaml', 'dir', 'x86-asm',
                      env.STANDARD)
    self.exec_mock.assert_called_once_with(
        args, no_exit=True, out_func=mock.ANY, err_func=mock.ANY)
    command = ' '.join(args)
    self.AssertLogMatches(
        re.escape(self._SUCCESS_MESSAGE.format(command=command)))
    self.AssertLogMatches(self._OUTPUT_PATTERN)
    ensure_installed_mock.assert_called_once_with(['app-engine-x86-asm'],
                                                  msg=mock.ANY)
    self.mkdtemp_mock.assert_called_once_with(dir='/staging-area')

  def testStage_CustomMapper(self):
    """Test that a custom mapper function can be invoked."""
    args = [os.path.join('sdk_root_dir', 'german-standard'), '-dir', 'tmp_dir',
            '-yaml', 'app.yaml', 'dir']
    self.stager.Stage('app.yaml', 'dir', 'german',
                      env.STANDARD)
    self.exec_mock.assert_called_once_with(
        args, no_exit=True, out_func=mock.ANY, err_func=mock.ANY)
    command = ' '.join(args)
    self.AssertLogMatches(
        re.escape(self._SUCCESS_MESSAGE.format(command=command)))
    self.AssertLogMatches(self._OUTPUT_PATTERN)
    self.mkdtemp_mock.assert_called_once_with(dir='/staging-area')


class StagerRealExecutableTest(sdk_test_base.WithLogCapture):
  """Tests the staging code using real executables."""

  _REGISTRY = runtime_registry.Registry({
      runtime_registry.RegistryEntry('success', {env.FLEX}):
          staging._BundledCommand('success.sh', 'success.cmd'),
      runtime_registry.RegistryEntry('failure', {env.FLEX}):
          staging._BundledCommand('failure.sh', 'failure.cmd')
  }, default=staging.NoopCommand())

  _SUCCESS_OUTPUT_PATTERN = (r'-+ STDOUT -+\r?\n'
                             r'out\r?\n'
                             r'-+ STDERR -+\r?\n'
                             r'service-yaml path: app.yaml\r?\n'
                             r'app-dir path: .\r?\n'
                             r'-+')

  _FAILURE_PATTERN = (r'Staging command '
                      r'\[\S+failure.(?:sh|cmd) app.yaml . \S+\] '
                      r'failed with return code \[1\].\r?\n\r?\n'
                      r'-+ STDOUT -+\r?\n'
                      r'out\r?\n'
                      r'-+ STDERR -+\r?\n'
                      r'service.yaml path: app.yaml\r?\n'
                      r'app-dir path: .\r?\n'
                      r'-+')

  def SetUp(self):
    scripts_dir = self.Resource(
        'tests', 'unit', 'command_lib', 'app', 'testdata', 'scripts')
    self.StartObjectPatch(config.Paths, 'sdk_root',
                          new_callable=mock.PropertyMock,
                          return_value=scripts_dir)
    self.staging_area = tempfile.mkdtemp()
    self.stager = staging.Stager(self._REGISTRY, self.staging_area)

  def testStage_Success(self):
    app_dir = self.stager.Stage('app.yaml', '.', 'success',
                                env.FLEX)
    self.AssertFileExistsWithContents(
        'app.yaml contents\n', os.path.join(app_dir, 'app.yaml'))
    self.AssertLogMatches(self._SUCCESS_OUTPUT_PATTERN)

  def testStage_Failure(self):
    with self.assertRaisesRegex(staging.StagingCommandFailedError,
                                self._FAILURE_PATTERN):
      self.stager.Stage('app.yaml', '.', 'failure',
                        env.FLEX)


class MapperTests(test_case.Base):
  """Test that the command mapper assembles correct arg lists."""

  def SetUp(self):
    self.command_path = '/command/path'
    self.app_yaml_descriptor = '/app-dir/app.yaml'
    self.app_dir = '/app-dir'
    self.staging_dir = '/tmp/staging-dir'
    self.require_java = self.StartObjectPatch(java, 'RequireJavaInstalled',
                                              return_value='/bin/java')

  def testJavaMapper(self):
    """Java staging doesn't conform, but uses a different mapper."""
    args = [
        self.command_path,
        '*ignored*',
        self.app_dir,
        self.staging_dir]
    actual = staging._JavaStagingMapper(*args)
    expected = [
        '/bin/java',
        '-classpath',
        '/command/path',
        'com.google.appengine.tools.admin.AppCfg',
        '--enable_new_staging_defaults',
        'stage',
        '/app-dir',
        '/tmp/staging-dir',
    ]
    self.assertSequenceEqual(actual, expected)

  def testJavaMapper_MissingJava(self):
    """Java staging requires a Java installation."""
    self.require_java.side_effect = java.JavaError('Missing Java')
    args = [
        self.command_path,
        '*ignored*',
        self.app_dir,
        self.staging_dir]
    with self.assertRaises(java.JavaError):
      staging._JavaStagingMapper(*args)


class NoopCommandTest(sdk_test_base.WithLogCapture):
  """Tests for NoopCommand."""

  def SetUp(self):
    self.staging_area = os.path.join(self.temp_path, 'staging')
    files.MakeDir(self.staging_area)
    self.app_dir = os.path.join(self.temp_path, 'app_dir')
    files.MakeDir(self.app_dir)
    self.descriptor = os.path.join(self.app_dir, 'descriptor.yaml')

  def testRun(self):
    """Tests that Run does nothing."""
    command = staging.NoopCommand()

    result = command.Run(self.staging_area, self.descriptor, self.app_dir)

    self.assertIsNone(result)
    self.assertEqual(os.listdir(self.staging_area), [],
                     'NoopCommand should not modify the staging area.')
    self.assertEqual(os.listdir(self.app_dir), [],
                     'NoopCommand should not modify the app directory.')

  def testEnsureInstalled(self):
    """Tests that EnsureInstalled does nothing."""
    command = staging.NoopCommand()

    command.EnsureInstalled()

    self.assertEqual(os.listdir(self.staging_area), [],
                     'NoopCommand should not modify the staging area.')
    self.assertEqual(os.listdir(self.app_dir), [],
                     'NoopCommand should not modify the app directory.')

  def testGetPath(self):
    """Tests that GetPath does nothing."""
    command = staging.NoopCommand()

    result = command.GetPath()

    self.assertIsNone(result, 'NoopCommand has no associated path.')


class ExecutableCommandTest(sdk_test_base.WithLogCapture):
  """Tests for ExecutableCommand."""

  def SetUp(self):
    self.staging_area = os.path.join(self.temp_path, 'staging')
    files.MakeDir(self.staging_area)
    self.app_dir = os.path.join(self.temp_path, 'app_dir')
    files.MakeDir(self.app_dir)
    self.descriptor = os.path.join(self.app_dir, 'descriptor.yaml')
    self.path = os.path.join(self.temp_path, 'my-command')

  def testRun(self):
    """Tests that ExecutableCommand executes."""
    command = staging.ExecutableCommand(self.path)
    self.exec_mock = self.StartObjectPatch(execution_utils, 'Exec',
                                           side_effect=_FakeExec())

    result = command.Run(self.staging_area, self.descriptor, self.app_dir)

    self.assertEqual(os.path.dirname(result), self.staging_area,
                     'The result of Run should be a temporary directory in '
                     'the staging area.')
    self.exec_mock.assert_called_once_with(
        [self.path, self.descriptor, self.app_dir, result],
        no_exit=True, out_func=mock.ANY, err_func=mock.ANY)
    self.AssertLogContains('out')
    self.AssertLogContains('err')

  def testEnsureInstalled(self):
    """Tests that EnsureInstalled does nothing."""
    command = staging.ExecutableCommand(self.temp_path)

    command.EnsureInstalled()

    self.assertEqual(set(os.listdir(self.temp_path)),
                     set(['staging', 'app_dir']),
                     'EnsureInstalled should not modify the temp dir.')
    self.assertEqual(os.listdir(self.staging_area), [],
                     'EnsureInstalled should not modify the staging area.')
    self.assertEqual(os.listdir(self.app_dir), [],
                     'EnsureInstalled should not modify the app directory.')

  def testGetPath(self):
    command = staging.ExecutableCommand(self.path)

    result = command.GetPath()

    self.assertEqual(result, self.path)

  def testGetFromInput_OnPath(self):
    self.StartObjectPatch(files, 'FindExecutableOnPath', return_value=self.path)

    command = staging.ExecutableCommand.FromInput('my-command')

    self.assertEqual(command.GetPath(), self.path)

  def testGetFromInput_FileExists(self):
    path = self.Touch(self.temp_path, 'my-command')
    command = staging.ExecutableCommand.FromInput(path)

    self.assertEqual(command.GetPath(), path)

  def testGetFromInput_FileDoesNotExist(self):
    with self.assertRaises(staging.StagingCommandNotFoundError):
      staging.ExecutableCommand.FromInput(self.path)


if __name__ == '__main__':
  test_case.main()
