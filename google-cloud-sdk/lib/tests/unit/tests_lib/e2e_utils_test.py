# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Tests for the e2e_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import re
import time

from tests.lib import e2e_utils
from tests.lib import test_case

import mock


class E2eUtilsTest(test_case.WithOutputCapture):

  def testPrintAllThreadStacks(self):
    output = io.StringIO()
    e2e_utils.PrintAllThreadStacks(out=output)
    self.assertTrue(
        re.search(r'e2e_utils\.py", line \d+, in PrintAllThreadStacks',
                  output.getvalue()), msg=output.getvalue())


class WatchDogTest(test_case.WithOutputCapture):

  def SetUp(self):
    self._watchdog = None
    self._timeout_cb_call_count = 0

  def TearDown(self):
    if self._watchdog:
      self._watchdog.Stop()
      self._watchdog.join(timeout=1.0)
      self.assertFalse(self._watchdog.isAlive())

  def _OnTimeout(self):
    self._timeout_cb_call_count += 1

  def _NewWatchDog(self, *args, **kwargs):
    self._watchdog = e2e_utils.WatchDog(*args, timeout_cb=self._OnTimeout,
                                        **kwargs)
    return self._watchdog

  def testStartStopJoin(self):
    """Tests the basic thread operations."""
    watchdog = self._NewWatchDog()
    watchdog.start()
    time.sleep(1.0)
    self.assertTrue(watchdog.isAlive())

    watchdog.Stop()
    watchdog.join(timeout=1.0)
    self.assertFalse(watchdog.isAlive())

  def testFiresWhenTimedOut(self):
    time_mock = mock.MagicMock()
    time_mock.time = mock.MagicMock(return_value=10)
    time_mock.sleep = time.sleep

    watchdog = self._NewWatchDog(timeout_secs=10, timer=time_mock)
    watchdog.start()
    watchdog.join(timeout=1.0)
    self.assertTrue(watchdog.isAlive())

    time_mock.time.return_value = 20
    watchdog.join(timeout=1.0)
    self.assertFalse(watchdog.isAlive())
    self.assertEqual(1, self._timeout_cb_call_count)

  def testAlivePreventsFiring(self):
    time_mock = mock.MagicMock()
    time_mock.time = mock.MagicMock(return_value=10)
    time_mock.sleep = time.sleep

    watchdog = self._NewWatchDog(timeout_secs=10, timer=time_mock)
    watchdog.start()
    watchdog.join(timeout=1.0)
    self.assertTrue(watchdog.isAlive())

    time_mock.time.return_value = 15
    watchdog.Alive()

    time_mock.time.return_value = 20
    watchdog.join(timeout=1.0)
    self.assertTrue(watchdog.isAlive())
    self.assertEqual(0, self._timeout_cb_call_count)


if __name__ == '__main__':
  test_case.main()
