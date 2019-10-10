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
"""Tests for surface.runtime_config.configs.waiters.wait."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import exceptions as rtc_exceptions
from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions as sdk_exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base
from six.moves import range


class WaitersWaitTest(base.RuntimeConfigTestBase):

  def testWait(self):
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    not_done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='30s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        )
    )
    done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='30s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        ),
        done=True
    )

    self.waiter_client.Get.Expect(request, not_done_result)
    self.waiter_client.Get.Expect(request, not_done_result)
    self.waiter_client.Get.Expect(request, done_result)

    got_result = self.RunRuntimeConfig(
        'waiters wait bar --config-name foo')

    self.assertEqual(util.FormatWaiter(done_result), got_result)

  def testWaitTimeout(self):
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    not_done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='30s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        )
    )

    # Set time to return +5 seconds each time it is called.
    self.time_mock.side_effect = list(range(0, 100, 5))

    self.waiter_client.Get.Expect(request, not_done_result)

    with self.assertRaises(rtc_exceptions.WaitTimeoutError):
      self.RunRuntimeConfig(
          'waiters wait bar --config-name foo --max-wait 1s')

  def testWaitWaiterFailure(self):
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    result = self.messages.Waiter(
        name=waiter_name,
        timeout='30s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        ),
        done=True,
        error=self.messages.Status(
            code=9,
            message='Failed'
        ),
    )

    self.waiter_client.Get.Expect(request, result)

    # If the waiter failed, the wait exits with a non-zero code but
    # does not raise an exception. The waiter resource is returned so
    # the user can use it.
    with self.assertRaises(sdk_exceptions.ExitCodeNoError):
      self.RunRuntimeConfig(
          'waiters wait bar --config-name foo')

    self.AssertErrContains('finished with an error: Failed')

  def testWaitWaiterFailureNoMessage(self):
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    result = self.messages.Waiter(
        name=waiter_name,
        timeout='30s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        ),
        done=True,
        error=self.messages.Status(
            code=9,
        ),
    )

    self.waiter_client.Get.Expect(request, result)

    # If the waiter failed, the wait exits with a non-zero code but
    # does not raise an exception. The waiter resource is returned so
    # the user can use it.
    with self.assertRaises(sdk_exceptions.ExitCodeNoError):
      self.RunRuntimeConfig(
          'waiters wait bar --config-name foo')

    self.AssertErrContains('finished with an error.')

  def testWaitNotFound(self):
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.waiter_client.Get.Expect(request, exception=exception)
    with self.assertRaises(sdk_exceptions.HttpException):
      self.RunRuntimeConfig('waiters wait bar --config-name foo')


if __name__ == '__main__':
  test_case.main()
