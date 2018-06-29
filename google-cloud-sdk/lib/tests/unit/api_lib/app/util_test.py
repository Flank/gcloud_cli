
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
"""Tests of the util module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.app import util
from tests.lib import test_case
import mock


class RetryTests(test_case.TestCase):
  """Tests of the RetryWithBackoff function in util."""

  def SetUp(self):
    self.func = mock.MagicMock()
    self.retry_func = mock.MagicMock()
    self.StartPatch('time.sleep')

  def RetryWithBackoff(self, *args, **kwargs):
    return util.RetryWithBackoff(*args, **kwargs)

  def testFirstSuccess(self):
    self.func.return_value = (True, 1)
    result = self.RetryWithBackoff(self.func, self.retry_func)
    self.assertEqual(result, (True, 1))
    self.func.assert_called_once_with()
    self.assertEqual(0, self.retry_func.call_count)

  def testRetrySuccess(self):
    self.func.side_effect = [(False, 1), (False, 2), (False, 3), (True, 4)]
    result = self.RetryWithBackoff(self.func, self.retry_func)
    self.assertEqual(result, (True, 4))
    self.assertEqual(self.func.call_count, 4)
    self.assertEqual(self.retry_func.call_args_list,
                     [mock.call(1, 1), mock.call(2, 2), mock.call(3, 4)])

  def testDifferentBackoff(self):
    self.func.side_effect = [(False, 1), (False, 2), (False, 3), (True, 4)]
    result = self.RetryWithBackoff(self.func, self.retry_func, initial_delay=5,
                                   backoff_factor=5, max_delay=100)
    self.assertEqual(result, (True, 4))
    self.assertEqual(self.func.call_count, 4)
    # Max is 100 instead of 125 because max_delay is set to 100.
    self.assertEqual(self.retry_func.call_args_list,
                     [mock.call(1, 5), mock.call(2, 25), mock.call(3, 100)])

  def testMaxTries(self):
    self.func.side_effect = [(False, 1), (False, 2), (False, 3), (False, 4)]
    result = self.RetryWithBackoff(self.func, self.retry_func, max_tries=3,
                                   raise_on_timeout=False)
    self.assertEqual(result, (False, 3))
    self.assertEqual(self.func.call_count, 3)
    self.assertEqual(self.retry_func.call_args_list,
                     [mock.call(1, 1), mock.call(2, 2)])

  def testException(self):
    self.func.return_value = (False, 1)
    with self.assertRaises(util.TimeoutError):
      self.RetryWithBackoff(self.func, self.retry_func, max_tries=3,
                            raise_on_timeout=True)
    self.assertEqual(self.func.call_count, 3)
    self.assertEqual(self.retry_func.call_args_list,
                     [mock.call(1, 1), mock.call(1, 2)])


if __name__ == '__main__':
  test_case.main()
