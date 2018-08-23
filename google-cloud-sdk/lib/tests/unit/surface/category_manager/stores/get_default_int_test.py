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
"""Tests for 'gcloud category-manager stores get-default'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib.surface.category_manager import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,])
class GetDefaultIntTest(base.CategoryManagerUnitTestBase):

  def _ExpectDefaultStoreResponse(self, organization, expected_store_name):
    """Mocks backend call that gets the common taxonomy store."""
    self.mock_client.organizations.GetTaxonomyStore.Expect(
        self.messages.CategorymanagerOrganizationsGetTaxonomyStoreRequest(
            parent=organization),
        self.messages.TaxonomyStore(name=expected_store_name))

  def testGettingDefaultStore(self, track):
    self.track = track
    organization = 'organizations/111'
    expected_store_name = 'taxonomyStores/222'
    self._ExpectDefaultStoreResponse(organization, expected_store_name)
    args = '--organization {}'.format(organization)
    default_store = self.Run('category-manager stores get-default ' + args)
    self.assertEqual(
        default_store, self.messages.TaxonomyStore(name=expected_store_name))
