# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the logs streaming library."""

import collections

from googlecloudsdk.api_lib.logging import common
from googlecloudsdk.command_lib.logs import stream
from googlecloudsdk.core.util import times
from tests.lib import test_case


Log = collections.namedtuple('Log', ['timestamp', 'insertId'])


class LogPositionTest(test_case.TestCase):
  """Tests LogPosition."""

  def testLogPosition(self):
    log_position = stream.LogPosition()
    self.assertEqual('timestamp>="1970-01-01T01:00:00.000000000Z"',
                     log_position.GetFilterLowerBound())
    log_position.Update('2016-09-20T17:28:24.002754926Z', '12345678')
    self.assertEqual('timestamp>="2016-09-20T17:28:24.002754926Z"',
                     log_position.GetFilterLowerBound())
    log_position.Update('2016-09-20T17:28:24.002754926Z', '12345679')
    self.assertEqual('((timestamp="2016-09-20T17:28:24.002754926Z" AND '
                     'insertId>"12345679") OR '
                     'timestamp>"2016-09-20T17:28:24.002754926Z")',
                     log_position.GetFilterLowerBound())
    self.assertEqual('timestamp<"2016-09-20T17:28:19.002754Z"',
                     log_position.GetFilterUpperBound(times.ParseDateTime(
                         '2016-09-20T17:28:24.002754926Z')))


