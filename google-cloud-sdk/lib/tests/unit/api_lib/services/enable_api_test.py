# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests of the enable_api module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class EnableApiTest(unit_test_base.SV1UnitTestBase,
                    sdk_test_base.WithFakeAuth):
  """Unit tests for enable_api module."""

  OPERATION_NAME = 'operation-00000-00000'

  def SetUp(self):
    self.service_names = ['service1', 'service2']
    self.services = [
        self.CreateService(service_name)
        for service_name in self.service_names]

  def _ExpectListEnabledServicesCall(self, error=None):
    if error:
      response = None
    else:
      response = self.services_messages.ListServicesResponse(
          services=self.services)
    self.mocked_client.services.List.Expect(
        self.services_messages.ServicemanagementServicesListRequest(
            consumerId='project:{}'.format(self.Project()), pageSize=100),
        response,
        exception=error
    )

  def testIsServiceEnabled_True(self):
    """Test IsServiceEnabled when result is True."""
    self._ExpectListEnabledServicesCall()
    self.assertTrue(enable_api.IsServiceEnabled(self.Project(),
                                                'service1.googleapis.com'))

  def testIsServiceEnabled_False(self):
    """Test IsServiceEnabled when result is False."""
    self._ExpectListEnabledServicesCall()
    self.assertFalse(enable_api.IsServiceEnabled(self.Project(),
                                                 'service3.googleapis.com'))

  def testIsServiceEnabled_PermissionsError(self):
    """Test IsServiceEnabled raises PermissionsError when expected."""
    server_error = http_error.MakeDetailedHttpError(code=403,
                                                    message='Something.')
    self._ExpectListEnabledServicesCall(error=server_error)
    with self.assertRaisesRegex(
        exceptions.ListServicesPermissionDeniedException, r'Something.'):
      enable_api.IsServiceEnabled(self.Project(), 'service3')

  def testIsServiceEnabled_OtherError(self):
    """Test IsServiceEnabled raises HttpError when expected."""
    server_error = http_error.MakeDetailedHttpError(code=401,
                                                    message='Something else.')
    self._ExpectListEnabledServicesCall(error=server_error)
    with self.assertRaisesRegex(
        apitools_exceptions.HttpError, r'Something else.'):
      enable_api.IsServiceEnabled(self.Project(), 'service3')

  def _ExpectEnableServiceCall(self, service_name, response, error=None):
    self.mocked_client.services.Enable.Expect(
        self.services_messages.ServicemanagementServicesEnableRequest(
            serviceName=service_name,
            enableServiceRequest=self.services_messages.EnableServiceRequest(
                consumerId='project:{}'.format(self.Project()))),
        response,
        exception=error
    )

  def testEnableServiceApiCall_Success(self):
    """Test EnableServiceApiCall returns operation when successful."""
    response = self.services_messages.Operation(
        name=self.OPERATION_NAME,
        done=False)
    self._ExpectEnableServiceCall('service3.googleapis.com', response)
    self.assertEqual(
        enable_api.EnableServiceApiCall(
            self.Project(), 'service3.googleapis.com'),
        self.services_messages.Operation(name=self.OPERATION_NAME, done=False))

  def testEnableServiceApiCall_PermissionDenied(self):
    """Test EnableServiceApiCall raises correctly when server returns 403 error.
    """
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self._ExpectEnableServiceCall('service3', None, error=server_error)
    with self.assertRaisesRegex(
        exceptions.EnableServicePermissionDeniedException,
        r'Error.'):
      enable_api.EnableServiceApiCall(self.Project(), 'service3')

  def testEnableServiceApiCall_GenericException(self):
    """Test EnableServiceApiCall raises when server returns other error.
    """
    server_error = http_error.MakeDetailedHttpError(code=400, message='Error.')
    self._ExpectEnableServiceCall('service3', None, error=server_error)
    with self.assertRaisesRegex(apitools_exceptions.HttpError, r'Error.'):
      enable_api.EnableServiceApiCall(self.Project(), 'service3')

  def testEnableServiceIfDisabled_AlreadyEnabled(self):
    """Test EnableServiceIfDisabled runs successfully if already enabled."""
    self._ExpectListEnabledServicesCall()
    enable_api.EnableServiceIfDisabled(self.Project(),
                                       'service1.googleapis.com')

  def testEnableServiceIfDisabled_NotYetEnabled_Success(self):
    """Test EnableServiceifDisabled enables service if not yet enabled."""
    self._ExpectListEnabledServicesCall()
    response = self.services_messages.Operation(
        name=self.OPERATION_NAME,
        done=False)
    self._ExpectEnableServiceCall('service3.googleapis.com', response)
    self.MockOperationWait(self.OPERATION_NAME)
    enable_api.EnableServiceIfDisabled(self.Project(),
                                       'service3.googleapis.com')

  def testEnableServiceIfDisabled_NotYetEnabled_EventualFailure(self):
    """Test EnableServiceIfDisabled raises if operation fails."""
    self._ExpectListEnabledServicesCall()
    response = self.services_messages.Operation(
        name=self.OPERATION_NAME,
        done=False)
    self._ExpectEnableServiceCall('service3.googleapis.com', response)
    self.MockOperationWait(self.OPERATION_NAME, final_error_code=403)
    with self.assertRaises(exceptions.OperationErrorException):
      enable_api.EnableServiceIfDisabled(self.Project(),
                                         'service3.googleapis.com')
