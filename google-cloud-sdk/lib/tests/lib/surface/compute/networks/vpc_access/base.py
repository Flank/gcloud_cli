# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Base classes for all gcloud compute networks vpc-access tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


class _VpcAccessBase(cli_test_base.CliTestBase):
  """ Base class for all VpcAccess tests."""
  pass


class VpcAccessE2ETestBase(e2e_base.WithServiceAuth, _VpcAccessBase):
  """base class for all VpcAccess e2e tests."""
  pass


class VpcAccessUnitTestBase(sdk_test_base.WithFakeAuth, _VpcAccessBase):
  """Base class for all VpcAccess unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.api_name = 'vpcaccess'
    self.api_version = 'v1alpha1'
    self.client = mock.Client(
        client_class=apis.GetClientClass(self.api_name, self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule(self.api_name, self.api_version)
    self.locations_client = self.client.projects_locations
    self.operations_client = self.client.projects_locations_operations
    self.connectors_client = self.client.projects_locations_connectors
    self._MakeTestResources()

  def _MakeTestResources(self):
    self.project_id = self.Project()
    self.project_relative_name = 'projects/{}'.format(self.project_id)

    self.region_id = 'us-central1'
    self.region_ref = resources.REGISTRY.Parse(
        self.region_id,
        collection='vpcaccess.projects.locations',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.region_relative_name = self.region_ref.RelativeName()

    self.operation_id = 'my-operation'
    self.operation_ref = resources.REGISTRY.Parse(
        self.operation_id,
        collection='vpcaccess.projects.locations.operations',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.operation_relative_name = self.operation_ref.RelativeName()

    self.connector_id = 'my-connector'
    self.connector_ref = resources.REGISTRY.Parse(
        self.connector_id,
        collection='vpcaccess.projects.locations.connectors',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.connector_relative_name = self.connector_ref.RelativeName()

    self.type_extended = self.messages.Connector.TypeValueValuesEnum.EXTENDED
    self.type_basic = self.messages.Connector.TypeValueValuesEnum.BASIC
    self.network_id = 'my-network'
    self.ip_cidr_range = '10.132.0.0/28'