class LogFetcherTest(test_case.TestCase):
  """Tests the LogFetcher."""

  def _ContinueFunc(self, num_empty_polls):
    self.continue_func_calls.append(num_empty_polls)
    return num_empty_polls <= 1

  def SetUp(self):
    # This is a list of lists where each poll returns the next batch of logs.
    self.logs = []
    self.continue_func_calls = []
    self.fetcher = stream.LogFetcher(continue_func=self._ContinueFunc)
    self.log_fetcher_mock = self.StartObjectPatch(common, 'FetchLogs')
    self.time_slept = 0
    def _IncrementSleepTime(x):
      self.time_slept += x
    self.sleep_mock = self.StartPatch('time.sleep',
                                      side_effect=_IncrementSleepTime)

  def testBasicGetLogs(self):
    log = Log('2017-01-20T17:28:22.929735908Z', 'foo')
    self.log_fetcher_mock.return_value = [log]

    logs = self.fetcher.GetLogs()

    self.assertEqual([log], logs)

  def testMultipleGetLogs(self):
    log1 = Log('2017-01-20T17:28:22.929735908Z', 'foo')
    log2 = Log('2017-01-20T17:28:22.929735908Z', 'foo2')
    self.log_fetcher_mock.return_value = [log1, log2]

    logs = self.fetcher.GetLogs()

    self.assertEqual([log1, log2], logs)

  def testRejectLateLogs(self):
    log1 = Log('2017-01-20T17:28:22.929735908Z', 'foo')
    log2 = Log('2017-01-20T17:28:21.929735908Z', 'foo2')
    self.log_fetcher_mock.return_value = [log1, log2]

    logs = self.fetcher.GetLogs()

    self.assertEqual([log1], logs)

  def testFiltersAreAdded(self):
    continue_func = lambda num_empty_polls: num_empty_polls == 0
    filters = ['insertId>=foo', 'random irrelevant filter']
    custom_fetcher = stream.LogFetcher(continue_func=continue_func,
                                       filters=filters)
    log1 = Log('2017-01-20T17:28:22.929735908Z', 'foo')
    log2 = Log('2017-01-20T17:28:22.929735908Z', 'foo2')
    self.log_fetcher_mock.return_value = [log1, log2]

    logs = custom_fetcher.GetLogs()

    self.assertEqual([log1, log2], logs)
    _, kwargs = self.log_fetcher_mock.call_args
    filter_string = kwargs['log_filter']
    for filter_ in filters:
      self.assertIn(filter_, filter_string)

  def testBasicYieldLogs(self):
    log = Log('2017-01-20T17:28:22.929735908Z', 'foo')
    self.log_fetcher_mock.side_effect = [[log]]

    logs = self.fetcher.YieldLogs()

    self.assertEqual([log], list(logs))

  def testMultipleYieldLogs(self):
    log1 = Log('2017-01-20T17:28:22.929735908Z', 'foo')
    log2 = Log('2017-01-20T17:28:22.929735908Z', 'foo2')
    self.log_fetcher_mock.side_effect = [[log1, log2]]

    logs = self.fetcher.YieldLogs()

    self.assertEqual([log1, log2], list(logs))

  def testMultiplePollsYieldLogs(self):
    log1 = Log('2017-01-20T17:28:22.929735908Z', 'foo')
    log2 = Log('2017-01-20T17:28:22.929735908Z', 'foo2')
    self.log_fetcher_mock.side_effect = [[log1], [log2]]

    logs = self.fetcher.YieldLogs()

    self.assertEqual([log1, log2], list(logs))

  def testYieldLogsRejectsLateLogs(self):
    log1 = Log('2017-01-20T17:28:22.929735908Z', 'foo')
    log2 = Log('2017-01-20T17:28:21.929735908Z', 'foo2')
    self.log_fetcher_mock.side_effect = [[log1], [log2]]

    logs = self.fetcher.YieldLogs()

    self.assertEqual([log1], list(logs))

  def testYieldLogsStopsAppropriately(self):
    expected_logs = [
        Log('2017-01-20T17:28:22.929735908Z', 'foo0'),
        Log('2017-01-20T17:28:22.929735909Z', 'foo1'),
        Log('2017-01-20T17:28:22.929735910Z', 'foo2'),
    ]
    self.log_fetcher_mock.side_effect = [
        [expected_logs[0]],
        [expected_logs[1]],
        [],
        [expected_logs[2]],
        [],
        []
    ]

    logs = self.fetcher.YieldLogs()

    # The laborious trace-through should give confidence that the log fetcher is
    # doing the following:
    #
    # - While there are logs, sleep and poll again
    # - If there are no logs, run the continue function (keeping track of the
    #   number of consecutive intervals without any logs)
    # - If the continue function returns false, break out of the loop
    self.assertEqual(logs.next(), expected_logs[0])
    self.assertEqual(self.time_slept, 0)
    self.assertEqual(self.log_fetcher_mock.call_count, 1)
    self.assertEqual(self.continue_func_calls, [])

    self.assertEqual(logs.next(), expected_logs[1])
    self.assertEqual(self.time_slept, 10)
    self.assertEqual(self.log_fetcher_mock.call_count, 2)
    self.assertEqual(self.continue_func_calls, [0])

    self.assertEqual(logs.next(), expected_logs[2])
    self.assertEqual(self.time_slept, 30)
    self.assertEqual(self.log_fetcher_mock.call_count, 4)
    self.assertEqual(self.continue_func_calls, [0, 0, 1])

    with self.assertRaises(StopIteration):
      logs.next()
    self.assertEqual(self.time_slept, 50)
    self.assertEqual(self.log_fetcher_mock.call_count, 6)
    self.assertEqual(self.continue_func_calls, [0, 0, 1, 0, 1, 2])

  def testYieldLogsStopsAppropriatelyShorterContinueInterval(self):
    expected_logs = [
        Log('2017-01-20T17:28:22.929735908Z', 'foo0'),
        Log('2017-01-20T17:28:22.929735909Z', 'foo1'),
    ]
    self.log_fetcher_mock.side_effect = [
        [expected_logs[0]],
        [],
        [expected_logs[1]],
        [],
        []
    ]

    # Note that 10 / 5 = 2, so we'll expect 2 _ContinueFunc calls for every log
    # poll
    fetcher = stream.LogFetcher(continue_func=self._ContinueFunc,
                                polling_interval=10, continue_interval=5)

    logs = fetcher.YieldLogs()

    self.assertEqual(logs.next(), expected_logs[0])
    self.assertEqual(self.time_slept, 0)
    self.assertEqual(self.log_fetcher_mock.call_count, 1)
    self.assertEqual(self.continue_func_calls, [])

    self.assertEqual(logs.next(), expected_logs[1])
    self.assertEqual(self.time_slept, 20)
    self.assertEqual(self.log_fetcher_mock.call_count, 3)
    self.assertEqual(self.continue_func_calls, [0, 0, 1, 1])

    with self.assertRaises(StopIteration):
      logs.next()
    self.assertEqual(self.time_slept, 40)
    self.assertEqual(self.log_fetcher_mock.call_count, 5)
    self.assertEqual(self.continue_func_calls,
                     [0, 0, 1, 1, 0, 0, 1, 1, 2])

  def testYieldLogsStopsAppropriatelyLongerContinueInterval(self):
    expected_logs = [
        Log('2017-01-20T17:28:22.929735908Z', 'foo0'),
        Log('2017-01-20T17:28:22.929735909Z', 'foo1'),
        Log('2017-01-20T17:28:22.929735910Z', 'foo2')
    ]
    self.log_fetcher_mock.side_effect = [
        [expected_logs[0]],
        [expected_logs[1]],
        [],
        [expected_logs[2]],
        [],
        [],
        []
    ]

    # Note that 20 / 10 = 2, so we'll expect 2 log polls for every _ContinueFunc
    # call
    fetcher = stream.LogFetcher(continue_func=self._ContinueFunc,
                                polling_interval=10, continue_interval=20)

    logs = fetcher.YieldLogs()

    self.assertEqual(logs.next(), expected_logs[0])
    self.assertEqual(self.time_slept, 0)
    self.assertEqual(self.log_fetcher_mock.call_count, 1)
    self.assertEqual(self.continue_func_calls, [])

    self.assertEqual(logs.next(), expected_logs[1])
    self.assertEqual(self.time_slept, 10)
    self.assertEqual(self.log_fetcher_mock.call_count, 2)
    self.assertEqual(self.continue_func_calls, [0])

    self.assertEqual(logs.next(), expected_logs[2])
    self.assertEqual(self.time_slept, 30)
    self.assertEqual(self.log_fetcher_mock.call_count, 4)
    self.assertEqual(self.continue_func_calls, [0, 1])

    with self.assertRaises(StopIteration):
      logs.next()
    self.assertEqual(self.time_slept, 60)
    self.assertEqual(self.log_fetcher_mock.call_count, 7)
    self.assertEqual(self.continue_func_calls,
                     [0, 1, 1, 3])


class TaskIntervalTimerTest(test_case.TestCase):

  def testTaskIntervalTimer(self):
    sleep_mock = self.StartPatch('time.sleep')
    timer = stream._TaskIntervalTimer({'a': 5, 'b': 10, 'c': 3})

    self.assertEqual(timer.Wait(), set(['c']))
    sleep_mock.assert_called_with(3)

    self.assertEqual(timer.Wait(), set(['a']))
    sleep_mock.assert_called_with(2)

    self.assertEqual(timer.Wait(), set(['c']))
    sleep_mock.assert_called_with(1)

    self.assertEqual(timer.Wait(), set(['c']))
    sleep_mock.assert_called_with(3)

    self.assertEqual(timer.Wait(), set(['a', 'b']))
    sleep_mock.assert_called_with(1)
