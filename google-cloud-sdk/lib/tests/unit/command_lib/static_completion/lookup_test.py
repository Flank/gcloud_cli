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
"""Tests for the table module."""

import os

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.static_completion import lookup
from googlecloudsdk.core import config
from googlecloudsdk.core.util import files
from tests.lib import calliope_test_base


class LookupCmdLineEnvTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.env = {lookup.IFS_ENV_VAR: ' '}

  def _SetCompletionContext(self, line, point):
    self.env.update({lookup.LINE_ENV_VAR: line, lookup.POINT_ENV_VAR: point})
    self.StartDictPatch('os.environ', self.env)

  def testCmdLineEnv(self):
    self._SetCompletionContext('gcloud fruits man', '17')
    self.assertEqual('gcloud fruits man', lookup._GetCmdLineFromEnv())

    self._SetCompletionContext('gcloud fruits man ', '9')
    self.assertEqual('gcloud fr', lookup._GetCmdLineFromEnv())

  def testCmdLineEnvFlags(self):
    self._SetCompletionContext('gcloud fruits --size', '20')
    self.assertEqual('gcloud fruits --size', lookup._GetCmdLineFromEnv())

    self._SetCompletionContext('gcloud fruits --size', '16')
    self.assertEqual('gcloud fruits --', lookup._GetCmdLineFromEnv())

    self._SetCompletionContext('gcloud fruits --size="large"', '28')
    self.assertEqual('gcloud fruits --size="large"',
                     lookup._GetCmdLineFromEnv())

    self._SetCompletionContext('gcloud fruits --size=large', '26')
    self.assertEqual('gcloud fruits --size=large',
                     lookup._GetCmdLineFromEnv())

    self._SetCompletionContext('gcloud fruits --size="extra large"', '34')
    self.assertEqual('gcloud fruits --size="extra large"',
                     lookup._GetCmdLineFromEnv())

  def testCmdLineEnvEmptyLastWord(self):
    self._SetCompletionContext('gcloud fruits man ', '18')
    self.assertEqual('gcloud fruits man ', lookup._GetCmdLineFromEnv())

    self._SetCompletionContext('gcloud fruits man', '14')
    self.assertEqual('gcloud fruits ', lookup._GetCmdLineFromEnv())

    self._SetCompletionContext('gcloud fruits --size ', '21')
    self.assertEqual('gcloud fruits --size ',
                     lookup._GetCmdLineFromEnv())


class LookupCmdWordQueueTest(calliope_test_base.CalliopeTestBase):

  def testCmdWordQueueCommands(self):
    self.assertEqual(['man', 'fruits'], lookup._GetCmdWordQueue(
        'gcloud fruits man'))

    self.assertEqual(['fr'], lookup._GetCmdWordQueue('gcloud fr'))

  def testCmdWordQueueFlags(self):
    self.assertEqual(['--size', 'fruits'], lookup._GetCmdWordQueue(
        'gcloud fruits --size'))

    self.assertEqual(['--', 'fruits'], lookup._GetCmdWordQueue(
        'gcloud fruits --'))

    self.assertEqual(['--size=large', 'fruits'], lookup._GetCmdWordQueue(
        'gcloud fruits --size="large"'))

    self.assertEqual(['--size=large', 'fruits'], lookup._GetCmdWordQueue(
        'gcloud fruits --size=large'))

    self.assertEqual(['--size=extra large', 'fruits'],
                     lookup._GetCmdWordQueue(
                         'gcloud fruits --size="extra large"'))

  def testCmdWordQueueEmptyLastWord(self):
    self.assertEqual(['', 'man', 'fruits'], lookup._GetCmdWordQueue(
        'gcloud fruits man '))

    self.assertEqual(['', 'fruits'], lookup._GetCmdWordQueue('gcloud fruits '))

    self.assertEqual(['', '--size', 'fruits'],
                     lookup._GetCmdWordQueue('gcloud fruits --size '))

  def testCmdWordQueueUnmatchedQuote(self):
    with self.assertRaises(ValueError):
      lookup._GetCmdWordQueue('gcloud fruits --size="extra large')


class LookupCompletionTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    class _FakeStream(object):

      @staticmethod
      def close():
        self.completions_closed = True

      @staticmethod
      def write(s):
        self.completions_value = s

    self.StartPropertyPatch(
        config.Paths, 'sdk_root', return_value=self.temp_path)
    files.MakeDir(os.path.join(self.temp_path, 'data', 'cli'))
    self.WalkTestCli('sdk4')
    self.root = cli_tree.Load(cli=self.test_cli)

    self.completions_closed = False
    self.completions_value = None
    self.StartObjectPatch(lookup, '_OpenCompletionsOutputStream',
                          return_value=_FakeStream())
    self.env = {lookup.IFS_ENV_VAR: ' '}

  def _SetCompletionContext(self, line, point):
    self.env.update({lookup.LINE_ENV_VAR: line, lookup.POINT_ENV_VAR: point})
    self.StartDictPatch('os.environ', self.env)

  def testCompleteCallsFindCompletionsWithCorrectArgs(self):
    self._SetCompletionContext('gcloud fruits man', '17')
    self.find_completions_mock = self.StartObjectPatch(
        lookup, '_FindCompletions')
    lookup.Complete()
    self.find_completions_mock.assert_called_with(self.root,
                                                  'gcloud fruits man')

  def testCompleteWritesCompletionsToStream(self):
    self._SetCompletionContext('gcloud alpha int', '16')
    find_completions_mock = self.StartObjectPatch(lookup, '_FindCompletions')
    find_completions_mock.return_value = ['internal']
    lookup.Complete()
    self.assertTrue(self.completions_closed)
    self.assertEqual('internal', self.completions_value)

  def testFindCompletionsPartialCommandCompletion(self):
    cmd_line = 'gcloud alpha int'
    self.assertEqual(['internal'],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsMultipleCommandCompletion(self):
    cmd_line = 'gcloud '
    self.assertEqual(['alpha', 'beta', 'internal', 'sdk', 'version'],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsIncorrectCompletions(self):
    cmd_line = 'gcloud blpha int'
    self.assertEqual([],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsPartialFlagCompletion(self):
    cmd_line = 'gcloud sdk xyzzy --ex'
    self.assertEqual(['--exactly-one=', '--exactly-three='],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsIncorrectFlagCompletion(self):
    cmd_line = 'gcloud sdk xyzzy --exte'
    self.assertEqual([],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsGlobalFlagCompletion(self):
    cmd_line = 'gcloud sdk --lo'
    self.assertEqual(['--log-http'],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsAfterFlagCompletion(self):
    cmd_line = 'gcloud sdk --log-http xy'
    self.assertEqual(['xyzzy'],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsFlagValueCompletion(self):
    cmd_line = 'gcloud sdk --verbosity=e'
    self.assertEqual(['error'],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsFlagValueMultipleCompletions(self):
    cmd_line = 'gcloud sdk --verbosity='
    self.assertEqual(['critical', 'debug', 'error', 'info', 'none', 'warning'],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsFlagValueCompletionWithEquals(self):
    cmd_line = 'gcloud sdk --verbosity '
    self.assertEqual(['critical', 'debug', 'error', 'info', 'none', 'warning'],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsFlagValueCannotComplete(self):
    cmd_line = 'gcloud sdk xyzzy --exactly-one=on'
    self.assertEqual([],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsFlagValueDynamicFallback(self):
    cmd_line = 'gcloud beta sdk betagroup sub-command-a --resourceful=on'
    with self.assertRaises(lookup.CannotHandleCompletionError):
      lookup._FindCompletions(self.root, cmd_line)

  def testFindCompletionsGroupFlagAfterGroup(self):
    cmd_line = 'gcloud beta sdk betagroup --loc'
    self.assertEqual(['--location='],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsGroupFlagAfterCommand(self):
    cmd_line = 'gcloud beta sdk betagroup beta-command --loc'
    self.assertEqual(['--location='],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsCommandAfterFlagValueCompletion(self):
    cmd_line = 'gcloud sdk --verbosity=error xy'
    self.assertEqual(['xyzzy'],
                     lookup._FindCompletions(self.root, cmd_line))

  def testFindCompletionsPositionalFallback(self):
    cmd_line = 'gcloud sdk xyzzy '
    with self.assertRaises(lookup.CannotHandleCompletionError):
      lookup._FindCompletions(self.root, cmd_line)


if __name__ == '__main__':
  calliope_test_base.main()
