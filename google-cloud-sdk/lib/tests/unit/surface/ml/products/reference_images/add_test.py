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

"""ml products reference-images add tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml.products import product_util
from googlecloudsdk.calliope import parser_errors
from tests.lib import test_case
from tests.lib.surface.ml.products import base


class AddTest(base.MlProductsTestBase):
  """ml products reference-images add command tests."""

  def SetUp(self):
    self.test_bounds = self.messages.BoundingPoly(vertices=[
        self.messages.Vertex(x=200, y=200),
        self.messages.Vertex(x=200, y=400),
        self.messages.Vertex(x=400, y=200),
        self.messages.Vertex(x=400, y=400)
    ])

  def testAddRequired(self):
    expected_image = self.test_resources.ExpectRefImageCreate(
        image_uri='gs://fake-bucket/myimage-0', product_category=None)
    self.mock_create = self.StartObjectPatch(
        product_util.ProductsClient, 'BuildRefImage',
        return_value=expected_image)
    added_image = self.RunProductsCommand(
        'reference-images', ('add gs://fake-bucket/myimage-0 '
                             '--catalog 12345 --product-id abc123'))
    self.assertEqual(added_image, expected_image)
    self.AssertErrContains(
        'Created ReferenceImage '
        '[productSearch/catalogs/12345/referenceImages/6789]')

  def testAddOptional(self):
    expected_image = self.test_resources.ExpectRefImageCreate(
        image_uri='gs://fake-bucket/myimage-0', bounding_poly=self.test_bounds)
    self.mock_create = self.StartObjectPatch(
        product_util.ProductsClient, 'BuildRefImage',
        return_value=expected_image)
    added_image = self.RunProductsCommand(
        'reference-images', ('add gs://fake-bucket/myimage-0 '
                             '--catalog 12345 --product-id abc123 '
                             '--category test-category '
                             '--bounds 200:200,200:400,400:200,400:400'))
    self.assertEqual(added_image, expected_image)
    self.AssertErrContains(
        'Created ReferenceImage '
        '[productSearch/catalogs/12345/referenceImages/6789]')

  def testAddMissingBounds(self):
    with self.assertRaisesRegex(parser_errors.ArgumentError,
                                (r'Missing \[bounds\]. Both category and '
                                 r'bounds must be specified if either is '
                                 r'provided')):
      self.RunProductsCommand('reference-images',
                              ('add gs://fake-bucket/myimage-0 '
                               '--catalog 12345 --product-id abc123 '
                               '--category test-category '))

  def testAddMissingCategory(self):
    with self.assertRaisesRegex(parser_errors.ArgumentError,
                                (r'Missing \[category\]. Both category and '
                                 r'bounds must be specified if either is '
                                 r'provided')):
      self.RunProductsCommand('reference-images',
                              ('add gs://fake-bucket/myimage-0 '
                               '--catalog 12345 --product-id abc123 '
                               '--bounds 200:200,200:400,400:200,400:400'))

if __name__ == '__main__':
  test_case.main()
