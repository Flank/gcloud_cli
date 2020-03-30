# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Base classes for gcloud memcache tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib import memcache
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import six


class UnitTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for `gcloud memcache` unit tests."""

  def SetUpForTrack(self):
    self.api_version = memcache.API_VERSION_FOR_TRACK[self.track]
    self.mock_client = mock.Client(
        client_class=apis.GetClientClass('memcache', self.api_version))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.messages = self.mock_client.MESSAGES_MODULE

    self.project_ref = resources.REGISTRY.Create(
        'memcache.projects', projectsId=self.Project())

    self.locations_service = self.mock_client.projects_locations
    self.instances_service = self.mock_client.projects_locations_instances
    self.operations_service = self.mock_client.projects_locations_operations

    self.region_id = 'us-central1'
    self.region_ref = resources.REGISTRY.Parse(
        self.region_id,
        collection='memcache.projects.locations',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.region_relative_name = self.region_ref.RelativeName()


class InstancesUnitTestBase(UnitTestBase):
  """Base class for `gcloud memcache instances` unit tests."""

  def SetUpInstances(self):
    self.instance_id = 'test-instance'
    self.instance_ref = resources.REGISTRY.Parse(
        self.instance_id,
        collection='memcache.projects.locations.instances',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.instance_relative_name = self.instance_ref.RelativeName()

    self.wait_operation_id = 'memcache-wait-operation'
    self.wait_operation_ref = resources.REGISTRY.Parse(
        self.wait_operation_id,
        collection='memcache.projects.locations.operations',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.wait_operation_relative_name = self.wait_operation_ref.RelativeName()

  def MakeInstance(self):
    return self.messages.Instance()

  def MakeLabels(self, labels_dict):
    labels = self.messages.Instance.LabelsValue()
    for k, v in sorted(six.iteritems(labels_dict)):
      labels.additionalProperties.append(
          self.messages.Instance.LabelsValue.AdditionalProperty(
              key=k, value=v))
    return labels

  def MakeParameters(self, parameters_dict):
    params = encoding.DictToMessage(
        parameters_dict, self.messages.MemcacheParameters.ParamsValue)
    parameters = self.messages.MemcacheParameters(params=params)
    return parameters


class OperationsUnitTestBase(UnitTestBase):
  """Base class for `gcloud memcache operations` unit tests."""

  def SetUpOperations(self):
    self.operation_id = 'my-memcache-operation'
    self.operation_ref = resources.REGISTRY.Parse(
        self.operation_id,
        collection='memcache.projects.locations.operations',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.operation_relative_name = self.operation_ref.RelativeName()


class RegionsUnitTestBase(UnitTestBase):
  """Base class for `gcloud memcache regions` unit tests."""

  def SetUpOperationsForTrack(self):
    self.region_id = 'us-central1'
    self.region_ref = resources.REGISTRY.Parse(
        self.region_id,
        collection='memcache.projects.locations',
        params={
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.region_relative_name = self.region_ref.RelativeName()
