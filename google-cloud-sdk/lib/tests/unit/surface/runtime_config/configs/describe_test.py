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
"""Tests for surface.runtime_config.configs.describe.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class ConfigurationsDescribeTest(base.RuntimeConfigTestBase):

  def testDescribe(self):
    config_name = 'projects/{0}/configs/foobar'.format(self.Project())
    expected_request = self.messages.RuntimeconfigProjectsConfigsGetRequest(
        name=config_name,
    )
    wanted_result = self.messages.RuntimeConfig(
        name=config_name,
        description='baz baz',
    )

    self.config_client.Get.Expect(expected_request, wanted_result)
    got_result = self.RunRuntimeConfig('describe foobar')

    self.assertEqual(util.FormatConfig(wanted_result), got_result)

  def testDescribeNotFound(self):
    config_name = 'projects/{0}/configs/foobar'.format(self.Project())
    expected_request = self.messages.RuntimeconfigProjectsConfigsGetRequest(
        name=config_name,
    )
    wanted_exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.config_client.Get.Expect(expected_request, exception=wanted_exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig('describe foobar')


if __name__ == '__main__':
  test_case.main()
