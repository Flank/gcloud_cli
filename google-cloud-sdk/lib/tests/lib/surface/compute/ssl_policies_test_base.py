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
"""Base class for all SSL policies tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class SslPoliciesTestBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):
  """Base class for all SSL policies test."""

  def _GetApiName(self, release_track):
    """Returns the API name for the specified release track."""
    if release_track == calliope_base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif release_track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  def _SetUp(self, release_track):
    """Setup common test components.

    Args:
      release_track: Release track the test is targetting.
    """
    api_name = self._GetApiName(release_track)
    self.track = release_track

    apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_name),
        real_client=core_apis.GetClientInstance(
            'compute', api_name, no_http=True))
    apitools_client.Mock()
    self.addCleanup(apitools_client.Unmock)
    self.messages = apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_name)
    self.service = apitools_client.sslPolicies
    self.global_operations = apitools_client.globalOperations

  def GetSslPolicyRef(self, name):
    """Returns the specified SSL policy reference."""
    params = {'project': self.Project()}
    collection = 'compute.sslPolicies'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetOperationRef(self, name):
    """Returns the operation reference."""
    params = {'project': self.Project()}
    collection = 'compute.globalOperations'
    return self.resources.Parse(name, params=params, collection=collection)

  def MakeOperationMessage(self, operation_ref, status=None, resource_ref=None):
    """Returns the operation message for the specified operation reference."""
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=status or self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def ExpectInsertRequest(self,
                          ssl_policy_ref,
                          ssl_policy,
                          response,
                          exception=None):
    """Expects the SSL policy Insert request to be invoked."""
    request = self.messages.ComputeSslPoliciesInsertRequest(
        project=ssl_policy_ref.project, sslPolicy=ssl_policy)
    self.service.Insert.Expect(
        request=request, response=response, exception=exception)

  def ExpectGetRequest(self, ssl_policy_ref, ssl_policy=None, exception=None):
    """Expects the SSL policy Get request to be invoked."""
    self.service.Get.Expect(
        request=self.messages.ComputeSslPoliciesGetRequest(
            **ssl_policy_ref.AsDict()),
        response=ssl_policy,
        exception=exception)

  def ExpectListRequest(self, ssl_policies=None, exception=None):
    """Expects the SSL policy List request to be invoked."""
    self.service.List.Expect(
        request=self.messages.ComputeSslPoliciesListRequest(
            project=self.Project()),
        response=self.messages.SslPoliciesList(items=ssl_policies),
        exception=exception)

  def ExpectPatchRequest(self,
                         ssl_policy_ref,
                         ssl_policy,
                         response,
                         exception=None):
    """Expects the SSL policy Patch request to be invoked."""
    request = self.messages.ComputeSslPoliciesPatchRequest(
        project=ssl_policy_ref.project,
        sslPolicy=ssl_policy_ref.Name(),
        sslPolicyResource=ssl_policy)
    self.service.Patch.Expect(
        request=request, response=response, exception=exception)

  def ExpectDeleteRequest(self, ssl_policy_ref, response, exception=None):
    """Expects the SSL policy Delete request to be invoked."""
    request = self.messages.ComputeSslPoliciesDeleteRequest(
        project=ssl_policy_ref.project, sslPolicy=ssl_policy_ref.Name())
    self.service.Delete.Expect(
        request=request, response=response, exception=exception)

  def ExpectListAvailableFeaturesRequest(self,
                                         project,
                                         features=None,
                                         exception=None):
    """Expects the ListAvailableFeatures request to be invoked."""
    messages = self.messages
    request = messages.ComputeSslPoliciesListAvailableFeaturesRequest(
        project=project)
    response = messages.SslPoliciesListAvailableFeaturesResponse(
        features=features)
    self.service.ListAvailableFeatures.Expect(
        request=request, response=response, exception=exception)

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
