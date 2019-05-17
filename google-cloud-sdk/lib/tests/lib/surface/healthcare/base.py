# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Base class for all Cloud Healthcare tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


class _CloudHealthBase(cli_test_base.CliTestBase):
  """Base class for Cloud Healthcare tests."""

  def SetUp(self):
    self.client = mock.Client(
        client_class=apis.GetClientClass('healthcare', 'v1alpha2'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule('healthcare', 'v1alpha2')


class CloudHealthUnitTestBase(sdk_test_base.WithFakeAuth,
                              sdk_test_base.WithLogCapture, _CloudHealthBase):
  """Base class for Cloud Healthcare unit tests."""

  def _MakeStores(self, store_type, n=10):
    stores = []
    for i in range(n):
      store_name = (
          'projects/{0}/locations/us-central1/datasets/my-dataset/{1}Stores/{1}-{2}'
      ).format(self.Project(), store_type, i)
      config = self.messages.NotificationConfig(pubsubTopic='my-topic')

      store = self.messages.DicomStore(
          name=store_name, notificationConfig=config)
      stores.append(store)
    return stores

  def _ExpectListStores(self, stores, project=None):
    response = self.messages.ListDicomStoresResponse(dicomStores=stores)
    self.client.projects_locations_datasets_dicomStores.List.Expect(
        self.messages.HealthcareProjectsLocationsDatasetsDicomStoresListRequest(
            parent='projects/{}/locations/us-central1/datasets/my-dataset'
            .format(project or self.Project())),
        response)


class CloudHealthE2ETestBase(e2e_base.WithServiceAuth, _CloudHealthBase):
  """base class for all MySurface e2e tests."""
  pass
