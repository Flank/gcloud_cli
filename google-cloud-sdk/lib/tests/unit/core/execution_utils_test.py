# -*- coding: utf-8 -*- #
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Unit tests for the file_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import io
import os
import re
import signal
import subprocess
import sys

from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import encoding
from tests.lib import sdk_test_base
from tests.lib import test_case


class ExecutionTests(sdk_test_base.WithLogCapture,
                     sdk_test_base.WithOutputCapture):
  _SCRIPT = 'test.' + ('cmd' if test_case.Filters.IsOnWindows() else 'sh')

  def SetUp(self):
    self.scripts_dir = self.Resource(
        'tests', 'unit', 'core', 'test_data', 'execution_utils', 'scripts')
    self.exit_mock = self.StartObjectPatch(sys, 'exit')

    # Set encoding so sys.stdout and sys.stderr mocks can accept unicode
    self.SetEncoding('utf8')

  def testExec_WithExit(self):
    execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                         in_str='test Ṳᾔḯ¢◎ⅾℯ input\n')
    self.AssertOutputNotContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertLogNotContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.exit_mock.assert_called_once_with(1)

  def testExec_WithArgsWithExit(self):
    # Also tests unicode args are handled correctly. Exec() raises exception
    # if args are not encoded properly.
    execution_utils.Exec(
        [os.path.join(self.scripts_dir, self._SCRIPT),
         'Ṳᾔḯ¢◎ⅾℯ'.encode('utf7')],
        in_str='fḯsh',
        out_func=sys.stdout.write,
        err_func=sys.stderr.write,
    )
    # The script above just echoes what we provided which is python encoded
    # value. This just make sure that arguments are encoded by default.
    self.assertMultiLineEqual(
        'input: fḯsh\n'
        'argument: +HnIflB4vAKIlziF+IS8-\n'
        'test Ṳᾔḯ¢◎ⅾℯ output\n',
        encoding.Decode(self.stdout.getvalue()))
    self.AssertErrEquals('test Ṳᾔḯ¢◎ⅾℯ error\n')
    self.AssertLogNotContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.exit_mock.assert_called_once_with(1)

  def testExec_NoExit(self):
    ret_val = execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                                   in_str='test Ṳᾔḯ¢◎ⅾℯ input\n',
                                   no_exit=True)
    self.assertEqual(ret_val, 1)
    self.AssertOutputNotContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertLogNotContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.assertFalse(self.exit_mock.called)

  def testExecPipeOut(self):
    execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                         in_str='test Ṳᾔḯ¢◎ⅾℯ input\n',
                         out_func=log.out.write)
    self.exit_mock.assert_called_once_with(1)
    self.AssertOutputContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertErrNotContains('test Ṳᾔḯ¢◎ⅾℯ error')

  def testExecPipeErr(self):
    execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                         in_str='test Ṳᾔḯ¢◎ⅾℯ input\n',
                         err_func=log.err.write)
    self.exit_mock.assert_called_once_with(1)
    self.AssertOutputNotContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertErrContains('test Ṳᾔḯ¢◎ⅾℯ error')

  def testExecPipeIn(self):
    execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                         in_str='test Ṳᾔḯ¢◎ⅾℯ input\n')
    self.exit_mock.assert_called_once_with(1)
    # Has no output
    self.AssertOutputNotContains('test Ṳᾔḯ¢◎ⅾℯ input')
    self.AssertOutputNotContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertErrNotContains('test Ṳᾔḯ¢◎ⅾℯ error')

  def testExecPipeInAndOut(self):
    execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                         out_func=log.out.write,
                         in_str='test Ṳᾔḯ¢◎ⅾℯ input\n')
    self.exit_mock.assert_called_once_with(1)
    self.AssertOutputContains('test Ṳᾔḯ¢◎ⅾℯ input')
    self.AssertOutputContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertErrNotContains('test Ṳᾔḯ¢◎ⅾℯ error')

  def testExecPipeOutAndErr(self):
    execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                         out_func=log.out.write,
                         err_func=log.err.write,
                         in_str='test Ṳᾔḯ¢◎ⅾℯ input\n')
    self.exit_mock.assert_called_once_with(1)
    self.AssertOutputContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertErrContains('test Ṳᾔḯ¢◎ⅾℯ error')

  def testExecPipeInAndOutAndErr(self):
    execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                         out_func=log.out.write, err_func=log.err.write,
                         in_str='test Ṳᾔḯ¢◎ⅾℯ input\n')
    self.exit_mock.assert_called_once_with(1)
    self.AssertOutputContains('test Ṳᾔḯ¢◎ⅾℯ input')
    self.AssertOutputContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertErrContains('test Ṳᾔḯ¢◎ⅾℯ error')

  def testExecPipeThroughLogger(self):
    execution_utils.Exec(os.path.join(self.scripts_dir, self._SCRIPT),
                         err_func=log.file_only_logger.debug,
                         out_func=log.file_only_logger.debug,
                         in_str='test Ṳᾔḯ¢◎ⅾℯ input\n')
    self.exit_mock.assert_called_once_with(1)
    self.AssertLogContains('test Ṳᾔḯ¢◎ⅾℯ output')
    self.AssertLogContains('test Ṳᾔḯ¢◎ⅾℯ error')

  def testExec_FilePermissionError(self):
    error_message = 'Permission denied'
    popen_mock = self.StartObjectPatch(subprocess, 'Popen')
    popen_mock.side_effect = OSError(errno.EACCES, error_message)
    self.assertRaises(execution_utils.PermissionError)
    with self.assertRaisesRegex(execution_utils.PermissionError, re.escape(
        '\nPlease verify that you have execute permission for all '
        'files in your CLOUD SDK bin'
        ' folder')):
      execution_utils.Exec(
          os.path.join(self.scripts_dir, self._SCRIPT))

  def testExec_InvalidCommandError(self):
    error_message = 'No such file or directory'
    fake_command = ['fake', 'command']
    popen_mock = self.StartObjectPatch(subprocess, 'Popen')
    popen_mock.side_effect = OSError(errno.ENOENT, error_message)
    self.assertRaises(OSError)
    with self.assertRaisesRegex(execution_utils.InvalidCommandError, re.escape(
        '{0}: command not found'.format(fake_command[0]))):
      execution_utils.Exec(fake_command)

  def testExec_OtherOSError(self):
    error_message = 'No such process'
    popen_mock = self.StartObjectPatch(subprocess, 'Popen')
    popen_mock.side_effect = OSError(errno.ESRCH, error_message)
    self.assertRaises(OSError)
    with self.assertRaisesRegex(OSError, re.escape(
        '[Errno 3] {0}'.format(error_message))):
      execution_utils.Exec(
          os.path.join(self.scripts_dir, self._SCRIPT))


