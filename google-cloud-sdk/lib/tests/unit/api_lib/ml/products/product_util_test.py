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
"""Tests for the ML vision api_lib products_utils."""

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.ml.products import product_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.ml.products import base


class ProductsApiClientTest(sdk_test_base.WithFakeAuth,
                            cli_test_base.CliTestBase):

  def _GetMessages(self):
    self.messages = self.client.messages
    self.search_messages = self.client.search_messages

  def SetUp(self):
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
    # Client Under test
    self.client = product_util.ProductsClient()
    self._GetMessages()
    self.test_resources = base.ResourceUtils(
        self.messages, self.search_messages,
        self.mock_client, self.mock_search_client)
    self.test_bounds = self.messages.BoundingPoly(vertices=[
        self.messages.Vertex(x=200, y=200),
        self.messages.Vertex(x=200, y=400),
        self.messages.Vertex(x=400, y=200),
        self.messages.Vertex(x=400, y=400)
    ])
    self.test_catalog = 'productSearch/catalogs/12345'

  def TearDown(self):
    # Join threads for operation waiter.py tests.
    self.JoinAllThreads(timeout=2)

# ReferenceImages
  def testBuildBoundingPoly(self):
    vertices = ['200:200', '200:400', '400:200', '400:400']
    # Build Expected Poly Message
    expected_bounds = self.test_bounds
    self.assertEqual(expected_bounds, self.client.BuildBoundingPoly(vertices))
    self.assertIsNone(self.client.BuildBoundingPoly([]))

  def testBuildBoundingPolyBadVertices(self):
    with self.assertRaisesRegexp(product_util.InvalidBoundsError,
                                 'Too few vertices'):
      self.client.BuildBoundingPoly(['200:200', '200:400'])

    with self.assertRaisesRegexp(
        product_util.InvalidBoundsError,
        r'vertices must be a list of coordinate pairs representing the '
        r'vertices of the bounding polygon e.g. \[x1:y1, x2:y2, x3:y3,...\].'):
      self.client.BuildBoundingPoly(['200:200', '200:400', '400'])

    with self.assertRaisesRegexp(
        product_util.InvalidBoundsError,
        r'vertices must be a list of coordinate pairs representing the '
        r'vertices of the bounding polygon e.g. \[x1:y1, x2:y2, x3:y3,...\].'):
      self.client.BuildBoundingPoly(['200,200', '200,400', '400,200'])

  def testBuildRefImage(self):
    expected_image = self.messages.ReferenceImage(imageUri='gs://fake/image',
                                                  productCategory='test-hats',
                                                  productId='abc123',
                                                  boundingPoly=self.test_bounds)
    self.assertEqual(expected_image, self.client.BuildRefImage(
        'abc123', 'gs://fake/image',
        bounds=self.test_bounds,
        product_category='test-hats'))

  def testBuildRefImageBadParams(self):
    # Bad ProductId
    with self.assertRaisesRegexp(product_util.ProductIdError,
                                 r'Invalid product_id \[abc 123\]'):
      self.client.BuildRefImage('abc 123', 'gs://fake-bucket')
    # Bad Bounds
    with self.assertRaises(TypeError):
      self.client.BuildRefImage('abc-123', 'gs://fake-bucket', bounds='BAD')

    # Bad imageURI
    with self.assertRaises(product_util.GcsPathError):
      self.client.BuildRefImage('abc-123', 'not://good-fake-bucket')

  def testCreateRefImage(self):
    expected_output = self.test_resources.ExpectRefImageCreate()
    returned_output = self.client.CreateRefImage(expected_output,
                                                 self.test_catalog)
    self.assertEqual(expected_output, returned_output)

  def testDeleteRefImage(self):
    to_delete = self.test_resources.ExpectRefImageDelete()
    result = self.client.DeleteRefImage(to_delete.name)
    self.assertEqual(result, self.messages.Empty)

  def testDescribeRefImage(self):
    expected_output = self.test_resources.ExpectRefImageDescribe()
    returned_output = self.client.DescribeRefImage(expected_output.name)
    self.assertEqual(expected_output, returned_output)

  def testListRefImages(self):
    ref_images = self.test_resources.MakeRefImageList()
    expected_request = self.client.ref_image_list_msg(
        pageSize=10, parent='productSearch/catalogs/12345', productId='abc123')
    self.client.ref_image_service.List.Expect(
        expected_request,
        self.messages.ListReferenceImagesResponse(referenceImages=ref_images))
    result_generator = self.client.ListRefImages('productSearch/catalogs/12345',
                                                 product_id='abc123')
    self.assertEqual(ref_images, list(result_generator))

  def testCreateCatalog(self):
    expected_output = self.test_resources.ExpectCreateCatalog()
    returned_output = self.client.CreateCatalog()
    self.assertEqual(expected_output, returned_output)

  def testDeleteCatalog(self):
    to_delete = self.test_resources.ExpectDeleteCatalog()
    result = self.client.DeleteCatalog(to_delete.name)
    self.assertEqual(result, to_delete.name)

  def testListCatalogs(self):
    catalogs = self.test_resources.MakeCatalogList()
    self.client.catalog_service.List.Expect(
        self.client.list_catalogs_msg(),
        self.messages.ListCatalogsResponse(catalogs=catalogs))
    results = self.client.ListCatalogs()
    self.assertEqual(catalogs, results)

  def testImportCatalog(self):
    self.StartPatch('time.sleep')
    import_response = self.test_resources.GetTestOperation('import')
    imported_images_response = self.test_resources.GetImportOperationResponse()
    import_response.response = imported_images_response

    import_config = self.messages.ImportCatalogsInputConfig(
        gcsSource=self.messages.ImportCatalogsGcsSource(
            csvFileUri='gs://fake-bucket/mycatalog'))
    self.client.catalog_service.Import.Expect(
        self.messages.ImportCatalogsRequest(inputConfig=import_config),
        import_response)
    self.test_resources.ExpectLongRunningOpResult(
        'operations/import', poll_count=3,
        response_value=imported_images_response)

    import_result = self.client.ImportCatalog('gs://fake-bucket/mycatalog')
    decoded_expected_response = encoding.JsonToMessage(
        self.messages.ImportCatalogsResponse,
        encoding.MessageToJson(imported_images_response))
    self.assertEqual(decoded_expected_response, import_result)

  def testImportCatalogBucketError(self):
    with self.assertRaisesRegexp(
        product_util.GcsPathError,
        r'The catalog csv file path \[NOT_A_BUCKET\] is not a properly '
        r'formatted URI for a remote catalog csv file. URI must be a Google '
        r'Cloud Storage image URI, in the form `gs://bucket_name/object_name`. '
        r'Please double-check your input and try again.'):
      self.client.ImportCatalog('NOT_A_BUCKET')

  def testDeleteProductCatalogImages(self):
    delete_images_req = self.client.delete_catalog_images_msg(
        parent='productSearch/catalogs/12345', productId='abc123')
    self.client.catalog_service.DeleteReferenceImages.Expect(
        request=delete_images_req, response=self.messages.Empty)
    result = self.client.DeleteProductCatalogImages(
        'productSearch/catalogs/12345', 'abc123')
    self.assertEqual(result, self.messages.Empty)

  def testWaitOperation(self):
    """Test WaitOperation method of client."""
    self.StartPatch('time.sleep')
    operation_ref = resources.REGISTRY.Parse(
        '12345', collection='alpha_vision.operations')
    complete_response = self.test_resources.GetImportOperationResponse()
    self.test_resources.ExpectLongRunningOpResult(
        'operations/12345', poll_count=4, response_value=complete_response)
    final_result = self.client.WaitOperation(operation_ref)
    self.assertEqual(final_result, complete_response)
    self.AssertErrContains(
        'Waiting for operation [operations/12345] to complete')

  def testWaitOperation_Error(self):
    """Test WaitOperation raises OperationError when operation has error."""
    self.StartPatch('time.sleep')
    operation_ref = resources.REGISTRY.Parse(
        '12345', collection='alpha_vision.operations')
    error = {'code': 400, 'message': 'Invalid Catalog config'}

    self.test_resources.ExpectLongRunningOpResult(
        'operations/12345', error_json=error)
    with self.assertRaisesRegexp(waiter.OperationError,
                                 r'Invalid Catalog config'):
      self.client.WaitOperation(operation_ref)

if __name__ == '__main__':
  test_case.main()
