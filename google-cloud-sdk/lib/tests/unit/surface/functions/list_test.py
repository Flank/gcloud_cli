# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests of the 'list' command."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions as base_exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.functions import base
from tests.lib.surface.functions import util as testutil


class FunctionsListTest(base.FunctionsTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudfunctions', 'v1')

  def _createFunction(self, name):
    full_name = 'projects/{0}/locations/us-central1/functions/{1}'.format(
        self.Project(), name)
    return self.messages.CloudFunction(
        name=full_name, sourceArchiveUrl='my-url',
        status=self.messages.CloudFunction.StatusValueValuesEnum('ACTIVE'))

  def _setListResponse(self, functions, project=None, region=None,
                       page_size=None):
    if project is None:
      project = self.Project()
    if region is None:
      region = '-'
    location = 'projects/{}/locations/{}'.format(project, region)

    page_token = None
    next_page = None
    while len(functions) > 100:
      next_page = 'next_page-{0}'.format(len(functions))
      self.mock_client.projects_locations_functions.List.Expect(
          self.messages.CloudfunctionsProjectsLocationsFunctionsListRequest(
              parent=location, pageSize=100, pageToken=page_token),
          self.messages.ListFunctionsResponse(
              functions=functions[0:100], nextPageToken=next_page))
      functions = functions[100:]
      page_token = next_page
    self.mock_client.projects_locations_functions.List.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsListRequest(
            parent=location, pageSize=page_size or 100, pageToken=page_token),
        self.messages.ListFunctionsResponse(
            functions=functions))

  def _setListResponseWithException(self):
    location = 'projects/{0}/locations/-'.format(self.Project())

    self.mock_client.projects_locations_functions.List.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsListRequest(
            parent=location, pageSize=100, pageToken=None),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))

  def _checkResult(self, actual, expected):
    self.assertListEqual(list(actual), list(expected))

  def testListNoAuth(self):
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegexp(Exception, base.NO_AUTH_REGEXP):
      self.Run('functions list')

  def testListEmptyResult(self):
    functions = []
    self._setListResponse(functions)
    properties.VALUES.core.user_output_enabled.Set(False)
    result = self.Run('functions list')
    self._checkResult(result, functions)

  def testListSingleResult(self):
    functions = [self._createFunction('one')]
    self._setListResponse(functions)
    properties.VALUES.core.user_output_enabled.Set(False)
    result = self.Run('functions list')
    self._checkResult(result, functions)

  def testListFilterByRegions(self):
    functions_asia = [self._createFunction('one')]
    functions_australia = [self._createFunction('two')]
    self._setListResponse(functions_asia, region='asia-east1')
    self._setListResponse(functions_australia, region='australia-south3')
    properties.VALUES.core.user_output_enabled.Set(False)
    result = self.Run('functions list --regions asia-east1,australia-south3')
    self._checkResult(result, functions_asia + functions_australia)

  def testListLimit(self):
    functions = [self._createFunction('one'), self._createFunction('two')]
    self._setListResponse(functions, page_size=1)
    properties.VALUES.core.user_output_enabled.Set(False)
    result = self.Run('functions list --limit=1')
    self._checkResult(result, [functions[0]])

  def testListOutput(self):
    http_triggered = self._createFunction('one')
    http_triggered.httpsTrigger = self.messages.HttpsTrigger(url='example.com')
    event_triggered = self._createFunction('four')
    event_triggered.eventTrigger = self.messages.EventTrigger(
        eventType='providers/cloud.storage/eventTypes/object.change',
        resource='projects/_/buckets/bucket',
    )
    event_untriggered = self._createFunction('five')
    functions = [
        http_triggered,
        event_triggered,
        event_untriggered,
    ]
    self._setListResponse(functions)
    properties.VALUES.core.user_output_enabled.Set(True)
    self.Run('functions list')
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME  STATUS  TRIGGER        REGION
        one   ACTIVE  HTTP Trigger   us-central1
        four  ACTIVE  Event Trigger  us-central1
        five  ACTIVE                 us-central1
     """))

  def testListPaging(self):
    functions = []
    for x in range(256):
      name = 'function-{0}'.format(x)
      functions.append(self._createFunction(name))
    self._setListResponse(functions)
    properties.VALUES.core.user_output_enabled.Set(False)
    result = self.Run('functions list')
    self._checkResult(result, functions)

  def testListFunctionsShouldPrintNameWithoutPath(self):
    # b/23147720: only function name should be printed during list,
    # not the full path
    cloud_function_name = 'foo'
    functions = [self._createFunction(cloud_function_name)]
    self._setListResponse(functions)
    properties.VALUES.core.user_output_enabled.Set(True)
    self.Run('functions list')

    self.AssertOutputContains(
        '{0} ACTIVE'.format(cloud_function_name), normalize_space=True)
    self.AssertOutputNotContains('/' + cloud_function_name)
    self.AssertOutputContains(cloud_function_name)

  def testListFunctionsCsv(self):
    cloud_function_name = 'foo'
    functions = [self._createFunction(cloud_function_name)]
    self._setListResponse(functions)
    properties.VALUES.core.user_output_enabled.Set(True)
    self.Run(
        'functions list --format=csv[no-heading](name,status,triggers.len())')

    self.AssertOutputEquals('{0},ACTIVE,0\n'.format(cloud_function_name))

  def testListShouldNotPrintStacktraceAfterHttpException(self):
    self._setListResponseWithException()
    expected = (
        r'ResponseError: status=\[404\], code=\[Not Found\], message=\[\]')
    with self.assertRaisesRegexp(base_exceptions.HttpException, expected):
      self.Run('functions list')


class FunctionsListWithoutProjectTest(base.FunctionsTestBase):

  def Project(self):
    return None

  def testListNoProject(self):
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegexp(Exception, base.NO_PROJECT_REGEXP):
      self.Run('functions list')

if __name__ == '__main__':
  test_case.main()
