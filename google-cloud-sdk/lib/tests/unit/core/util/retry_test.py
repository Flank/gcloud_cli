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

import time

from googlecloudsdk.core.util import retry
from tests.lib import test_case

import mock
from six.moves import range


class RetryTest(test_case.TestCase):

  def SetUp(self):
    self.time_mock = self.StartObjectPatch(time, 'time')
    self.time_mock.side_effect = range(10)
    self.sleep_mock = self.StartObjectPatch(time, 'sleep')

  def testNoRetryOnResultWhenMaxRetriesIsNotSet(self):
    retryer = retry.Retryer()

    sample_mock = mock.Mock(return_value=True)

    self.assertTrue(retryer.RetryOnResult(sample_mock, [],
                                          should_retry_if=False,
                                          sleep_ms=1000))

    self.assertEqual(1, sample_mock.call_count)
    self.assertEqual(0, self.sleep_mock.call_count)

  def testNoRetryOnExceptionWhenMaxRetriesIsNotSet(self):
    retryer = retry.Retryer()

    sample_mock = mock.Mock(return_value=True)

    self.assertTrue(retryer.RetryOnException(sample_mock, [], sleep_ms=1000))

    self.assertEqual(1, sample_mock.call_count)
    self.assertEqual(0, self.sleep_mock.call_count)

  def testSingleRetryOnResult(self):
    retryer = retry.Retryer(jitter_ms=None)

    sample_mock = mock.Mock(side_effect=[False, True])

    self.assertTrue(
        retryer.RetryOnResult(sample_mock,
                              [],
                              should_retry_if=lambda x, s: not x,
                              sleep_ms=1000))
    self.assertEqual(2, sample_mock.call_count)
    args, unused_kwargs = self.sleep_mock.call_args
    self.assertAlmostEqual(1.0, args[0])

  def testSingleRetryOnResultState(self):
    retryer = retry.Retryer(jitter_ms=None)

    sample_mock = mock.Mock(side_effect=['a', 'b'])

    self.assertEqual(
        'b',
        retryer.RetryOnResult(sample_mock,
                              [],
                              should_retry_if=lambda x, s: s.retrial != 1,
                              sleep_ms=1000))
    self.assertEqual(2, sample_mock.call_count)
    args, unused_kwargs = self.sleep_mock.call_args
    self.assertAlmostEqual(1.0, args[0])

  def testSingleRetryOnException(self):
    retryer = retry.Retryer(max_retrials=2, jitter_ms=None)

    sample_mock = mock.Mock(side_effect=[Exception('raised'), 7])

    self.assertEqual(7, retryer.RetryOnException(sample_mock, [],
                                                 sleep_ms=1000))
    self.assertEqual(2, sample_mock.call_count)
    args, unused_kwargs = self.sleep_mock.call_args
    self.assertAlmostEqual(1.0, args[0])

  def testRetryOnExceptionWithRetryFunc(self):
    retryer = retry.Retryer(max_retrials=2, jitter_ms=None)

    sample_mock = mock.Mock(side_effect=[Exception('1'), Exception('2')])

    with self.assertRaisesRegex(Exception, r'^2$'):
      retryer.RetryOnException(
          sample_mock,
          [],
          sleep_ms=1000,
          should_retry_if=lambda t, v, tr, s: str(v) != '2')
    self.assertEqual(2, sample_mock.call_count)
    args, unused_kwargs = self.sleep_mock.call_args
    self.assertAlmostEqual(1.0, args[0])

  def testNoRetriesWhenMaxRetriesIsNotSet(self):
    retryer = retry.Retryer()

    sample_mock = mock.Mock(return_value=True)

    self.assertTrue(retryer.RetryOnResult(
        sample_mock, [], should_retry_if=False, sleep_ms=1000))

    self.assertEqual(1, sample_mock.call_count)
    self.assertEqual(0, self.sleep_mock.call_count)

  def testSingleRetryWhenRetriesNotAllowed(self):
    retryer = retry.Retryer(max_retrials=0, jitter_ms=None)

    sample_mock = mock.Mock(side_effect=[False, True])

    with self.assertRaises(retry.MaxRetrialsException) as context:
      retryer.RetryOnResult(sample_mock,
                            [],
                            should_retry_if=lambda x, s: not x,
                            sleep_ms=1000)
    self.assertFalse(context.exception.last_result)
    self.assertEqual(0, context.exception.state.retrial)
    self.assertEqual(1000, context.exception.state.time_passed_ms)
    self.assertIn('time_passed_ms', str(context.exception))

  def testMultipleRetriesAndTimeout(self):
    retryer = retry.Retryer(max_retrials=10,
                            max_wait_ms=2000, jitter_ms=None)

    sample_mock = mock.Mock(side_effect=[False, False, False, True])

    with self.assertRaises(retry.WaitException) as context:
      retryer.RetryOnResult(sample_mock, (), should_retry_if=False,
                            sleep_ms=1000)

    self.assertEqual(2000, context.exception.state.time_passed_ms)
    self.assertEqual(1000, context.exception.state.time_to_wait_ms)
    self.assertEqual(1, context.exception.state.retrial)
    self.assertFalse(context.exception.last_result)
    self.assertIn('time_passed_ms', str(context.exception))

  def testStatusUpdate(self):
    status_update_mock = mock.Mock()
    retryer = retry.Retryer(
        max_retrials=3, jitter_ms=None,
        status_update_func=status_update_mock)

    sample_mock = mock.Mock(return_value=False)

    with self.assertRaises(retry.MaxRetrialsException):
      self.assertTrue(
          retryer.RetryOnResult(sample_mock, (), should_retry_if=False,
                                sleep_ms=2000))

    for idx, mock_call in enumerate(status_update_mock.call_args_list):
      result, state = mock_call[0][:2]
      self.assertEqual(False, result)
      self.assertEqual(idx, state.retrial)
      self.assertEqual((idx + 1) * 1000, state.time_passed_ms)
      self.assertEqual(2000, state.time_to_wait_ms)

    self.assertEqual(4, sample_mock.call_count)
    self.assertEqual(3, self.sleep_mock.call_count)

  def testSleepIterable(self):
    status_update_mock = mock.Mock()
    retryer = retry.Retryer(
        max_retrials=3, jitter_ms=None,
        status_update_func=status_update_mock)

    sample_mock = mock.Mock(return_value=False)

    with self.assertRaises(retry.MaxRetrialsException):
      self.assertTrue(
          retryer.RetryOnResult(sample_mock, [], should_retry_if=False,
                                sleep_ms=[100, 200, 300]))

    for idx, mock_call in enumerate(status_update_mock.call_args_list):
      result, state = mock_call[0][:2]
      self.assertEqual(False, result)
      self.assertEqual(idx, state.retrial)
      self.assertEqual((idx + 1) * 1000, state.time_passed_ms)
      self.assertEqual((idx + 1) * 100, state.time_to_wait_ms)

    self.assertEqual(4, sample_mock.call_count)
    self.assertEqual(3, self.sleep_mock.call_count)

  def testExponential(self):
    retryer = retry.Retryer(exponential_sleep_multiplier=2, jitter_ms=None)

    sample_mock = mock.Mock(side_effect=[False, False, False, False, True])

    self.assertTrue(
        retryer.RetryOnResult(sample_mock, [], should_retry_if=False,
                              sleep_ms=1000))

    self.assertEqual(5, sample_mock.call_count)
    self.assertEqual(
        [mock.call(1.0), mock.call(2.0), mock.call(4.0), mock.call(8.0)],
        self.sleep_mock.call_args_list)

  def testExponentialWithCeiling(self):
    retryer = retry.Retryer(exponential_sleep_multiplier=2, jitter_ms=None,
                            wait_ceiling_ms=3000)

    sample_mock = mock.Mock(side_effect=[False, False, False, False, True])

    self.assertTrue(
        retryer.RetryOnResult(sample_mock, [], should_retry_if=False,
                              sleep_ms=1000))

    self.assertEqual(5, sample_mock.call_count)
    self.assertEqual(
        [mock.call(1.0), mock.call(2.0), mock.call(3.0), mock.call(3.0)],
        self.sleep_mock.call_args_list)

  def testRetryWithArgs(self):
    count = [2]

    def F(x, y):
      if count[0] > 0:
        count[0] -= 1
        raise ValueError
      return (x, y)

    retryer = retry.Retryer()
    result = retryer.RetryOnException(F, [42], {'y': 312})
    self.assertEqual((42, 312), result)

  def testRetryOnExceptionDecoratorOk(self):
    count = [2]

    @retry.RetryOnException(max_retrials=2)
    def F():
      if count[0] > 0:
        count[0] -= 1
        raise ValueError
      return count[0]

    self.assertEqual(0, F())

  def testRetryOnExceptionDecoratorTooManyRetrials(self):
    count = [2]

    @retry.RetryOnException(max_retrials=1)
    def F():
      if count[0] > 0:
        count[0] -= 1
        raise ValueError
      return count[0]

    with self.assertRaises(ValueError):
      F()


if __name__ == '__main__':
  test_case.main()
