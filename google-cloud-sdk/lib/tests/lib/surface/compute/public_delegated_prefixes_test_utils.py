# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Base class for public delegated prefixes patch tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.api_lib.util import waiter as waiter_test_base
import mock


class PublicDelegatedPrefixPatchTestBase(sdk_test_base.WithFakeAuth,
                                         cli_test_base.CliTestBase,
                                         waiter_test_base.Base):
  """Base class for public delegated prefixes patch tests."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.client = apitools_mock.Client(
        core_apis.GetClientClass('compute', 'alpha'))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()
    self.messages = self.client.MESSAGES_MODULE
    self.compute_uri = (
        'https://www.googleapis.com/compute/{0}'.format('alpha'))
    self.pdp_name = 'my-pdp'
    self.operation_status_enum = self.messages.Operation.StatusValueValuesEnum
    self.operation_name = 'operation-pizza-crust'

  def _GetOperationMessage(self, status, region=None, resource_uri=None):
    scope = 'regions/{}'.format(region) if region else 'global'
    return self.messages.Operation(
        name=self.operation_name,
        status=status,
        selfLink='{0}/projects/{1}/{2}/operations/{3}'.format(
            self.compute_uri, self.Project(), scope, self.operation_name),
        targetLink=resource_uri)

  def _ExpectPatch(self, resource, region=None):
    if region:
      self.client.publicDelegatedPrefixes.Patch.Expect(
          self.messages.ComputePublicDelegatedPrefixesPatchRequest(
              publicDelegatedPrefix=self.pdp_name,
              project=self.Project(),
              region=region,
              publicDelegatedPrefixResource=resource),
          self._GetOperationMessage(
              self.operation_status_enum.PENDING, region=region))
    else:
      self.client.globalPublicDelegatedPrefixes.Patch.Expect(
          self.messages.ComputeGlobalPublicDelegatedPrefixesPatchRequest(
              publicDelegatedPrefix=self.pdp_name,
              project=self.Project(),
              publicDelegatedPrefixResource=resource),
          self._GetOperationMessage(self.operation_status_enum.PENDING))

  def _ExpectPollAndGet(self, resource, region=None):
    scope = 'regions/{}'.format(region) if region else 'global'
    pdp_uri = (
        self.compute_uri +
        '/projects/{0}/{1}/publicDelegatedPrefixes/{2}'.format(
            self.Project(), scope, self.pdp_name))
    if region:
      self.client.regionOperations.Wait.Expect(
          self.messages.ComputeRegionOperationsWaitRequest(
              operation=self.operation_name,
              project=self.Project(),
              region=region),
          self._GetOperationMessage(
              self.operation_status_enum.DONE,
              region=region,
              resource_uri=pdp_uri))
      self.client.publicDelegatedPrefixes.Get.Expect(
          self.messages.ComputePublicDelegatedPrefixesGetRequest(
              publicDelegatedPrefix=self.pdp_name,
              project=self.Project(),
              region=region), resource)
    else:
      self.client.globalOperations.Wait.Expect(
          self.messages.ComputeGlobalOperationsWaitRequest(
              operation=self.operation_name, project=self.Project()),
          self._GetOperationMessage(
              self.operation_status_enum.DONE, resource_uri=pdp_uri))
      self.client.globalPublicDelegatedPrefixes.Get.Expect(
          self.messages.ComputeGlobalPublicDelegatedPrefixesGetRequest(
              publicDelegatedPrefix=self.pdp_name, project=self.Project()),
          resource)