class GetPythonExecutableTests(test_case.TestCase):

  def testGetPythonExecutableEnvironment(self):
    self.StartEnvPatch({'CLOUDSDK_PYTHON': '/env/python'}, clear=True)
    self.assertEqual(execution_utils.GetPythonExecutable(),
                     '/env/python')

  def testGetPythonExecutableNoEnvironment(self):
    self.StartEnvPatch({}, clear=True)
    self.StartObjectPatch(sys, 'executable', new='/current/python')
    self.assertEqual(execution_utils.GetPythonExecutable(), '/current/python')


class ArgsForPythonToolTests(test_case.TestCase):

  def SetUp(self):
    get_python_mock = self.StartObjectPatch(execution_utils,
                                            'GetPythonExecutable')
    get_python_mock.return_value = '/path/to/python'

  def testArgsForPythonTool(self):
    self.StartEnvPatch({}, clear=True)
    self.assertEqual(execution_utils.ArgsForPythonTool('foo.py'),
                     ['/path/to/python', 'foo.py'])

  def testArgsForPythonToolArgs(self):
    self.StartEnvPatch({}, clear=True)
    self.assertEqual(execution_utils.ArgsForPythonTool('foo.py', 'a', 'b'),
                     ['/path/to/python', 'foo.py', 'a', 'b'])

  def testArgsForPythonToolEnvironArgs(self):
    self.StartEnvPatch({'CLOUDSDK_PYTHON_ARGS': '--bar'}, clear=True)
    self.assertEqual(execution_utils.ArgsForPythonTool('foo.py'),
                     ['/path/to/python', '--bar', 'foo.py'])

  def testArgsForPythonToolPython(self):
    self.StartEnvPatch({}, clear=True)
    self.assertEqual(execution_utils.ArgsForPythonTool('foo.py',
                                                       python='/other/python'),
                     ['/other/python', 'foo.py'])


