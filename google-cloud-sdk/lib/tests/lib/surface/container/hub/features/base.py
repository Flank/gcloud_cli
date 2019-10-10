# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.

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
"""Base classes for Features tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as apimock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import six


class FeaturesTestBase(cli_test_base.CliTestBase,
                       sdk_test_base.WithFakeAuth):
  """Base class for Features Alpha testing."""

  MODULE_NAME = 'gkehub'
  API_VERSION = 'v1alpha1'

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule(self.MODULE_NAME,
                                                self.API_VERSION)
    self.mocked_client = apimock.Client(
        client_class=core_apis.GetClientClass(self.MODULE_NAME,
                                              self.API_VERSION))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    self.wait_operation_ref = resources.REGISTRY.Parse(
        'operation-x',
        collection='gkehub.projects.locations.operations',
        params={
            'locationsId': 'global',
            'projectsId': self.Project(),
        },
        api_version=self.API_VERSION)
    self.wait_operation_relative_name = self.wait_operation_ref.RelativeName()

    self.parent = 'projects/{0}/locations/global'.format(self.Project())
    self.feature = '{0}/features/{1}'.format(self.parent,
                                             self.FEATURE_NAME)

  def RunCommand(self, params):
    prefix = ['container', 'hub', 'features', self.FEATURE_NAME]
    if isinstance(params, six.string_types):
      return self.Run(prefix + [params])
    return self.Run(prefix + params)

  def _MakeFeature(self, **kwargs):
    return self.messages.Feature(**kwargs)

  def _MakeOperation(self, name=None, done=False, error=None, response=None):
    operation = self.messages.Operation(
        name=name or self.wait_operation_relative_name, done=done, error=error)
    if done:
      operation.response = response
    return operation

  def ExpectDeleteFeature(self, response):
    self.mocked_client.projects_locations_global_features.Delete.Expect(
        request=(
            self.messages.GkehubProjectsLocationsGlobalFeaturesDeleteRequest(
                name=self.feature)),
        response=response)

  def ExpectGetFeature(self, feature):
    self.mocked_client.projects_locations_global_features.Get.Expect(
        request=(self.messages.GkehubProjectsLocationsGlobalFeaturesGetRequest(
            name=self.feature)),
        response=feature)

  def ExpectCreateFeature(self, feature, response):
    self.mocked_client.projects_locations_global_features.Create.Expect(
        request=(
            self.messages.GkehubProjectsLocationsGlobalFeaturesCreateRequest(
                parent=self.parent,
                featureId=self.FEATURE_NAME,
                feature=feature)),
        response=response)

  def ExpectGetOperation(self, operation, exception=None):
    req = self.messages.GkehubProjectsLocationsOperationsGetRequest(
        name=self.wait_operation_relative_name)
    self.mocked_client.projects_locations_operations.Get.Expect(
        req, response=operation, exception=exception)
