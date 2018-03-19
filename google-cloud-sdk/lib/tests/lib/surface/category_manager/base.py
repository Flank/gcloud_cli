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

"""Base class for all category manager tests."""


from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.category_manager import utils
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class CategoryManagerUnitTestBase(cli_test_base.CliTestBase,
                                  sdk_test_base.WithFakeAuth,
                                  sdk_test_base.WithTempCWD):
  """Base class for category manager command unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.messages = apis.GetMessagesModule(utils.API_NAME, utils.API_VERSION)
    self.mock_client = apitools_mock.Client(
        apis.GetClientClass(utils.API_NAME, utils.API_VERSION),
        real_client=apis.GetClientInstance(
            utils.API_NAME, utils.API_VERSION, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def ExpectGetTaxonomyStore(self, org_id, taxonomy_store_id):
    """Fakes a request to get a taxonomy store for an organization id."""
    self.mock_client.organizations.GetTaxonomyStore.Expect(
        self.messages.CategorymanagerOrganizationsGetTaxonomyStoreRequest(
            parent='organizations/' + org_id),
        self.messages.TaxonomyStore(name='taxonomyStores/' + taxonomy_store_id))