class ArgsForGcloudTests(test_case.TestCase):

  def testArgsForGcloudNormal(self):
    self.StartEnvPatch({}, clear=True)
    self.StartObjectPatch(sys, 'executable', new='/path/to/python')
    gcloud_path_mock = self.StartObjectPatch(config, 'GcloudPath')
    gcloud_path_mock.return_value = '/abc/def/gcloud.py'
    self.assertEqual(execution_utils.ArgsForGcloud(), ['/path/to/python',
                                                       '/abc/def/gcloud.py'])

  def testArgsForGcloudHermeticPar(self):
    self.StartEnvPatch({}, clear=True)
    self.StartObjectPatch(sys, 'executable', new=None)
    self.StartObjectPatch(sys, 'argv', new=['/abc/def/gcloud.par', 'info'])
    self.assertEqual(execution_utils.ArgsForGcloud(), ['/abc/def/gcloud.par'])


class RaisesKeyboardInterruptTest(test_case.TestCase):

  @test_case.Filters.DoNotRunOnWindows
  def testRaisesKeyboardInterrupt(self):
    # The code this tests works on Windows, however, it is not possible to send
    # a SIGINT signal on Windows.  The Windows shell catches CTRL-C and converts
    # it into a SIGINT (which is why the code works.  Also sending a
    # CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaises(KeyboardInterrupt):
      with execution_utils.RaisesKeyboardInterrupt():
        os.kill(os.getpid(), signal.SIGINT)


class UninterruptibleSectionTests(test_case.WithOutputCapture):

  @test_case.Filters.DoNotRunOnWindows
  def testUninterruptibleSection(self):
    # The code this tests works on Windows, however, it is not possible to send
    # a SIGINT signal on Windows.  The Windows shell catches CTRL-C and converts
    # it into a SIGINT (which is why the code works.  Also sending a
    # CTRL_C_EVENT does not actually trigger the SIGINT handler.
    output = io.StringIO()
    with execution_utils.UninterruptibleSection(stream=output, message='foo'):
      os.kill(os.getpid(), signal.SIGINT)
    self.assertIn('foo', output.getvalue())


class EnvTests(sdk_test_base.SdkBase):

  def testGetToolEnv(self):
    self.StartEnvPatch({config.CLOUDSDK_ACTIVE_CONFIG_NAME: 'config'})
    properties.VALUES.core.account.Set('account')
    env = execution_utils._GetToolEnv(env={})
    self.assertEqual(
        encoding.GetEncodedValue(env, 'CLOUDSDK_ACTIVE_CONFIG_NAME'), 'config')
    self.assertEqual(
        encoding.GetEncodedValue(env, 'CLOUDSDK_CORE_ACCOUNT'), 'account')
    self.assertEqual(encoding.GetEncodedValue(env, 'CLOUDSDK_WRAPPER'), '1')


class KillSubprocessTests(test_case.TestCase):

  def testIsTaskKillErrorStringReason(self):
    stderr = 'foo\nbar\n'
    self.assertTrue(execution_utils._IsTaskKillError(stderr))
    stderr = 'foo\nAccess is denied.\nbar\n'
    self.assertFalse(execution_utils._IsTaskKillError(stderr))

  def testIsTaskKillErrorPatternReason(self):
    stderr = 'foo\nThe process "abcd" not found.\nbar\n'
    self.assertTrue(execution_utils._IsTaskKillError(stderr))
    stderr = 'foo\nThe process "1234" not found.\nbar\n'
    self.assertFalse(execution_utils._IsTaskKillError(stderr))


if __name__ == '__main__':
  test_case.main()
