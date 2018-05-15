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

"""Tests for gcloud app create."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import encoding
from googlecloudsdk.command_lib.app import create_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.apitools import retry
from tests.lib.surface.app import api_test_util


class CreateAppTest(api_test_util.ApiTestBase, test_case.WithInput):

  REGION = 'us-central'  # Any valid region

  CREATING_APP_MSG = ('Creating App Engine application in project [{project}] '
                      'and region [{region}]')
  CHOOSE_REGION_MSG = 'Please choose the region'
  PROJECT_MSG = 'You are creating an app for project [{project}].'
  WARNING_MSG = ('Creating an App Engine application for a project is '
                 'irreversible')

  def _ExpectRegionsListRequest(self, single_region=False):
    regions = {'us-central': [('standardEnvironmentAvailable', True),
                              ('flexibleEnvironmentAvailable', True)],
               'us-east1': [('standardEnvironmentAvailable', True),
                            ('flexibleEnvironmentAvailable', True)],
               'europe-west': [('standardEnvironmentAvailable', True),
                               ('flexibleEnvironmentAvailable', False)]}
    if single_region:
      regions = {'us-central': [('standardEnvironmentAvailable', True),
                                ('flexibleEnvironmentAvailable', True)]}
    self.ExpectListRegionsRequest(regions, self.Project())

  def _ExpectCreateAppRequest(self, region, err=None, retries=2):
    # If err is set, it will replace response
    app_msg = self.messages.Application(id=self.Project(), locationId=region)
    if err:
      self.mock_client.apps.Create.Expect(request=app_msg,
                                          response=None,
                                          exception=err)
      return
    op_name = api_test_util.AppOperationName(self.Project())
    intermediate_response = self.messages.Operation(name=op_name)
    final_response = self.messages.Operation(
        name=op_name,
        done=True,
        response=encoding.JsonToMessage(
            self.messages.Operation.ResponseValue,
            encoding.MessageToJson(app_msg)))
    retry.ExpectWithRetries(
        method=self.mock_client.apps.Create,
        polling_method=self.mock_client.apps_operations.Get,
        request=app_msg,
        polling_request=self.messages.AppengineAppsOperationsGetRequest(
            name=op_name),
        response=intermediate_response,
        final_response=final_response,
        num_retries=retries)

  def testCreateApp_NoProject(self):
    """Test create app errors if no project is set."""
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app create --region={0}'.format(self.REGION))

  def testCreateApp_Region(self):
    """Test create app creates project without prompting using --region flag."""
    self._ExpectCreateAppRequest(self.REGION)
    self.Run('app create --region={0}'.format(self.REGION))
    self.AssertErrContains(self.PROJECT_MSG.format(project=self.Project()))
    self.AssertErrContains('WARNING: ' + self.WARNING_MSG)
    self.AssertErrNotContains(self.CHOOSE_REGION_MSG)
    self.AssertErrContains(
        self.CREATING_APP_MSG.format(project=self.Project(),
                                     region=self.REGION))

  def testCreateApp_NonInteractiveRegion(self):
    """Same as above, just explicitly turn off prompts."""
    properties.VALUES.core.disable_prompts.Set(True)
    self._ExpectCreateAppRequest(self.REGION)
    self.Run('app create --region={0}'.format(self.REGION))
    self.AssertErrContains(self.PROJECT_MSG.format(project=self.Project()))
    self.AssertErrContains('WARNING: ' + self.WARNING_MSG)
    self.AssertErrNotContains(self.CHOOSE_REGION_MSG)
    self.AssertErrContains(
        self.CREATING_APP_MSG.format(project=self.Project(),
                                     region=self.REGION))

  def testCreateApp_InteractiveNoRegion(self):
    """Tests create app prompts for a region and uses the selection."""
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)

    region = 'us-central'
    self.WriteInput('1')  # User chooses the first region.

    err = http_error.MakeHttpError(code=404)
    self.ExpectGetApplicationRequest(self.Project(), exception=err)
    self._ExpectRegionsListRequest(single_region=True)
    self._ExpectCreateAppRequest(region)
    self.Run('app create')
    self.AssertErrContains(self.PROJECT_MSG.format(project=self.Project()))
    self.AssertErrContains('WARNING: ' + self.WARNING_MSG)
    self.AssertErrContains(self.CHOOSE_REGION_MSG)
    self.AssertErrContains(
        self.CREATING_APP_MSG.format(project=self.Project(), region=region))

  def testCreateApp_InteractiveCancelled(self):
    """Tests create app prompts for a region and allows cancellation."""
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)

    region = 'us-central'
    self.WriteInput('4')  # User chooses "cancel".

    err = http_error.MakeHttpError(code=404)
    self.ExpectGetApplicationRequest(self.Project(), exception=err)
    self._ExpectRegionsListRequest()
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('app create')
    self.AssertErrContains(self.PROJECT_MSG.format(project=self.Project()))
    self.AssertErrContains('WARNING: ' + self.WARNING_MSG)
    self.AssertErrContains(self.CHOOSE_REGION_MSG)
    self.AssertErrNotContains(
        self.CREATING_APP_MSG.format(project=self.Project(), region=region))

  def testCreateApp_NonInteractiveNoRegion(self):
    """Tests create app errors if prompting disabled and region not given."""
    properties.VALUES.core.disable_prompts.Set(True)
    with self.assertRaisesRegex(create_util.UnspecifiedRegionError,
                                r'Prompts are disabled'):
      self.Run('app create')
    self.AssertErrNotContains(self.CHOOSE_REGION_MSG)
    self.AssertErrNotContains(
        self.CREATING_APP_MSG.format(project=self.Project(),
                                     region=self.REGION))

  def testCreateApp_NonInteractiveAlreadyExists(self):
    """Test error correctly raised to user when app already exists."""
    # Inject a HTTP 409 Conflict error (signifying that app already exists)
    err = http_error.MakeHttpError(code=409)
    self._ExpectCreateAppRequest(self.REGION, err)
    with self.assertRaisesRegex(
        create_util.AppAlreadyExistsError, r'The project \[{project}\] already '
        r'contains an App Engine application'.format(project=self.Project())):
      self.Run('app create --region={0}'.format(self.REGION))
    self.AssertErrContains(self.PROJECT_MSG.format(project=self.Project()))
    self.AssertErrContains('WARNING: ' + self.WARNING_MSG)
    self.AssertErrNotContains(self.CHOOSE_REGION_MSG)

  def testCreateApp_InteractiveAlreadyExists(self):
    """Test error correctly raised when an app exists in interactive mode.

    Ensures that only one GetApplication API call is made, so that the error
    is raised early, prior to region selection and info messages are displayed.
    """
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)
    existing_location = 'us-east'
    self.ExpectGetApplicationRequest(self.Project(), location_id='us-east')
    with self.AssertRaisesExceptionMatches(
        create_util.AppAlreadyExistsError, 'The project [{project}] already '
        'contains an App Engine application in region [{region}]'
        .format(project=self.Project(), region=existing_location)):
      self.Run('app create')
    self.AssertErrNotContains(self.PROJECT_MSG.format(project=self.Project()))
    self.AssertErrNotContains('WARNING: ' + self.WARNING_MSG)
    self.AssertErrNotContains(self.CHOOSE_REGION_MSG)
    self.AssertErrNotContains(
        self.CREATING_APP_MSG.format(project=self.Project(),
                                     region=self.REGION))

  def testCreateApp_Retries(self):
    """Test that app creation results in retries."""
    self._ExpectCreateAppRequest(self.REGION, retries=2)
    self.Run('app create --region={0}'.format(self.REGION))
    self.AssertErrContains(self.PROJECT_MSG.format(project=self.Project()))
    self.AssertErrContains('WARNING: ' + self.WARNING_MSG)
    self.AssertErrNotContains(self.CHOOSE_REGION_MSG)
    self.AssertErrContains(
        self.CREATING_APP_MSG.format(project=self.Project(),
                                     region=self.REGION))


if __name__ == '__main__':
  test_case.main()
