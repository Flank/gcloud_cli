# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Base classes for all gcloud managed-identities tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib import managed_identities
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class UnitTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for `gcloud managed-identities` unit tests."""

  def SetUpForTrack(self, track):
    self.track = track
    self.api_version = managed_identities.API_VERSION_FOR_TRACK[track]
    self.mock_client = mock.Client(
        client_class=apis.GetClientClass('managedidentities', self.api_version))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.messages = self.mock_client.MESSAGES_MODULE
    self.project_ref = resources.REGISTRY.Create(
        'managedidentities.projects.locations.global',
        projectsId=self.Project())

    self.locations_service = self.mock_client.projects_locations
    self.domains_service = self.mock_client.projects_locations_global_domains
    self.operations_service = \
        self.mock_client.projects_locations_global_operations


class MsADDomainsUnitTestBase(UnitTestBase):
  """Base class for `gcloud managed-identities microsoft-ad domains` unit tests."""

  def SetUpDomainsForTrack(self):
    self.domain_name = 'my-test-domain.com'
    self.domain_ref = resources.REGISTRY.Parse(
        self.domain_name,
        collection='managedidentities.projects.locations.global.domains',
        params={'projectsId': self.Project()},
        api_version=self.api_version)
    self.domain_relative_name = self.domain_ref.RelativeName()

    self.wait_operation_id = 'managed-identities-wait-operation'
    self.wait_operation_ref = resources.REGISTRY.Parse(
        self.wait_operation_id,
        collection='managedidentities.projects.locations.global.operations',
        params={'projectsId': self.Project()},
        api_version=self.api_version)
    self.wait_operation_relative_name = self.wait_operation_ref.RelativeName()

    self.region_id = 'us-central1'  # region to create domain in
    self.reserved_ip_range = '10.0.1.0/24'
    self.authorized_network = 'projects/some-project/global/networks/some-network'
    self.admin_name = 'MIAdmin'
    self.parent_relative_name = self.domain_ref.Parent().RelativeName()

  def MakeDefaultDomain(self, name=None):
    return self.messages.Domain(
        locations=[self.region_id], reservedIpRange=self.reserved_ip_range)

  def MakeAllOptionsDomain(self, name):
    return self.messages.Domain(
        name=name,
        locations=[self.region_id],
        reservedIpRange=self.reserved_ip_range,
        authorizedNetworks=[self.authorized_network],
        managedIdentitiesAdminName=self.admin_name)

  def MakeDomains(self, n):
    return [
        self.MakeAllOptionsDomain('domain{}.com'.format(i)) for i in range(n)
    ]


class OperationsUnitTestBase(UnitTestBase):
  """Base class for `gcloud managed-identities operations` unit tests."""

  def SetUpOperationsForTrack(self):
    self.operation_id = 'my-ad-operation'
    self.operation_ref = resources.REGISTRY.Parse(
        self.operation_id,
        collection='managedidentities.projects.locations.global.operations',
        params={'projectsId': self.Project()},
        api_version=self.api_version)
    self.operation_relative_name = self.operation_ref.RelativeName()
