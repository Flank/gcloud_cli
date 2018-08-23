# -*- coding: utf-8 -*- #
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
"""Tests for surface.runtime_config.configs.waiters.create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions as sdk_exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class WaitersCreateTest(base.RuntimeConfigTestBase):

  def testCreateWithSuccessOnly(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    op_name = 'projects/{0}/configs/foo/operations/waiters/bar'.format(
        self.Project())
    cr_request = self.messages.RuntimeconfigProjectsConfigsWaitersCreateRequest(
        parent=config_name,
        waiter=self.messages.Waiter(
            name=waiter_name,
            timeout='60s',
            success=self.messages.EndCondition(
                cardinality=self.messages.Cardinality(
                    path='/success',
                    number=1,
                )
            )
        ),
    )
    cr_result = self.messages.Operation(name=op_name, done=False)

    get_request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    not_done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='60s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        )
    )
    done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='60s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        ),
        done=True
    )

    self.waiter_client.Create.Expect(cr_request, cr_result)
    self.waiter_client.Get.Expect(get_request, not_done_result)
    self.waiter_client.Get.Expect(get_request, done_result)
    got_result = self.RunRuntimeConfig(
        'waiters create bar --config-name foo --timeout 1m '
        '--success-cardinality-path /success')

    self.assertEqual(util.FormatWaiter(done_result), got_result)

  def testCreateWithSuccessAndFailure(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    op_name = 'projects/{0}/configs/foo/operations/waiters/bar'.format(
        self.Project())
    cr_request = self.messages.RuntimeconfigProjectsConfigsWaitersCreateRequest(
        parent=config_name,
        waiter=self.messages.Waiter(
            name=waiter_name,
            timeout='60s',
            success=self.messages.EndCondition(
                cardinality=self.messages.Cardinality(
                    path='/success',
                    number=1,
                )
            ),
            failure=self.messages.EndCondition(
                cardinality=self.messages.Cardinality(
                    path='/failure',
                    number=1,
                )
            )
        ),
    )
    cr_result = self.messages.Operation(name=op_name, done=False)

    get_request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    not_done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='60s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        ),
        failure=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/failure',
                number=1,
            )
        )
    )
    done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='60s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        ),
        failure=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/failure',
                number=1,
            )
        ),
        done=True
    )

    self.waiter_client.Create.Expect(cr_request, cr_result)
    self.waiter_client.Get.Expect(get_request, not_done_result)
    self.waiter_client.Get.Expect(get_request, done_result)
    got_result = self.RunRuntimeConfig(
        'waiters create bar --config-name foo --timeout 1m '
        '--success-cardinality-path /success '
        '--failure-cardinality-path /failure')

    self.assertEqual(util.FormatWaiter(done_result), got_result)

  def testCreateCustomCardinalityNumbers(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    op_name = 'projects/{0}/configs/foo/operations/waiters/bar'.format(
        self.Project())
    cr_request = self.messages.RuntimeconfigProjectsConfigsWaitersCreateRequest(
        parent=config_name,
        waiter=self.messages.Waiter(
            name=waiter_name,
            timeout='60s',
            success=self.messages.EndCondition(
                cardinality=self.messages.Cardinality(
                    path='/success',
                    number=15,
                )
            ),
            failure=self.messages.EndCondition(
                cardinality=self.messages.Cardinality(
                    path='/failure',
                    number=20,
                )
            )
        ),
    )
    cr_result = self.messages.Operation(name=op_name, done=False)

    get_request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    not_done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='60s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=15,
            )
        ),
        failure=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/failure',
                number=20,
            )
        )
    )
    done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='60s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=15,
            )
        ),
        failure=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/failure',
                number=20,
            )
        ),
        done=True
    )

    self.waiter_client.Create.Expect(cr_request, cr_result)
    self.waiter_client.Get.Expect(get_request, not_done_result)
    self.waiter_client.Get.Expect(get_request, done_result)

    got_result = self.RunRuntimeConfig(
        'waiters create bar --config-name foo --timeout 1m '
        '--success-cardinality-path /success '
        '--success-cardinality-number 15 '
        '--failure-cardinality-path /failure '
        '--failure-cardinality-number 20')

    self.assertEqual(util.FormatWaiter(done_result), got_result)

  def _setupCreateAsyncTest(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    op_name = 'projects/{0}/configs/foo/operations/waiters/bar'.format(
        self.Project())
    cr_request = self.messages.RuntimeconfigProjectsConfigsWaitersCreateRequest(
        parent=config_name,
        waiter=self.messages.Waiter(
            name=waiter_name,
            timeout='60s',
            success=self.messages.EndCondition(
                cardinality=self.messages.Cardinality(
                    path='/success',
                    number=1,
                )
            )
        ),
    )
    cr_result = self.messages.Operation(name=op_name, done=False)
    get_request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    get_result = self.messages.Waiter(
        name=waiter_name,
        timeout='60s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        )
    )

    self.waiter_client.Create.Expect(cr_request, cr_result)
    self.waiter_client.Get.Expect(get_request, get_result)

    return get_result

  def testCreateAsync(self):
    expected_result = self._setupCreateAsyncTest()
    got_result = self.RunRuntimeConfig(
        'waiters create bar --config-name foo --timeout 1m '
        '--success-cardinality-path /success --async')

    self.assertEqual(util.FormatWaiter(expected_result), got_result)

  def testCreateAsyncEpilog(self):
    self._setupCreateAsyncTest()
    self.RunRuntimeConfig(
        'waiters create bar --config-name foo --timeout 1m '
        '--success-cardinality-path /success --async', output_enabled=True)

    self.AssertErrContains(
        'The wait command can be used to monitor the progress of waiter [bar].')

  def testCreateWaiterFailure(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    op_name = 'projects/{0}/configs/foo/operations/waiters/bar'.format(
        self.Project())
    cr_request = self.messages.RuntimeconfigProjectsConfigsWaitersCreateRequest(
        parent=config_name,
        waiter=self.messages.Waiter(
            name=waiter_name,
            timeout='60s',
            success=self.messages.EndCondition(
                cardinality=self.messages.Cardinality(
                    path='/success',
                    number=1,
                )
            )
        ),
    )
    cr_result = self.messages.Operation(name=op_name, done=False)

    get_request = self.messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
        name=waiter_name,
    )
    done_result = self.messages.Waiter(
        name=waiter_name,
        timeout='60s',
        success=self.messages.EndCondition(
            cardinality=self.messages.Cardinality(
                path='/success',
                number=1,
            )
        ),
        done=True,
        error=self.messages.Status(
            code=9,
            message='Failed.'
        )
    )

    self.waiter_client.Create.Expect(cr_request, cr_result)
    self.waiter_client.Get.Expect(get_request, done_result)
    with self.assertRaises(sdk_exceptions.ExitCodeNoError):
      self.RunRuntimeConfig(
          'waiters create bar --config-name foo --timeout 1m '
          '--success-cardinality-path /success')

  def testCreateAlreadyExists(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    waiter_name = 'projects/{0}/configs/foo/waiters/bar'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsWaitersCreateRequest(
        parent=config_name,
        waiter=self.messages.Waiter(
            name=waiter_name,
            timeout='60s',
            success=self.messages.EndCondition(
                cardinality=self.messages.Cardinality(
                    path='/success',
                    number=1,
                )
            )
        ),
    )
    exception = base.MakeHttpError(code=409, status='ALREADY_EXISTS')

    self.waiter_client.Create.Expect(request,
                                     exception=exception)
    with self.assertRaises(sdk_exceptions.HttpException):
      self.RunRuntimeConfig(
          'waiters create bar --config-name foo --timeout 1m '
          '--success-cardinality-path /success')


if __name__ == '__main__':
  test_case.main()
