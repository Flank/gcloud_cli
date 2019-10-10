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
"""Tests for surface.runtime_config.configs.waiters.list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class WaitersListTest(base.RuntimeConfigTestBase):

  DEFAULT_PAGE_SIZE = 100

  def testList(self):
    # Tests a list request with two pages.
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    success = self.messages.EndCondition(
        cardinality=self.messages.Cardinality(
            path='/success',
            number=1,
        )
    )
    waiters = [
        self.messages.Waiter(
            name='projects/{0}/configs/foo/waiters/bar1'.format(self.Project()),
            timeout='30s',
            success=success,
        ),
        self.messages.Waiter(
            name='projects/{0}/configs/foo/waiters/bar2'.format(self.Project()),
            timeout='30s',
            success=success,
            done=True,
        ),
    ]
    request_1 = self.messages.RuntimeconfigProjectsConfigsWaitersListRequest(
        parent=config_name,
        pageSize=self.DEFAULT_PAGE_SIZE,
    )
    request_2 = self.messages.RuntimeconfigProjectsConfigsWaitersListRequest(
        parent=config_name,
        pageSize=self.DEFAULT_PAGE_SIZE,
        pageToken='foobar',
    )

    wrapped_result_1 = self.messages.ListWaitersResponse(
        waiters=waiters[:1],
        nextPageToken='foobar',
    )
    wrapped_result_2 = self.messages.ListWaitersResponse(
        waiters=waiters[1:],
        nextPageToken=None,
    )

    self.waiter_client.List.Expect(request_1, wrapped_result_1)
    self.waiter_client.List.Expect(request_2, wrapped_result_2)
    got_result = self.RunRuntimeConfig(
        'waiters list --config-name foo')

    self.assertEqual([util.FormatWaiter(w) for w in waiters], list(got_result))

  def testListCustomPageSize(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    success = self.messages.EndCondition(
        cardinality=self.messages.Cardinality(
            path='/success',
            number=1,
        )
    )
    waiters = [
        self.messages.Waiter(
            name='projects/{0}/configs/foo/waiters/bar1'.format(self.Project()),
            timeout='30s',
            success=success,
        ),
        self.messages.Waiter(
            name='projects/{0}/configs/foo/waiters/bar2'.format(self.Project()),
            timeout='30s',
            success=success,
            done=True,
        ),
    ]

    request = self.messages.RuntimeconfigProjectsConfigsWaitersListRequest(
        parent=config_name,
        pageSize=55,
    )
    wrapped_result = self.messages.ListWaitersResponse(
        waiters=waiters,
        nextPageToken=None,
    )

    self.waiter_client.List.Expect(request, wrapped_result)
    got_result = self.RunRuntimeConfig(
        'waiters list --config-name foo --page-size 55')

    self.assertEqual([util.FormatWaiter(w) for w in waiters], list(got_result))

  def testListNotFound(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsWaitersListRequest(
        parent=config_name,
        pageSize=self.DEFAULT_PAGE_SIZE,
    )
    exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.waiter_client.List.Expect(request, exception=exception)
    with self.assertRaises(exceptions.HttpException):
      result = self.RunRuntimeConfig('waiters list --config-name foo')
      # Evaluate the returned generator to generate the exception
      list(result)


if __name__ == '__main__':
  test_case.main()
