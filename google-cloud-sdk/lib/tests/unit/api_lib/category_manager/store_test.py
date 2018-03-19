# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Unit tests for the store API."""

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.category_manager import store as store_api
from googlecloudsdk.api_lib.category_manager import utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.projects import util as projects_test_util


class StoreTest(sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.messages = apis.GetMessagesModule(utils.API_NAME, utils.API_VERSION)
    self.mock_client = apitools_mock.Client(
        apis.GetClientClass(utils.API_NAME, utils.API_VERSION),
        real_client=apis.GetClientInstance(
            utils.API_NAME, utils.API_VERSION, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def _GetTestIamPolicy(self):
    policy = projects_test_util.GetTestIamPolicy()
    return self.messages.Policy(etag=policy.etag, version=policy.version)

  def testGetTaxStoreFromOrg(self):
    expected = self.messages.TaxonomyStore(name='taxonomyStores/42')
    self.mock_client.organizations.GetTaxonomyStore.Expect(
        self.messages.CategorymanagerOrganizationsGetTaxonomyStoreRequest(
            parent='organizations/123456789'),
        expected)
    org_ref = resources.REGISTRY.Create(
        'cloudresourcemanager.organizations', organizationsId='123456789')
    actual = store_api.GetTaxonomyStoreFromOrgRef(org_ref)
    self.assertEqual(expected, actual)

  def testGetIamPolicy(self):
    policy = self._GetTestIamPolicy()
    self.mock_client.taxonomyStores.GetIamPolicy.Expect(
        self.messages.CategorymanagerTaxonomyStoresGetIamPolicyRequest(
            resource='taxonomyStores/111',
            getIamPolicyRequest=self.messages.GetIamPolicyRequest()), policy)
    response = store_api.GetIamPolicy(
        resources.REGISTRY.Create(
            'categorymanager.taxonomyStores', taxonomyStoresId='111'))
    self.assertEquals(policy, response)

  def testSetIamPolicy(self):
    policy = self._GetTestIamPolicy()
    self.mock_client.taxonomyStores.SetIamPolicy.Expect(
        self.messages.CategorymanagerTaxonomyStoresSetIamPolicyRequest(
            resource='taxonomyStores/111',
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)), policy)
    response = store_api.SetIamPolicy(
        resources.REGISTRY.Create(
            'categorymanager.taxonomyStores', taxonomyStoresId='111'), policy)
    self.assertEquals(policy, response)


if __name__ == '__main__':
  test_case.main()
