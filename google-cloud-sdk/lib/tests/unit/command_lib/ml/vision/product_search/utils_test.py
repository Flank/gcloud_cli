# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.

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
"""Tests for the utils of product search."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml.vision import api_utils
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.ml.vision.product_search import utils
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base

import mock


def _GetMockArgsForPolygon(parsed_polygon):
  polygon = {'bounding_polygon': parsed_polygon}
  args_mock = mock.create_autospec(
      parser_extensions.Namespace, instance=True, **polygon)
  args_mock.IsSpecified.return_value = True
  return args_mock


class ProductSearchUtils(parameterized.TestCase,
                         concepts_test_base.ConceptsTestBase):

  def SetUp(self):
    self.message = api_utils.GetMessage()
    self.args_mock = mock.create_autospec(
        parser_extensions.Namespace, instance=True, product='my_product')
    self.ref_mock = mock.create_autospec(
        resources.Resource,
        instance=True,
        projectsId='my_project',
        locationsId='my_location')

  @parameterized.parameters(
      (['--product-labels=k1=v1'], [('k1', 'v1')]),
      (['--product-labels=k1=v1,k1=v2'], [('k1', 'v1'), ('k1', 'v2')]),
      (['--product-labels=k1=v1', '--product-labels=k2=v2'], [('k1', 'v1'),
                                                              ('k2', 'v2')]),
      (['--product-labels=k1=v1', '--product-labels=k1=v2'], [('k1', 'v1'),
                                                              ('k1', 'v2')]),
      (['--product-labels=k1=v1,k1=v1'], [('k1', 'v1')]))
  def testPrepareProductLabelsForProductCreationRequest(self, args,
                                                        expected_labels):
    utils.ProductLabelsArgumentsForCreate()[0].AddToParser(self.parser)
    args = self.parser.parser.parse_args(args)
    product = self.message.Product(
        description='desc', displayName='display_name')
    input_request = self.message.VisionProjectsLocationsProductsCreateRequest(
        parent='projects/my_project/locations/my_location',
        product=product,
        productId='my_product')
    fixed_request = utils.PrepareProductLabelsForProductCreationRequest(
        None, args, input_request)
    expected_labels = [
        self.message.KeyValue(key=k, value=v) for k, v in expected_labels
    ]
    self.assertEqual(expected_labels, fixed_request.product.productLabels)

  @parameterized.parameters(
      (['--clear-product-labels'], [('k1', 'v1'), ('k2', 'v2')], []),
      (['--clear-product-labels', '--add-product-labels=k1=v1'
       ], [('k1', 'v2')], [('k1', 'v1')]),
      (['--remove-product-labels=k1=v1'], [('k1', 'v1'),
                                           ('k2', 'v2')], [('k2', 'v2')]),
      (['--remove-product-labels=k1=v1', '--add-product-labels=k1=v2'
       ], [('k1', 'v1')], [('k1', 'v2')]))
  def testUpdateLabelsForProductUpdateRequest(self, args, existing_labels,
                                              expected_labels):
    for argument in utils.ProductLabelsArgumentsForUpdate():
      argument.AddToParser(self.parser)

    existing_labels = [
        self.message.KeyValue(key=k, value=v) for k, v in existing_labels
    ]
    self.StartPatch(
        'googlecloudsdk.command_lib.ml.vision.product_search.utils._GetExistingProductLabels',
        return_value=existing_labels)

    expected_labels = [
        self.message.KeyValue(key=k, value=v) for k, v in expected_labels
    ]
    product = self.message.Product(
        description='desc',
        displayName='display_name',
        productLabels=existing_labels)

    args = self.parser.parser.parse_args(args)
    input_request = self.message.VisionProjectsLocationsProductsPatchRequest(
        name='projects/my_project/location/my_location/products/my_product',
        product=product)
    fixed_request = utils.UpdateLabelsAndUpdateMaskForProductUpdateRequest(
        None, args, input_request)
    self.assertEqual(expected_labels, fixed_request.product.productLabels)

  def testAddBoundingPolygonsToReferenceImageCreationRequest(self):
    polygons = {
        'bounding_polygon': [{
            'vertices': [{
                'x': '0',
                'y': '0'
            }, {
                'x': '0',
                'y': '10'
            }]
        }, {
            'normalized-vertices': [{
                'x': '0.8',
                'y': '0.1'
            }, {
                'x': '0.8',
                'y': '1'
            }]
        }]
    }
    args_mock = mock.create_autospec(
        parser_extensions.Namespace, instance=True, **polygons)
    args_mock.IsSpecified.return_value = True
    request = self.message.VisionProjectsLocationsProductsReferenceImagesCreateRequest(
    )
    request.referenceImage = self.message.ReferenceImage()
    utils.AddBoundingPolygonsToReferenceImageCreationRequest(
        None, args_mock, request)
    expected_vertices = [
        self.message.Vertex(x=0, y=0),
        self.message.Vertex(x=0, y=10)
    ]
    expected_bounding_poly_1 = self.message.BoundingPoly(
        vertices=expected_vertices)
    expected_normalized_vertices = [
        self.message.NormalizedVertex(x=0.8, y=0.1),
        self.message.NormalizedVertex(x=0.8, y=1)
    ]
    expected_bounding_poly_2 = self.message.BoundingPoly(
        normalizedVertices=expected_normalized_vertices)

    self.assertEqual([expected_bounding_poly_1, expected_bounding_poly_2],
                     request.referenceImage.boundingPolys)

  @parameterized.parameters(
      ('operations/123', 'operations/123'),
      ('operations/projects/my-projects/operations/123',
       'projects/my-projects/operations/123'),
      ('operations/locations/us-east1/operations/123',
       'locations/us-east1/operations/123'),
      ('operations/projects/my-project/locations/us-east1/operations/123',
       'projects/my-project/locations/us-east1/operations/123'))
  def testFixOperationNameInGetOperationRequest(self, name, expected_name):
    operation = self.message.VisionOperationsGetRequest(name=name)
    fixed_operation = utils.FixOperationNameInGetOperationRequest(
        None, None, operation)
    self.assertEqual(fixed_operation.name, expected_name)

  def testFixProductInAddProductToProductSetRequest(self):
    add_product_to_product_set = self.message.AddProductToProductSetRequest(
        product='some random value')
    input_request = self.message.VisionProjectsLocationsProductSetsAddProductRequest(
        addProductToProductSetRequest=add_product_to_product_set, name='')
    fixed_request = utils.FixProductInAddProductToProductSetRequest(
        self.ref_mock, self.args_mock, input_request)
    self.assertEqual(
        fixed_request.addProductToProductSetRequest.product,
        'projects/my_project/locations/my_location/products/my_product')

  def testFixProductInRemoveProductFromProductSetRequest(self):
    remove_product_from_product_set = self.message.RemoveProductFromProductSetRequest(
        product='some random value')
    input_request = self.message.VisionProjectsLocationsProductSetsRemoveProductRequest(
        removeProductFromProductSetRequest=remove_product_from_product_set,
        name='')
    fixed_request = utils.FixProductInRemoveProductFromProductSetRequest(
        self.ref_mock, self.args_mock, input_request)
    self.assertEqual(
        fixed_request.removeProductFromProductSetRequest.product,
        'projects/my_project/locations/my_location/products/my_product')

  def testFixNameInListProductsInProductSetRequest(self):
    input_request = self.message.VisionProjectsLocationsProductSetsProductsListRequest(
        name='projects/my_project/locations/my_location/products/my_product/products'
    )
    fixed_request = utils.FixNameInListProductsInProductSetRequest(
        self.ref_mock, self.args_mock, input_request)
    self.assertEqual(
        fixed_request.name,
        'projects/my_project/locations/my_location/products/my_product')

  @parameterized.parameters(
      ('0.1,0.1,0.2,0.2',
       api_utils.GetMessage().BoundingPoly(normalizedVertices=[
           api_utils.GetMessage().NormalizedVertex(x=0.1, y=0.1),
           api_utils.GetMessage().NormalizedVertex(x=0.2, y=0.2)
       ])),
      ('1,1,10,10', api_utils.GetMessage().BoundingPoly(vertices=[
          api_utils.GetMessage().Vertex(x=1, y=1),
          api_utils.GetMessage().Vertex(x=10, y=10)
      ])),
  )
  def testAddBoundingPolygonToDetectProductRequest(self, polygon_arg,
                                                   expected_bounding_polygon):
    args_mock = _GetMockArgsForPolygon(polygon_arg)
    input_request = self.message.BatchAnnotateImagesRequest(requests=[
        self.message.AnnotateImageRequest(
            imageContext=self.message.ImageContext())
    ])
    expected_request = self.message.BatchAnnotateImagesRequest(requests=[
        self.message.AnnotateImageRequest(
            imageContext=self.message.ImageContext())
    ])
    expected_request.requests[
        0].imageContext.productSearchParams = self.message.ProductSearchParams(
            boundingPoly=expected_bounding_polygon)
    result_request = utils.AddBoundingPolygonToDetectProductRequest(
        None, args_mock, input_request)
    self.assertEqual(expected_request, result_request)

  @parameterized.parameters(('0.1,0.2,0.3',), ('1',))
  def testAddBoundingPolygonToDetectProductRequest_WrongValueCount(
      self, polygon_arg):
    args_mock = _GetMockArgsForPolygon(polygon_arg)
    input_request = self.message.BatchAnnotateImagesRequest(requests=[
        self.message.AnnotateImageRequest(
            imageContext=self.message.ImageContext())
    ])
    with self.AssertRaisesExceptionRegexp(utils.BoundingPolygonFormatError,
                                          r'.* even number .*'):
      utils.AddBoundingPolygonToDetectProductRequest(None, args_mock,
                                                     input_request)

  def testAddBoundingPolygonToDetectProductRequest_MixedIntegerFloat(self):
    args_mock = _GetMockArgsForPolygon('0.1,1')
    input_request = self.message.BatchAnnotateImagesRequest(requests=[
        self.message.AnnotateImageRequest(
            imageContext=self.message.ImageContext())
    ])
    with self.AssertRaisesExceptionRegexp(utils.BoundingPolygonFormatError,
                                          r'Coordinates of normalized .*'):
      utils.AddBoundingPolygonToDetectProductRequest(None, args_mock,
                                                     input_request)

  def testAddBoundingPolygonToDetectProductRequest_NegativeValues(self):
    args_mock = _GetMockArgsForPolygon('-0.1,-1.')
    input_request = self.message.BatchAnnotateImagesRequest(requests=[
        self.message.AnnotateImageRequest(
            imageContext=self.message.ImageContext())
    ])
    with self.AssertRaisesExceptionRegexp(utils.BoundingPolygonFormatError,
                                          r'Coordinates must be .*'):
      utils.AddBoundingPolygonToDetectProductRequest(None, args_mock,
                                                     input_request)

  def testGroupCoordinates(self):
    coordinates_input = ['0.1', '0.2', '0.3', '0.4']
    expected = [('0.1', '0.2'), ('0.3', '0.4')]
    res = utils.GroupCoordinates(coordinates_input)
    self.assertEqual(res, expected)

  def testGroupCoordinates_Exception(self):
    coordinates_input = ['0.1', '0.2', '0.3']
    with self.AssertRaisesExceptionRegexp(
        utils.BoundingPolygonFormatError, '.* an even number .*'):
      utils.GroupCoordinates(coordinates_input)

if __name__ == '__main__':
  test_case.main()
