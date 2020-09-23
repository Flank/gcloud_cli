# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

import json
import os.path
import subprocess

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.code import cross_platform_temp_file
from googlecloudsdk.command_lib.code import run_subprocess
from googlecloudsdk.core import config
from googlecloudsdk.core.updater import update_manager
from tests.lib import test_case
import mock


class GetGcloudPreferredExecutableTest(test_case.TestCase):

  def testPrefersGcloudComponent(self):
    with mock.patch.object(config, 'Paths') as mock_paths:
      mock_paths.return_value.sdk_root = os.path.join('some', 'sdk', 'root')
      with mock.patch.object(update_manager.UpdateManager,
                             'EnsureInstalledAndRestart') as mock_ensure:
        mock_ensure.return_value = True

        found = run_subprocess.GetGcloudPreferredExecutable('echo')
    self.assertEqual(mock_ensure.call_args, mock.call(['echo']))
    self.assertEqual(found, os.path.join('some', 'sdk', 'root', 'bin', 'echo'))

  def testFallsBackToUsingShellPath(self):
    with mock.patch.object(config, 'Paths') as mock_paths:
      mock_paths.return_value.sdk_root = os.path.join('some', 'sdk', 'root')
      with mock.patch.object(update_manager.UpdateManager,
                             'EnsureInstalledAndRestart') as mock_ensure:
        mock_ensure.return_value = False

        found = run_subprocess.GetGcloudPreferredExecutable('echo')
    # Path will be like /usr/buildtools/buildhelpers/v4/bin/echo' or
    # '.../bin/echo.exe'.
    self.assertIn(os.path.join('bin', 'echo'), found)


# Missing unittests: Run(..., show_output=True) should pass through the child
# process's output; show_output=False should suppress stdout and stderr.


class RunTimeoutTest(test_case.TestCase):

  def CommandToTest(self):
    return run_subprocess.Run

  def testErrorsOnTimeout(self):
    with self.assertRaises(utils.TimeoutError):
      self.CommandToTest()(
          cmd=['bash', '-c', 'sleep 2; echo {}'], timeout_sec=0.1)

  def testNoErrorIfCommandIsFastEnough(self):
    # This should not raise:
    self.CommandToTest()(
        cmd=['bash', '-c', 'sleep 0.1; echo {}'], timeout_sec=2)


class GetOutputLinesTimeoutTest(RunTimeoutTest):

  def CommandToTest(self):
    return run_subprocess.GetOutputLines


class GetOutputJsonTimeoutTest(RunTimeoutTest):

  def CommandToTest(self):
    return run_subprocess.GetOutputJson


class GetOutputLinesTest(test_case.TestCase):

  def testReturnsCommandOutputLines(self):
    with cross_platform_temp_file.NamedTempFile('one\ntwo') as multi_line_file:
      lines = run_subprocess.GetOutputLines(['cat', multi_line_file.name],
                                            timeout_sec=10)
      self.assertEqual(lines, ['one', 'two'])

  def testCanPreserveWhitespaceAtEnds(self):
    with cross_platform_temp_file.NamedTempFile(
        '\none\ntwo\n\n') as multi_line_file:
      lines = run_subprocess.GetOutputLines(['cat', multi_line_file.name],
                                            timeout_sec=10)
      self.assertEqual(lines, ['', 'one', 'two', ''])

  def testCanStripWhitespaceAtEnds(self):
    with cross_platform_temp_file.NamedTempFile(
        '\none\ntwo\n\n') as multi_line_file:
      lines = run_subprocess.GetOutputLines(['cat', multi_line_file.name],
                                            timeout_sec=10,
                                            strip_output=True)
      self.assertEqual(lines, ['one', 'two'])

  def testCanHideStderr(self):
    run_subprocess.GetOutputLines(
        ['bash', '-c', 'echo should not see this in test log >&2'],
        timeout_sec=10,
        show_stderr=False)

  @test_case.Filters.DoNotRunInRpmPackage('Centos 8 Weirdness')
  def testReturnsErrorCode(self):
    with self.assertRaises(subprocess.CalledProcessError) as raised:
      run_subprocess.GetOutputLines(['diff', 'nonexist', 'nonexist2'],
                                    timeout_sec=10)
    self.assertEqual(raised.exception.returncode, 2)


class GetOutputJsonTest(test_case.TestCase):

  def testReturnsParsedCommandJson(self):
    parsed = run_subprocess.GetOutputJson(['echo', '{"hello": "world"}'],
                                          timeout_sec=10)
    self.assertEqual(parsed, {u'hello': u'world'})

  def testErrorsOnInvalidJson(self):
    with self.assertRaises(ValueError):
      run_subprocess.GetOutputJson(['echo', '{corruptjson'], timeout_sec=10)

  def testCanHideStderr(self):
    # The JSON decode will fail either way. The point of this (flimsy) test is
    # to see if stderr is suppressed. I'll try to eliminate that feature
    # in an upcoming CL.
    with self.assertRaises(ValueError):
      run_subprocess.GetOutputJson(
          ['bash', '-c', 'echo should not see this in test log >&2'],
          timeout_sec=10,
          show_stderr=False)


class StreamOutputJsonTest(test_case.TestCase):

  def testJsonObjects(self):
    objs = [{'one': 'two', 'three': 4}, {'five': {'six': 'seven'}}]
    text = ''.join(json.dumps(obj) + '\n' for obj in objs)

    with cross_platform_temp_file.NamedTempFile(text) as multi_line_file:
      cmd = ['cat', multi_line_file.name]
      self.assertSequenceEqual(
          tuple(run_subprocess.StreamOutputJson(cmd, event_timeout_sec=10)),
          objs)

  def testTimeout(self):
    with self.assertRaises(utils.TimeoutError):
      tuple(
          run_subprocess.StreamOutputJson(
              cmd=['bash', '-c', 'sleep 2; echo {}'], event_timeout_sec=0.1))

  def testNoTimeoutIfProgressEventsComeFastEnough(self):
    tuple(
        run_subprocess.StreamOutputJson(
            cmd=[
                'bash', '-c',
                'sleep .1; echo {}; sleep .1; echo {}; sleep .1; echo {}'
            ],
            event_timeout_sec=0.2))
    # (Assert no exception.)

  def testExitNonZero(self):
    with self.assertRaises(subprocess.CalledProcessError):
      tuple(
          run_subprocess.StreamOutputJson(['bash', '-c', 'exit 1'],
                                          event_timeout_sec=1))
