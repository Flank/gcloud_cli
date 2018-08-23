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
"""Tests for surface.runtime_config.configs.variables.describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class VariablesGetValueTest(base.RuntimeConfigTestBase):

  def testDescribe(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesGetRequest(
        name=var_name,
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        value=b'value1\nvalue2',
    )

    self.variable_client.Get.Expect(request, wanted_result)
    self.RunRuntimeConfig(
        'variables get-value var1 --config-name foo',
        output_enabled=True)

    self.AssertOutputEquals('value1\nvalue2')

  def testDescribeText(self):
    # Text value test.
    var_name = 'projects/{0}/configs/foo/variables/var2'.format(self.Project())
    request2 = self.messages.RuntimeconfigProjectsConfigsVariablesGetRequest(
        name=var_name,
    )
    wanted_result2 = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        text='new\ntest',
    )

    self.variable_client.Get.Expect(request2, wanted_result2)
    self.RunRuntimeConfig(
        'variables get-value var2 --config-name foo',
        output_enabled=True)

    self.AssertOutputEquals('new\ntest')

  def testDescribeMultiSegmentName(self):
    var_name = 'projects/{0}/configs/foo/variables/var1/var2'.format(
        self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesGetRequest(
        name=var_name,
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        value=b'value1\nvalue2',
    )

    self.variable_client.Get.Expect(request, wanted_result)
    self.RunRuntimeConfig(
        'variables get-value var1/var2 --config-name foo',
        output_enabled=True)

    self.AssertOutputEquals('value1\nvalue2')

  def testGetValueNotFound(self):
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesGetRequest(
        name=var_name,
    )
    exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.variable_client.Get.Expect(request, exception=exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig(
          'variables get-value var1 --config-name foo',
          output_enabled=True)


if __name__ == '__main__':
  test_case.main()
