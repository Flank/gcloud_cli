# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests of the services module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.services import serviceusage
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class ServiceUsageTest(unit_test_base.SUUnitTestBase):
  """Unit tests for services module."""

  OPERATION_NAME = 'operations/abc.0000000000'

  def testEnableApiCall_Success(self):
    """Test EnableApiCall returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectEnableApiCall(self.OPERATION_NAME)

    got = serviceusage.EnableApiCall(self.PROJECT_NAME,
                                     self.DEFAULT_SERVICE_NAME)

    self.assertEqual(got, want)

  def testEnableApiCall_PermissionDenied(self):
    """Test EnableApiCall raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectEnableApiCall(None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.EnableServicePermissionDeniedException, r'Error.'):
      serviceusage.EnableApiCall(self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME)

  def testBatchEnableApiCall_Success(self):
    """Test BatchEnableApiCall returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectBatchEnableApiCall(self.OPERATION_NAME)

    got = serviceusage.BatchEnableApiCall(
        self.PROJECT_NAME,
        [self.DEFAULT_SERVICE_NAME, self.DEFAULT_SERVICE_NAME_2])

    self.assertEqual(got, want)

  def testDisableApiCall_Success(self):
    """Test DisableApiCall returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectDisableApiCall(self.OPERATION_NAME)

    got = serviceusage.DisableApiCall(self.PROJECT_NAME,
                                      self.DEFAULT_SERVICE_NAME)

    self.assertEqual(got, want)

  def testDisableApiCall_FailedPrecondition(self):
    """Test DisableApiCall with failed precondition error."""
    server_error = http_error.MakeDetailedHttpError(code=400, message='Error.')
    self.ExpectDisableApiCall(None, error=server_error)

    with self.assertRaisesRegex(exceptions.Error, r'Error.'):
      serviceusage.DisableApiCall(self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME)
    self.AssertErrContains('--force')

  def testGetService_Disabled(self):
    """Test GetService."""
    want = self._NewServiceConfig(
        self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME, enabled=False)
    self.ExpectGetService(want)

    got = serviceusage.GetService(self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME)

    self.assertEqual(got, want)

  def testGetService_Enabled(self):
    """Test GetService."""
    want = self._NewServiceConfig(
        self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME, enabled=True)
    self.ExpectGetService(want)

    got = serviceusage.GetService(self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME)

    self.assertEqual(got, want)

  def testGetService_PermissionDenied(self):
    """Test GetService raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectGetService(None, error=server_error)

    with self.assertRaisesRegex(exceptions.GetServicePermissionDeniedException,
                                r'Error.'):
      serviceusage.GetService(self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME)

  def testIsServiceEnabled_Disabled(self):
    service = self.services_messages.GoogleApiServiceusageV1Service(
        name='projects/123/services/hi.googleapis.com',
        state=self.services_messages.GoogleApiServiceusageV1Service
        .StateValueValuesEnum.DISABLED,
    )
    self.assertFalse(serviceusage.IsServiceEnabled(service))

  def testIsServiceEnabled_Enabled(self):
    service = self.services_messages.GoogleApiServiceusageV1Service(
        name='projects/123/services/hi.googleapis.com',
        state=self.services_messages.GoogleApiServiceusageV1Service
        .StateValueValuesEnum.ENABLED,
    )
    self.assertTrue(serviceusage.IsServiceEnabled(service))

  def testListServicesCall(self):
    """Test ListServices returns operation when successful."""
    want = [self.DEFAULT_SERVICE_NAME, self.DEFAULT_SERVICE_NAME_2]
    self.ExpectListServicesCall()

    got = serviceusage.ListServices(self.PROJECT_NAME, False, None, 10)
    self.assertEqual([s.config.name for s in got], want)

  def testGetOperation_Success(self):
    """Test GetOperation returns operation when successful."""
    want = self.services_messages.Operation(name=self.OPERATION_NAME, done=True)
    self.ExpectOperation(self.OPERATION_NAME, 0)

    got = serviceusage.GetOperation(self.OPERATION_NAME)

    self.assertEqual(got, want)

  def testGetOperation_PermissionDenied(self):
    """Test GetOperation raises exception when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectOperation(self.OPERATION_NAME, 0, error=server_error)

    with self.assertRaisesRegex(exceptions.OperationErrorException, r'Error.'):
      serviceusage.GetOperation(self.OPERATION_NAME)

  def testGenerateServiceIdentityCall_Success(self):
    """Test EnableApiCall returns operation when successful."""
    email = 'hello@world.com'
    unique_id = 'hello-uid'
    self.ExpectGenerateServiceIdentityCall(email, unique_id)

    got_email, got_unique_id = serviceusage.GenerateServiceIdentity(
        self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME)

    self.assertEqual(got_email, email)
    self.assertEqual(got_unique_id, unique_id)

  def testGenerateServiceIdentityCall_PermissionDenied(self):
    """Test EnableApiCall returns operation when successful."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectGenerateServiceIdentityCall(None, None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.GenerateServiceIdentityPermissionDeniedException, r'Error.'):
      serviceusage.GenerateServiceIdentity(self.PROJECT_NAME,
                                           self.DEFAULT_SERVICE_NAME)
