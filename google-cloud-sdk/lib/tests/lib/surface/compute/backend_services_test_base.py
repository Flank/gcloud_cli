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
"""Base class for all backend services tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class BackendServicesTestBase(sdk_test_base.WithFakeAuth,
                              cli_test_base.CliTestBase):
  """Base class for all backend services test."""

  DEFAULT_SIGNED_URL_CACHE_MAX_AGE_SEC = 3600

  def _GetApiName(self, release_track):
    """Returns the API name for the specified release track."""
    if release_track == calliope_base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif release_track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    else:
      return 'v1'

  def _SetUp(self, release_track):
    """Setup common test components.

    Args:
      release_track: Release track the test is targeting.
    """
    api_name = self._GetApiName(release_track)

    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_name),
        real_client=core_apis.GetClientInstance(
            'compute', api_name, no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_name)
    self.track = release_track
    self.service = self.apitools_client.backendServices
    self.global_operations = self.apitools_client.globalOperations

  def RunBackendServices(self, command):
    """Run the compute backend-services command with the arguments."""
    return self.Run('compute backend-services ' + command)

  def GetBackendServiceRef(self, name):
    """Returns the specified backend service reference."""
    params = {'project': self.Project()}
    collection = 'compute.backendServices'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetOperationRef(self, name):
    """Returns the operation reference."""
    params = {'project': self.Project()}
    collection = 'compute.globalOperations'
    return self.resources.Parse(name, params=params, collection=collection)

  def MakeBackendServiceMessage(self,
                                backend_service_ref,
                                enable_cdn=False,
                                signed_url_key_names=None):
    """Returns the backend service message with the specified fields."""
    backend_service = self.messages.BackendService(
        name=backend_service_ref.Name(),
        enableCDN=enable_cdn,
        selfLink=backend_service_ref.SelfLink())
    if signed_url_key_names:
      backend_service.cdnPolicy = self.messages.BackendServiceCdnPolicy(
          signedUrlKeyNames=signed_url_key_names,
          signedUrlCacheMaxAgeSec=self.DEFAULT_SIGNED_URL_CACHE_MAX_AGE_SEC)
    return backend_service

  def MakeOperationMessage(self, operation_ref, resource_ref=None):
    """Returns the operation message for the specified operation reference."""
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def ExpectGetRequest(self,
                       backend_service_ref,
                       backend_service=None,
                       exception=None):
    """Expects the backend service Get request to be invoked."""
    messages = self.messages
    request_type = messages.ComputeBackendServicesGetRequest
    self.service.Get.Expect(
        request=request_type(**backend_service_ref.AsDict()),
        response=backend_service,
        exception=exception)

  def ExpectOperationGetRequest(self, operation_ref, operation):
    """Expects the operation Get request to be invoked."""
    self.global_operations.Get.Expect(
        self.messages.ComputeGlobalOperationsGetRequest(
            operation=operation_ref.operation, project=operation_ref.project),
        operation)

  def ExpectOperationWaitRequest(self, operation_ref, operation):
    """Expects the operation Wait request to be invoked."""
    self.global_operations.Wait.Expect(
        self.messages.ComputeGlobalOperationsWaitRequest(
            operation=operation_ref.operation, project=operation_ref.project),
        operation)

  def ExpectOperationPollingRequest(self, operation_ref, operation):
    self.ExpectOperationWaitRequest(operation_ref, operation)

  def ExpectAddSignedUrlKeyRequest(self,
                                   backend_service_ref,
                                   key_name,
                                   key_value,
                                   response=None,
                                   exception=None):
    """Expects the AddSignedUrlKey request to be invoked."""
    messages = self.messages
    request_type = messages.ComputeBackendServicesAddSignedUrlKeyRequest

    request = request_type(
        project=backend_service_ref.project,
        backendService=backend_service_ref.Name(),
        signedUrlKey=messages.SignedUrlKey(
            keyName=key_name, keyValue=key_value))

    self.service.AddSignedUrlKey.Expect(
        request=request, response=response, exception=exception)

  def ExpectDeleteSignedUrlKeyRequest(self,
                                      backend_service_ref,
                                      key_name,
                                      response=None,
                                      exception=None):
    """Expects the DeleteSignedUrlKey request to be invoked."""
    messages = self.messages
    request_type = messages.ComputeBackendServicesDeleteSignedUrlKeyRequest

    request = request_type(
        project=backend_service_ref.project,
        backendService=backend_service_ref.Name(),
        keyName=key_name)

    self.service.DeleteSignedUrlKey.Expect(
        request=request, response=response, exception=exception)
