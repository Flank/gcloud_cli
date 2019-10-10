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
"""Tests for surface.runtime_config.configs.waiters.describe.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class WaitersDescribeTest(base.RuntimeConfigTestBase):

  def testDescribe(self):
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
        )
    )

    self.waiter_client.Get.Expect(request, result)
    got_result = self.RunRuntimeConfig(
        'waiters describe bar --config-name foo')

    self.assertEqual(util.FormatWaiter(result), got_result)

  def testDescribeNotFound(self):
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.waiter_client.Get.Expect(request, exception=exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig('waiters describe bar --config-name foo')


if __name__ == '__main__':
  test_case.main()
