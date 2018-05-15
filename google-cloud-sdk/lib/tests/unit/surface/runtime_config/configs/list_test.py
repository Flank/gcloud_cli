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
"""Tests for surface.runtime_config.configs.list."""

from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap
from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class ConfigurationsListTest(base.RuntimeConfigTestBase):

  DEFAULT_PAGE_SIZE = 100

  def testList(self):
    # Tests a list request with two pages.
    configs = [
        self.messages.RuntimeConfig(
            name='projects/{0}/configs/foobar1'.format(self.Project()),
            description='first config',
        ),
        self.messages.RuntimeConfig(
            name='projects/{0}/configs/foobar2'.format(self.Project()),
            description='second config',
        ),
    ]
    request_1 = self.messages.RuntimeconfigProjectsConfigsListRequest(
        parent='projects/{0}'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
    )
    request_2 = self.messages.RuntimeconfigProjectsConfigsListRequest(
        parent='projects/{0}'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
        pageToken='foobar',
    )

    wrapped_result_1 = self.messages.ListConfigsResponse(
        configs=configs[:1],
        nextPageToken='foobar',
    )
    wrapped_result_2 = self.messages.ListConfigsResponse(
        configs=configs[1:],
        nextPageToken=None,
    )

    self.config_client.List.Expect(request_1, wrapped_result_1)
    self.config_client.List.Expect(request_2, wrapped_result_2)
    got_result = self.RunRuntimeConfig('list')

    self.assertEqual([util.FormatConfig(c) for c in configs], list(got_result))

  def testFormat(self):
    # Tests a list request with two pages.
    configs = [
        self.messages.RuntimeConfig(
            name='projects/{0}/configs/foobar1'.format(self.Project()),
            description='first config',
        ),
        self.messages.RuntimeConfig(
            name='projects/{0}/configs/foobar2'.format(self.Project()),
            description='second config',
        ),
    ]
    request_1 = self.messages.RuntimeconfigProjectsConfigsListRequest(
        parent='projects/{0}'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
    )
    request_2 = self.messages.RuntimeconfigProjectsConfigsListRequest(
        parent='projects/{0}'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
        pageToken='foobar',
    )

    wrapped_result_1 = self.messages.ListConfigsResponse(
        configs=configs[:1],
        nextPageToken='foobar',
    )
    wrapped_result_2 = self.messages.ListConfigsResponse(
        configs=configs[1:],
        nextPageToken=None,
    )

    self.config_client.List.Expect(request_1, wrapped_result_1)
    self.config_client.List.Expect(request_2, wrapped_result_2)
    self.RunRuntimeConfig('list', output_enabled=True)

    self.AssertOutputContains(
        textwrap.dedent("""\
            NAME     DESCRIPTION
            foobar1  first config
            foobar2  second config
        """), normalize_space=True)

  def testListCustomPageSize(self):
    expected_request = self.messages.RuntimeconfigProjectsConfigsListRequest(
        parent='projects/{0}'.format(self.Project()),
        pageSize=55,
    )

    configs = [
        self.messages.RuntimeConfig(
            name='projects/{0}/configs/foobar1'.format(self.Project()),
            description='first config',
        ),
        self.messages.RuntimeConfig(
            name='projects/{0}/configs/foobar2'.format(self.Project()),
            description='second config',
        ),
    ]
    wrapped_result = self.messages.ListConfigsResponse(
        configs=configs,
        nextPageToken=None,
    )

    self.config_client.List.Expect(expected_request, wrapped_result)
    got_result = self.RunRuntimeConfig('list --page-size 55')

    self.assertEqual([util.FormatConfig(c) for c in configs], list(got_result))

  def testListNotFound(self):
    expected_request = self.messages.RuntimeconfigProjectsConfigsListRequest(
        parent='projects/{0}'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
    )
    wanted_exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.config_client.List.Expect(expected_request, exception=wanted_exception)
    with self.assertRaises(exceptions.HttpException):
      result = self.RunRuntimeConfig('list')
      # Evaluate the returned generator to generate the exception
      list(result)


if __name__ == '__main__':
  test_case.main()
