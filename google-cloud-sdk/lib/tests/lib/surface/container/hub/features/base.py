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
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import six


MODULE_NAME = 'gkehub'


class MockMembershipsAPI(object):
  """Mock for Memberships API."""

  API_VERSION = 'v1beta1'

  def __init__(self, project):
    self.messages = core_apis.GetMessagesModule(MODULE_NAME,
                                                self.API_VERSION)
    self.mocked_client = apimock.Client(
        client_class=core_apis.GetClientClass(MODULE_NAME,
                                              self.API_VERSION))

    self.parent = 'projects/{0}/locations/global'.format(project)

  def _MakeMembership(self,
                      name,
                      description):

    membership = self.messages.Membership(
        name=name,
        description=description)
    return membership

  def ExpectList(self, responses):
    self.mocked_client.projects_locations_memberships.List.Expect(
        (self.messages.GkehubProjectsLocationsMembershipsListRequest(
            parent=self.parent)),
        response=self.messages.ListMembershipsResponse(resources=responses))


class MockFeaturesAPI(object):
  """Mock for Features API."""

  API_VERSION = 'v1alpha1'

  def __init__(self, project, feature_id):
    self.messages = core_apis.GetMessagesModule(MODULE_NAME,
                                                self.API_VERSION)
    self.mocked_client = apimock.Client(
        client_class=core_apis.GetClientClass(MODULE_NAME,
                                              self.API_VERSION))
    self.feature_id = feature_id
    self.parent = 'projects/{0}/locations/global'.format(project)
    self.resource_name = '{0}/features/{1}'.format(self.parent, self.feature_id)

    self.wait_operation_relative_name = (
        'projects/{0}/locations/global/operations/operation-x'.format(
            project))

  def _MakeFeature(self, **kwargs):
    return self.messages.Feature(**kwargs)

  def ExpectDelete(self, response, force=False):
    self.mocked_client.projects_locations_global_features.Delete.Expect(
        request=(
            self.messages.GkehubProjectsLocationsGlobalFeaturesDeleteRequest(
                name=self.resource_name, force=force)),
        response=response)

  def ExpectGet(self, feature):
    self.mocked_client.projects_locations_global_features.Get.Expect(
        request=(self.messages.GkehubProjectsLocationsGlobalFeaturesGetRequest(
            name=self.resource_name)),
        response=feature)

  def ExpectCreate(self, feature, response):
    self.mocked_client.projects_locations_global_features.Create.Expect(
        request=(
            self.messages.GkehubProjectsLocationsGlobalFeaturesCreateRequest(
                parent=self.parent,
                featureId=self.feature_id,
                feature=feature)),
        response=response)

  def ExpectUpdate(self, mask, feature, response):
    self.mocked_client.projects_locations_global_features.Patch.Expect(
        request=(
            self.messages.GkehubProjectsLocationsGlobalFeaturesPatchRequest(
                name=self.resource_name,
                updateMask=mask,
                feature=feature)),
        response=response)

  def _MakeOperation(self, name=None, done=False, error=None, response=None):
    operation = self.messages.Operation(
        name=name or self.wait_operation_relative_name,
        done=done, error=error,
        metadata={})
    if done:
      operation.response = response
    return operation

  def ExpectOperation(self, operation, exception=None):
    req = self.messages.GkehubProjectsLocationsOperationsGetRequest(
        name=self.wait_operation_relative_name)
    self.mocked_client.projects_locations_operations.Get.Expect(
        req, response=operation, exception=exception)


class FeaturesTestBase(cli_test_base.CliTestBase,
                       sdk_test_base.WithFakeAuth):
  """Base class for Features Alpha testing."""

  MODULE_NAME = 'gkehub'
  API_VERSION = 'v1alpha1'

  def SetUp(self):
    self.memberships_api = MockMembershipsAPI(self.Project())
    self.memberships_api.mocked_client.Mock()
    self.addCleanup(self.memberships_api.mocked_client.Unmock)

    self.features_api = MockFeaturesAPI(self.Project(), self.FEATURE_NAME)
    self.features_api.mocked_client.Mock()
    self.addCleanup(self.features_api.mocked_client.Unmock)

  def RunCommand(self, params):
    if hasattr(self, 'NO_FEATURE_PREFIX'):
      prefix = ['container', 'hub', self.NO_FEATURE_PREFIX]
    else:
      prefix = ['container', 'hub', 'features', self.FEATURE_NAME]
    if isinstance(params, six.string_types):
      return self.Run(prefix + [params], track=self.track)
    return self.Run(prefix + params, track=self.track)

