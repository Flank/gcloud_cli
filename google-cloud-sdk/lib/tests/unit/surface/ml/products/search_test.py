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

"""ml products search tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from apitools.base.py import encoding

from tests.lib import test_case
from tests.lib.surface.ml.products import base

from six.moves import map  # pylint: disable=redefined-builtin
from six.moves import range  # pylint: disable=redefined-builtin


class SearchTest(base.MlProductsTestBase):
  """ml products search command tests."""

  def _ExpectProductSearchResults(self, image_path, catalog, category=None,
                                  bounds=None, results=None,
                                  error_message=None, contents=None):
    """Expect request that lead to ProductSearchResults.

    Args:
      image_path: str, the path to the image.
      catalog: string, catalog name for the request.
      category: string, product category for request/response.
      bounds: NormalizedBoundingPoly, the bounds to use for the search.
      results: [Products], the list of product results to return.
      error_message: str, the error message to be given if an error is desired.
      contents: bytes, the contents of the Image message if desired.

    Returns:
      AnnotateImageResponse

    """
    feature = self.search_messages.Feature(
        type=self.search_messages.Feature.TypeValueValuesEnum.PRODUCT_SEARCH)
    image = self.search_messages.Image()
    if image_path:
      image.source = self.search_messages.ImageSource(imageUri=image_path)
    elif contents:
      image.content = contents
    search_params = self.search_messages.ProductSearchParams()
    search_params.normalizedBoundingPoly = bounds
    search_params.catalogName = catalog
    search_params.productCategory = category
    search_params.view = search_params.ViewValueValuesEnum('FULL')

    annotate_request = self.search_messages.AnnotateImageRequest(
        features=[feature],
        image=image,
        imageContext=self.search_messages.ImageContext(
            productSearchParams=search_params))

    annotate_response = self.search_messages.AnnotateImageResponse()
    if results:
      search_response = self.search_messages.ProductSearchResults()
      search_response.productCategory = category
      search_response.products = results
      annotate_response = self.search_messages.AnnotateImageResponse()
      annotate_response.productSearchResults = search_response

    if error_message:
      response = encoding.PyValueToMessage(
          self.search_messages.AnnotateImageResponse,
          {'error': {'code': 400,
                     'details': [],
                     'message': error_message}})
      annotate_response.error = response

    batch_request = self.search_messages.BatchAnnotateImagesRequest(
        requests=[annotate_request])
    batch_response = self.search_messages.BatchAnnotateImagesResponse(
        responses=[annotate_response])
    self.mock_search_client.images.Annotate.Expect(request=batch_request,
                                                   response=batch_response)
    return batch_response

  def _GetProductResponses(self, count=3):
    """Get test product search results."""
    return [
        self.search_messages.ProductInfo(
            imageUri='gs://fake-bucket/image{}.jpg'.format(i),
            productId='abc123',
            score=0.7) for i in range(count)
    ]

  def _MakeBounds(self, bounds):
    vertices = []
    for vertex in bounds:
      x_coord, y_coord = list(map(int, vertex.split(':')))
      vertices.append(
          self.search_messages.NormalizedVertex(x=x_coord, y=y_coord))
    return  self.search_messages.NormalizedBoundingPoly(vertices=vertices)

  def SetUp(self):
    self.test_bounds = ['200:200', '200:400', '400:200']

  def testSearchSimple(self):

    expected_output = self._ExpectProductSearchResults(
        'gs://fake-bucket/myimage0.jpg', 'productSearch/catalogs/12345',
        results=self._GetProductResponses())
    output = self.RunProductsCommand('',
                                     ('search gs://fake-bucket/myimage0.jpg '
                                      '--catalog 12345'))
    self.assertEqual(expected_output, output)

  def testSearchWithBoundsAndCategory(self):
    expected_output = self._ExpectProductSearchResults(
        'gs://fake-bucket/myimage0.jpg',
        'productSearch/catalogs/12345',
        results=self._GetProductResponses(),
        category='shoes',
        bounds=self._MakeBounds(self.test_bounds))
    output = self.RunProductsCommand(
        '', ('search gs://fake-bucket/myimage0.jpg '
             '--catalog 12345 --category=shoes '
             '--bounds {} '.format(','.join(self.test_bounds))))
    self.assertEqual(expected_output, output)


if __name__ == '__main__':
  test_case.main()
