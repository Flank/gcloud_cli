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
"""Tests for surface.runtime_config.configs.update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class ConfigurationsUpdateTest(base.RuntimeConfigTestBase):

  def testUpdateWithDescription(self):
    config_name = 'projects/{0}/configs/foobar'.format(self.Project())
    expected_request = self.messages.RuntimeConfig(
        name=config_name,
        description='baz baz',
    )
    wanted_result = self.messages.RuntimeConfig(
        name=config_name,
        description='baz baz',
    )

    self.config_client.Update.Expect(expected_request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'update foobar --description="baz baz"')

    self.assertEqual(util.FormatConfig(wanted_result), got_result)

  def testUpdateWithEmptyDescription(self):
    config_name = 'projects/{0}/configs/foobar'.format(self.Project())
    expected_request = self.messages.RuntimeConfig(
        name=config_name,
        description='',
    )
    wanted_result = self.messages.RuntimeConfig(
        name=config_name,
    )

    self.config_client.Update.Expect(expected_request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'update foobar --description=""')

    self.assertEqual(util.FormatConfig(wanted_result), got_result)

  def testUpdateNotFound(self):
    config_name = 'projects/{0}/configs/foobar'.format(self.Project())
    expected_request = self.messages.RuntimeConfig(
        name=config_name,
        description='abcd',
    )
    wanted_exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.config_client.Update.Expect(expected_request,
                                     exception=wanted_exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig('update foobar --description="abcd"')


if __name__ == '__main__':
  test_case.main()
