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
"""Tests for surface.runtime_config.configs.variables.set."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class VariablesSetTest(base.RuntimeConfigTestBase):

  def testSetWithValue(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesCreateRequest(
        parent=config_name,
        variable=self.messages.Variable(
            name=var_name,
            value=b'value1',
        ),
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        value=b'value1',
    )

    self.variable_client.Create.Expect(request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'variables set var1 "value1" --config-name foo')

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testSetWithTextValue(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesCreateRequest(
        parent=config_name,
        variable=self.messages.Variable(
            name=var_name,
            text='value1',
        ),
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        text='value1',
    )

    self.variable_client.Create.Expect(request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'variables set var1 "value1" --config-name foo --is-text')

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testSetMultiSegmentName(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    var_name = 'projects/{0}/configs/foo/variables/var1/var2'.format(
        self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesCreateRequest(
        parent=config_name,
        variable=self.messages.Variable(
            name=var_name,
            value=b'value1',
        ),
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        value=b'value1',
    )

    self.variable_client.Create.Expect(request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'variables set var1/var2 "value1" --config-name foo')

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testSetFromStdIn(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesCreateRequest(
        parent=config_name,
        variable=self.messages.Variable(
            name=var_name,
            value=b'line1\nline2\n',
        ),
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        value=b'line1\nline2\n',
    )

    self.variable_client.Create.Expect(request, wanted_result)
    # WriteInput appends a '\n' to each line.
    self.WriteInput('line1', 'line2')
    got_result = self.RunRuntimeConfig(
        'variables set var1 --config-name foo')

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testSetOverwritesExisting(self):
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())

    # Short names due to the long class names hitting 80 characters
    cr_req = self.messages.RuntimeconfigProjectsConfigsVariablesCreateRequest(
        parent=config_name,
        variable=self.messages.Variable(
            name=var_name,
            value=b'value1',
        ),
    )
    cr_exception = base.MakeHttpError(409, 'ALREADY_EXISTS')

    upd_req = self.messages.Variable(
        name=var_name,
        value=b'value1',
    )
    upd_result = self.messages.Variable(
        name=var_name,
        state=self.messages.Variable.StateValueValuesEnum.UPDATED,
        updateTime='2016-04-16T00:00:00Z',
        value=b'value1',
    )

    self.variable_client.Create.Expect(cr_req,
                                       exception=cr_exception)
    self.variable_client.Update.Expect(upd_req, upd_result)
    got_result = self.RunRuntimeConfig(
        'variables set var1 "value1" --config-name foo')

    self.assertEqual(util.FormatVariable(upd_result), got_result)

  def testSetFailIfPresentSucceeds(self):
    # Tests that --fail-if-present doesn't cause an error if the named
    # variable does not already exist.
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesCreateRequest(
        parent=config_name,
        variable=self.messages.Variable(
            name=var_name,
            value=b'value1',
        ),
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        updateTime='2016-04-16T00:00:00Z',
        value=b'value1',
    )

    self.variable_client.Create.Expect(request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'variables set var1 "value1" --config-name foo '
        '--fail-if-present'
    )

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testSetFailIfPresentFails(self):
    # Tests that --fail-if-present causees an error if the named
    # variable already exists.
    config_name = 'projects/{0}/configs/foo'.format(self.Project())
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.RuntimeconfigProjectsConfigsVariablesCreateRequest(
        parent=config_name,
        variable=self.messages.Variable(
            name=var_name,
            value=b'value1',
        ),
    )
    exception = base.MakeHttpError(409, 'ALREADY_EXISTS')

    self.variable_client.Create.Expect(request, exception=exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig(
          'variables set var1 "value1" --config-name foo '
          '--fail-if-present'
      )

  def testSetFailIfAbsentSucceeds(self):
    # Tests that --fail-if-absent doesn't cause an error if the named
    # variable already exists.
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.Variable(
        name=var_name,
        value=b'value1',
    )
    wanted_result = self.messages.Variable(
        name=var_name,
        state=self.messages.Variable.StateValueValuesEnum.UPDATED,
        updateTime='2016-04-16T00:00:00Z',
        value=b'value1',
    )

    self.variable_client.Update.Expect(request, wanted_result)
    got_result = self.RunRuntimeConfig(
        'variables set var1 "value1" --config-name foo '
        '--fail-if-absent'
    )

    self.assertEqual(util.FormatVariable(wanted_result), got_result)

  def testSetFailIfAbsentFails(self):
    # Tests that --fail-if-absent causees an error if the named
    # variable does not already exist.
    var_name = 'projects/{0}/configs/foo/variables/var1'.format(self.Project())
    request = self.messages.Variable(
        name=var_name,
        value=b'value1',
    )
    exception = base.MakeHttpError(404, 'NOT_FOUND')

    self.variable_client.Update.Expect(request, exception=exception)
    with self.assertRaises(exceptions.HttpException):
      self.RunRuntimeConfig(
          'variables set var1 "value1" --config-name foo '
          '--fail-if-absent'
      )


if __name__ == '__main__':
  test_case.main()
