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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import copy
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.category_manager import assets
from googlecloudsdk.api_lib.category_manager import utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import http
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
import httplib2


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

  def ExpectListAnnotationTags(self, asset_ref, expected_annotation_tags):
    """Mocks backend call to list annotation tags."""
    # Make expected value copy to ensure that field mutations don't occur.
    expected_annotation_tags_copy = copy.deepcopy(expected_annotation_tags)
    self.mock_client.assets_annotationTags.List.Expect(
        self.messages.CategorymanagerAssetsAnnotationTagsListRequest(
            name=asset_ref.RelativeName(url_escape=True)),
        expected_annotation_tags_copy)

  def ExpectApplyAnnotation(self, asset_ref, annotation_ref,
                            expected_annotation_tag):
    """Mocks backend call to apply annotation tag."""
    # Make expected value copy to ensure that field mutations don't occur.
    expected_annotation_tag_copy = copy.deepcopy(expected_annotation_tag)
    self.mock_client.assets.ApplyAnnotationTag.Expect(
        self.messages.CategorymanagerAssetsApplyAnnotationTagRequest(
            name=asset_ref.RelativeName(url_escape=True),
            applyAnnotationTagRequest=self.messages.ApplyAnnotationTagRequest(
                annotation=annotation_ref.RelativeName())),
        expected_annotation_tag_copy)

  def ExpectDeleteAnnotation(self, asset_ref, annotation_ref, sub_asset):
    """Mocks backend call to delete annotation tag."""
    self.mock_client.assets.DeleteAnnotationTag.Expect(
        self.messages.CategorymanagerAssetsDeleteAnnotationTagRequest(
            name=assets.GetDeleteTagNamePattern().format(
                asset_ref.RelativeName(url_escape=True)),
            annotation=annotation_ref.RelativeName(),
            subAsset=sub_asset), self.messages.Empty())

  def CreateAnnotationTag(self, asset_id, taxonomy_id, annotation_id,
                          taxonomy_display_name, annotation_display_name):
    """Creates an AnnotationTag message."""
    asset_ref = resources.REGISTRY.Create(
        'categorymanager.assets', assetId=asset_id)
    annotation_ref = resources.REGISTRY.Create(
        'categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=taxonomy_id,
        annotationsId=annotation_id)
    return self.messages.AnnotationTag(
        annotation=annotation_ref.RelativeName(),
        annotationDisplayName=annotation_display_name,
        asset=asset_ref.RelativeName(url_escape=True),
        taxonomyDisplayName=taxonomy_display_name)

  def MockHttpRequest(self, expected_content, status_code='200'):
    """Mocks any backend call making an Http request that uses httplib2.

    Args:
      expected_content: The excepted content of the response.
      status_code: The desired return status code of the response.

    Returns:
      Returns a mocked httplib2.Http object.
    """
    response = {'status': status_code}
    mock_http_client = self.StartObjectPatch(httplib2, 'Http')
    mock_http_client.request.return_value = (response, expected_content)
    http_mock = self.StartObjectPatch(http, 'Http')
    http_mock.return_value = mock_http_client
    return mock_http_client
