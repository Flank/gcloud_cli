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
"""Base class for all ml products tests."""

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.ml.products import product_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ResourceUtils(object):
  """Utility class for creating ml products resources for mocking."""

  def __init__(self, messages, search_messages, product_client, search_client):
    self.messages = messages
    self.search_messages = search_messages
    self.product_client = product_client
    self.search_client = search_client

  def ImageShortMessage(self, msg):
    return getattr(
        self.messages,
        'AlphaVisionProductSearchCatalogsReferenceImages{}'.format(msg))

  def CatalogShortMessage(self, msg):
    return getattr(self.messages,
                   'AlphaVisionProductSearchCatalogs{}'.format(msg))

  def GetImportOperationResponse(self):
    return encoding.PyValueToMessage(
        self.messages.Operation.ResponseValue, {
            '@type': ('type.googleapis.com/google.cloud.alpha_vision.v1alpha1.'
                      'ImportCatalogsResponse'),
            'refImages': [
                encoding.MessageToJson(x) for x in self.MakeRefImageList(10)
            ],
            'statuses': [{
                'code': 200
            } for x in range(10)]
        })

  def GetTestOperation(self,
                       op_name,
                       error_json=None,
                       is_done=True,
                       response_value=None):

    operation = self.messages.Operation(name=op_name, done=is_done)
    if error_json:
      is_done = True
      operation.error = encoding.PyValueToMessage(self.messages.Status,
                                                  error_json)
    if response_value:
      operation.response = response_value

    return operation

  def MakeRefImageList(self, num=3):
    """Build a list of ReferenceImage messages."""
    image_list = []
    for i in xrange(0, num):
      image_list.append(
          self.messages.ReferenceImage(
              imageUri='gs://fake-bucket/myimage-{}'.format(i),
              productCategory='test-category',
              productId='abc123',
              boundingPoly=None,
              name='productSearch/catalogs/12345/referenceImages/{}'.format(i)))
    return image_list

  def MakeCatalogList(self, num=3):
    """Build a list of Catalog messages."""
    catalog_list = []
    for i in xrange(0, num):
      catalog_list.append(self.messages.Catalog(
          name='productSearch/catalogs/{}'.format(i)))
    return catalog_list

  def ExpectCreateCatalog(self, name='productSearch/catalogs/12345',
                          error=None):
    """Create Expected Request for a Catalog Create Operation."""
    expected_catalog = self.messages.Catalog(name=name)
    self.product_client.productSearch_catalogs.Create.Expect(
        self.messages.Catalog(), expected_catalog, exception=error)

    return expected_catalog

  def ExpectDeleteCatalog(self, name='productSearch/catalogs/12345',
                          error=None):
    """Create Expected Request for a Catalog Delete Operation."""

    expected_catalog = self.messages.Catalog(name=name)
    self.product_client.productSearch_catalogs.Delete.Expect(
        self.messages.AlphaVisionProductSearchCatalogsDeleteRequest(name=name),
        expected_catalog.name,
        exception=error)

    return expected_catalog

  def ExpectLongRunningOpResult(self,
                                op_name,
                                poll_count=2,
                                response_value=None,
                                error_json=None):
    """Get Expectaion for Long Running Operation."""
    for _ in xrange(poll_count):
      in_progress_op = self.GetTestOperation(
          op_name, is_done=False)
      self.search_client.OperationsService.Get.Expect(
          request=self.search_messages.AlphaVisionOperationsGetRequest(
              name=op_name),
          response=in_progress_op)

    op_done_response = self.GetTestOperation(
        op_name, is_done=True,
        response_value=response_value,
        error_json=error_json)

    self.search_client.OperationsService.Get.Expect(
        request=self.search_messages.AlphaVisionOperationsGetRequest(
            name=op_name),
        response=op_done_response)

    return op_done_response

  def ExpectDeleteImageFromCatalog(self,
                                   catalog='productSearch/catalogs/12345',
                                   product_id='abc123'):
    delete_images_req = (
        self.messages.
        AlphaVisionProductSearchCatalogsDeleteReferenceImagesRequest(
            parent=catalog, productId=product_id))
    self.product_client.productSearch_catalogs.DeleteReferenceImages.Expect(
        request=delete_images_req, response=self.messages.Empty)

    return self.messages.Empty

  def ExpectRefImageCreate(
      self, image_uri='gs://fake-bucket/myimage',
      product_category='test-category', product_id='abc123', bounding_poly=None,
      catalog_name='productSearch/catalogs/12345',
      name='productSearch/catalogs/12345/referenceImages/6789', error=None):
    """Create Expection for ReferenceImage Create Operation."""
    expected_image = self.messages.ReferenceImage(
        name=name, imageUri=image_uri, productCategory=product_category,
        productId=product_id, boundingPoly=bounding_poly)

    expected_request = (self.ImageShortMessage('CreateRequest')(
        parent=catalog_name, referenceImage=expected_image))
    self.product_client.productSearch_catalogs_referenceImages.Create.Expect(
        expected_request, expected_image, exception=error)

    return expected_image

  def ExpectRefImageDelete(
      self, image_uri='gs://fake-bucket/myimage',
      product_category='test-category', product_id='abc123', bounding_poly=None,
      name='productSearch/catalogs/12345/referenceImages/6789', error=None):
    """Create Expection for ReferenceImage Delete Operation."""
    expected_image = self.messages.ReferenceImage(
        name=name, imageUri=image_uri, productCategory=product_category,
        productId=product_id, boundingPoly=bounding_poly)

    expected_request = (self.ImageShortMessage('DeleteRequest')(
        name=expected_image.name))
    self.product_client.productSearch_catalogs_referenceImages.Delete.Expect(
        expected_request, self.messages.Empty, exception=error)
    return expected_image

  def ExpectRefImageDescribe(
      self, image_uri='gs://fake-bucket/myimage',
      product_category='test-category', product_id='abc123', bounding_poly=None,
      name='productSearch/catalogs/12345/referenceImages/6789', error=None):
    """Create Expection for ReferenceImage Describe Operation."""
    expected_image = self.messages.ReferenceImage(
        name=name, imageUri=image_uri, productCategory=product_category,
        productId=product_id, boundingPoly=bounding_poly)

    expected_request = (self.ImageShortMessage('GetRequest')(
        name=expected_image.name))
    self.product_client.productSearch_catalogs_referenceImages.Get.Expect(
        expected_request, expected_image, exception=error)

    return expected_image

  def ExpectRefImageList(self, num=5, product_id='abc123'):
    ref_images = self.MakeRefImageList(num)
    expected_request = self.ImageShortMessage('ListRequest')(
        pageSize=10, parent='productSearch/catalogs/12345',
        productId=product_id)
    self.product_client.productSearch_catalogs_referenceImages.List.Expect(
        expected_request,
        self.messages.ListReferenceImagesResponse(referenceImages=ref_images))
    return ref_images


class MlProductsTestBase(sdk_test_base.WithFakeAuth,
                         cli_test_base.CliTestBase):
  """Base class for ml products command unit tests."""

  def RunProductsCommand(self, group, command):
    return self.Run('ml products {} {}'.format(group, command))

  def SetUp(self):
    """Creates api client mocks and adds Unmock on cleanup."""
    self.track = base.ReleaseTrack.ALPHA
    self.mock_client = mock.Client(
        apis.GetClientClass(product_util.PRODUCTS_API,
                            product_util.PRODUCTS_VERSION))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.mock_search_client = mock.Client(
        apis.GetClientClass(product_util.PRODUCTS_API,
                            product_util.PRODUCTS_SEARCH_VERSION))
    self.mock_search_client.Mock()
    self.addCleanup(self.mock_search_client.Unmock)
    self.client = product_util.ProductsClient()
    self.messages = self.client.messages
    self.search_messages = self.client.search_messages
    self.test_resources = ResourceUtils(self.messages,
                                        self.search_messages,
                                        self.mock_client,
                                        self.mock_search_client)
