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

"""Test assertions for the cli_test_base test assertions. We must dig deeper."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import random
import time

from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.core.util import retry
from tests.lib import cli_test_base

import mock


class CliTestBaseRunUntilTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.run_patch = self.StartObjectPatch(self, 'Run')
    self.time_patch = self.StartObjectPatch(time, 'time')
    self.sleep_patch = self.StartObjectPatch(time, 'sleep')
    self.random_patch = self.StartObjectPatch(random, 'random')
    self.random_patch.return_value = 0.5

  def testRunUntilMaxRetrials(self):
    self.run_patch.return_value = 'FOO'
    self.time_patch.side_effect = [0.0, 1.0, 3.0, 6.0]

    with self.assertRaises(retry.MaxRetrialsException):
      self.ReRunUntilOutputContains(
          ['foo'], 'bar', exponential_sleep_multiplier=2.0, jitter_ms=0)

    calls = [mock.call(1.0), mock.call(2.0)]
    self.assertEqual(len(calls), self.sleep_patch.call_count)
    self.sleep_patch.assert_has_calls(calls)

    calls = [mock.call(['foo']), mock.call(['foo']), mock.call(['foo'])]
    self.assertEqual(len(calls), self.run_patch.call_count)
    self.run_patch.assert_has_calls(calls)

  def testRunUntilTimeOut(self):
    self.run_patch.return_value = 'FOO'
    self.time_patch.side_effect = [0.0, 2.0, 5.0, 9.0]

    with self.assertRaises(retry.WaitException):
      self.ReRunUntilOutputContains(
          ['foo'], 'bar', exponential_sleep_multiplier=2.0, jitter_ms=0)

    calls = [mock.call(1.0)]
    self.assertEqual(len(calls), self.sleep_patch.call_count)
    self.sleep_patch.assert_has_calls(calls)

    calls = [mock.call(['foo']), mock.call(['foo'])]
    self.assertEqual(len(calls), self.run_patch.call_count)
    self.run_patch.assert_has_calls(calls)

  def testRunUntilSuccess(self):
    def Run(cmd):
      self._foo_counter = getattr(self, '_foo_counter', 0) + 1
      print(self._foo_counter)
      return cmd

    self.run_patch.side_effect = Run
    self.time_patch.side_effect = [0.0, 1.0, 3.0, 6.0]

    result = self.ReRunUntilOutputContains(
        ['foo'], '3', exponential_sleep_multiplier=2.0, jitter_ms=0)

    self.assertEqual(['foo'], result)

    calls = [mock.call(1.0), mock.call(2.0)]
    self.assertEqual(len(calls), self.sleep_patch.call_count)
    self.sleep_patch.assert_has_calls(calls)

    calls = [mock.call(['foo']), mock.call(['foo']), mock.call(['foo'])]
    self.assertEqual(len(calls), self.run_patch.call_count)
    self.run_patch.assert_has_calls(calls)

  def testRunWhileException(self):
    self.run_patch.side_effect = ValueError
    self.time_patch.side_effect = [0.0, 1.0, 3.0, 6.0]

    with self.assertRaises(retry.MaxRetrialsException):
      self.ReRunWhileException(
          ['foo'], ValueError, exponential_sleep_multiplier=2.0, jitter_ms=0)

    calls = [mock.call(1.0), mock.call(2.0)]
    self.assertEqual(len(calls), self.sleep_patch.call_count)
    self.sleep_patch.assert_has_calls(calls)

    calls = [mock.call(['foo']), mock.call(['foo']), mock.call(['foo'])]
    self.assertEqual(len(calls), self.run_patch.call_count)
    self.run_patch.assert_has_calls(calls)

  def testRunWhileWrongException(self):
    self.run_patch.side_effect = AttributeError
    self.time_patch.side_effect = [0.0, 1.0, 3.0, 6.0]

    with self.assertRaises(AttributeError):
      self.ReRunWhileException(
          ['foo'], ValueError, exponential_sleep_multiplier=2.0, jitter_ms=0)

    self.sleep_patch.assert_not_called()

    calls = [mock.call(['foo'])]
    self.assertEqual(len(calls), self.run_patch.call_count)
    self.run_patch.assert_has_calls(calls)

  def testAssertRaisesExceptionRegexp(self):
    with self.AssertRaisesExceptionRegexp(ValueError, '[B]ad call.'):
      raise ValueError('Bad call.')

  def testAssertRaisesExceptionMatches(self):
    with self.AssertRaisesExceptionMatches(ValueError, '[B]ad call.'):
      raise ValueError('[B]ad call.')

  def testAssertRaisesHttpExceptionRegexp(self):
    with self.AssertRaisesHttpExceptionRegexp('[B]ad error.'):
      raise exceptions.HttpException('Bad error.')

  def testAssertRaisesHttpExceptionMatches(self):
    with self.AssertRaisesHttpExceptionMatches('[B]ad error.'):
      raise exceptions.HttpException('[B]ad error.')

  def testAssertRaisesArgumentErrorRegexp(self):
    with self.AssertRaisesArgumentErrorRegexp('[B]ad arg.'):
      raise cli_test_base.MockArgumentError('Bad arg.')

  def testAssertRaisesArgumentErrorMatches(self):
    with self.AssertRaisesArgumentErrorMatches('[B]ad arg.'):
      raise cli_test_base.MockArgumentError('[B]ad arg.')


if __name__ == '__main__':
  cli_test_base.main()
