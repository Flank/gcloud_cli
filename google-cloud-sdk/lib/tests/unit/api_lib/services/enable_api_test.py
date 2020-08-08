# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base

import httplib2


class EnableApiServiceUsageTest(unit_test_base.SUUnitTestBase):
  """Unit tests for services module."""

  OPERATION_NAME = 'operations/abc.0000000000'

  def testEnableApiCall_Success(self):
    """Test EnableService."""
    self.ExpectEnableApiCall(self.OPERATION_NAME)
    self.ExpectOperation(self.OPERATION_NAME, 0)

    enable_api.EnableService(self.PROJECT_NAME, self.DEFAULT_SERVICE)
    self.AssertErrContains("""\
Enabling service [example.googleapis.com] on project [fake-project]...
Operation "operations/abc.0000000000" finished successfully.
""")

  def testEnableApiDoneCall_Success(self):
    """Test EnableService."""
    self.ExpectEnableApiCall(self.OPERATION_NAME, done=True)

    enable_api.EnableService(self.PROJECT_NAME, self.DEFAULT_SERVICE)
    self.AssertErrContains("""\
Enabling service [example.googleapis.com] on project [fake-project]...
""")

  def testIsServiceEnabled_True(self):
    """Test IsServiceEnabled when result is True."""
    service = self._NewServiceConfig(
        self.PROJECT_NAME, self.DEFAULT_SERVICE, enabled=True)
    self.ExpectGetService(service)

    self.assertTrue(
        enable_api.IsServiceEnabled(self.PROJECT_NAME, self.DEFAULT_SERVICE))

  def testIsServiceEnabled_False(self):
    """Test IsServiceEnabled when result is False."""
    service = self._NewServiceConfig(
        self.PROJECT_NAME, self.DEFAULT_SERVICE, enabled=False)
    self.ExpectGetService(service)

    self.assertFalse(
        enable_api.IsServiceEnabled(self.PROJECT_NAME, self.DEFAULT_SERVICE))

  def testIsServiceEnabled_PermissionsError(self):
    """Test IsServiceEnabled raises PermissionsError when expected."""
    server_error = http_error.MakeDetailedHttpError(
        code=403, message='Something.')
    self.ExpectGetService(None, error=server_error)

    with self.assertRaisesRegex(exceptions.GetServicePermissionDeniedException,
                                r'Something.'):
      enable_api.IsServiceEnabled(self.PROJECT_NAME, self.DEFAULT_SERVICE)

  def testIsServiceEnabled_OtherError(self):
    """Test IsServiceEnabled raises HttpError when expected."""
    server_error = http_error.MakeDetailedHttpError(
        code=401, message='Something else.')
    self.ExpectGetService(None, error=server_error)

    with self.assertRaisesRegex(apitools_exceptions.HttpError,
                                r'Something else.'):
      enable_api.IsServiceEnabled(self.PROJECT_NAME, self.DEFAULT_SERVICE)

  def testEnableServiceIfDisabled_AlreadyEnabled(self):
    """Test EnableServiceIfDisabled runs successfully if already enabled."""
    service = self._NewServiceConfig(
        self.PROJECT_NAME, self.DEFAULT_SERVICE, enabled=True)
    self.ExpectGetService(service)

    enable_api.EnableServiceIfDisabled(self.PROJECT_NAME, self.DEFAULT_SERVICE)

  def testEnableServiceIfDisabled_NotYetEnabled_Success(self):
    """Test EnableServiceifDisabled enables service if not yet enabled."""
    service = self._NewServiceConfig(self.PROJECT_NAME, self.DEFAULT_SERVICE)
    self.ExpectGetService(service)
    self.ExpectEnableApiCall(self.OPERATION_NAME)
    self.ExpectOperation(self.OPERATION_NAME, 3)

    enable_api.EnableServiceIfDisabled(self.PROJECT_NAME, self.DEFAULT_SERVICE)

  def testEnableServiceIfDisabled_NotYetEnabled_EventualFailure(self):
    """Test EnableServiceIfDisabled raises if operation fails."""
    service = self._NewServiceConfig(self.PROJECT_NAME, self.DEFAULT_SERVICE)
    self.ExpectGetService(service)
    self.ExpectEnableApiCall(self.OPERATION_NAME)
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectOperation(self.OPERATION_NAME, 0, error=server_error)

    with self.assertRaises(exceptions.OperationErrorException):
      enable_api.EnableServiceIfDisabled(self.PROJECT_NAME,
                                         self.DEFAULT_SERVICE)


class ResourceQuotaTests(sdk_test_base.WithFakeAuth):

  def testDoesntUseResourceQuota(self):
    mock_http_client = self.StartObjectPatch(http, 'Http')
    mock_http_client.return_value.request.return_value = \
        (httplib2.Response({'status': 200}), b'')
    self.request_mock = mock_http_client.return_value.request
    properties.VALUES.core.project.Set('myproject')
    enable_api.IsServiceEnabled('myproj', 'service1.googleapis.com')
    self.assertNotIn(b'X-Goog-User-Project',
                     self.request_mock.call_args[0][3])
