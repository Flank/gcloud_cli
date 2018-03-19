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
"""Tests for surface.runtime_config.configs.variables.list."""

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class VariablesListTest(base.RuntimeConfigTestBase):

  DEFAULT_PAGE_SIZE = 100

  def testList(self):
    # Tests a list request with two pages.
    variables = [
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var1'.format(
                self.Project()),
            updateTime='2016-04-16T00:00:00Z',
        ),
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var2/var3'.format(
                self.Project()),
            updateTime='2016-04-16T01:00:00Z',
        ),
    ]
    request_1 = self.messages.RuntimeconfigProjectsConfigsVariablesListRequest(
        parent='projects/{0}/configs/foo'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
        returnValues=False,)
    request_2 = self.messages.RuntimeconfigProjectsConfigsVariablesListRequest(
        parent='projects/{0}/configs/foo'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
        pageToken='foobar',
        returnValues=False,)

    wrapped_result_1 = self.messages.ListVariablesResponse(
        variables=variables[:1],
        nextPageToken='foobar',
    )
    wrapped_result_2 = self.messages.ListVariablesResponse(
        variables=variables[1:],
        nextPageToken=None,
    )

    self.variable_client.List.Expect(request_1, wrapped_result_1)
    self.variable_client.List.Expect(request_2, wrapped_result_2)
    got_result = self.RunRuntimeConfig(
        'variables list --config-name foo')

    self.assertEqual([util.FormatVariable(v) for v in variables],
                     list(got_result))

  def testListCustomPageSize(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesListRequest(
        parent='projects/{0}/configs/foo'.format(self.Project()),
        pageSize=55,
        returnValues=False,)

    variables = [
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var1'.format(
                self.Project()),
            updateTime='2016-04-16T00:00:00Z',
        ),
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var2/var3'.format(
                self.Project()),
            updateTime='2016-04-16T01:00:00Z',
        ),
    ]
    wrapped_result = self.messages.ListVariablesResponse(
        variables=variables,
        nextPageToken=None,
    )

    self.variable_client.List.Expect(request, wrapped_result)
    got_result = self.RunRuntimeConfig(
        'variables list --config-name foo --page-size 55')

    self.assertEqual([util.FormatVariable(v) for v in variables],
                     list(got_result))

  def testListNotFound(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesListRequest(
        parent='projects/{0}/configs/foo'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
        returnValues=False,)
    exception = base.MakeHttpError(code=404, status='NOT_FOUND')

    self.variable_client.List.Expect(request, exception=exception)
    with self.assertRaises(exceptions.HttpException):
      result = self.RunRuntimeConfig(
          'variables list --config-name foo')
      # Evaluate the returned generator to generate the exception
      list(result)

  def testListReturnValues(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesListRequest(
        parent='projects/{0}/configs/foo'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
        returnValues=True,)

    variables = [
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var1'.format(
                self.Project()),
            updateTime='2016-04-16T00:00:00Z',
            value='This is var1.',),
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var2/var3'.format(
                self.Project()),
            updateTime='2016-04-16T01:00:00Z',
            value='This is var2/var3',),
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var4'.format(
                self.Project()),
            updateTime='2016-04-16T02:00:00Z',
            text='This is var4',),
    ]
    wrapped_result = self.messages.ListVariablesResponse(
        variables=variables,)

    self.variable_client.List.Expect(request, wrapped_result)
    got_result = self.RunRuntimeConfig(
        'variables list --config-name foo --values')

    self.assertEqual([util.FormatVariable(v, True) for v in variables],
                     list(got_result))

  def testListReturnValuesOutputFormat(self):
    request = self.messages.RuntimeconfigProjectsConfigsVariablesListRequest(
        parent='projects/{0}/configs/foo'.format(self.Project()),
        pageSize=self.DEFAULT_PAGE_SIZE,
        returnValues=True,)

    variables = [
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var1'.format(
                self.Project()),
            updateTime='2016-04-16T00:00:00Z',
            value='This is var1.',),
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var2/var3'.format(
                self.Project()),
            updateTime='2016-04-16T01:00:00Z',
            value='This is var2/var3',),
        self.messages.Variable(
            name='projects/{0}/configs/foo/variables/var4'.format(
                self.Project()),
            updateTime='2016-04-16T02:00:00Z',
            text='This is var4',),
    ]
    wrapped_result = self.messages.ListVariablesResponse(
        variables=variables,)

    self.variable_client.List.Expect(request, wrapped_result)
    self.RunRuntimeConfig('variables list --config-name foo --values', True)

    self.AssertOutputContains(
        """\
NAME  UPDATE_TIME  VALUE
var1  2016-04-16T00:00:00Z  This is var1.
var2/var3  2016-04-16T01:00:00Z  This is var2/var3
var4  2016-04-16T02:00:00Z  This is var4
""",
        normalize_space=True)
    self.ClearOutput()

if __name__ == '__main__':
  test_case.main()
