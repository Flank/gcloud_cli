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
"""ml products reference-images list tests."""
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.ml.products import base


class ListTest(base.MlProductsTestBase):
  """ml products catalogs list command tests."""

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def testList(self):
    ref_images = self.test_resources.ExpectRefImageList(product_id=None)

    results = self.RunProductsCommand(
        'reference-images', 'list --catalog=12345')
    self.assertEqual(results, ref_images)

  def testListWithProductId(self):
    expected_results = self.test_resources.ExpectRefImageList()
    results = self.RunProductsCommand(
        'reference-images', 'list --catalog=12345 --product-id=abc123')
    self.assertEqual(results, expected_results)

  def testListWithBadProductId(self):
    with self.assertRaisesRegexp(cli_test_base.MockArgumentError,
                                 (r'Product Id is restricted to 255 characters '
                                  r'including letters, numbers, underscore '
                                  r'\( _ \) and hyphen \(-\)')):
      self.RunProductsCommand(
          'reference-images', 'list --catalog=12345 --product-id=B@D*ID')

  def testListFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.test_resources.ExpectRefImageList()
    self.RunProductsCommand('reference-images',
                            'list --catalog=12345 --product-id abc123')
    self.AssertOutputContains("""\
NAME  CATALOG_ID  PRODUCT_ID  IMAGE_URI                   CATEGORY
0     12345       abc123      gs://fake-bucket/myimage-0
1     12345       abc123      gs://fake-bucket/myimage-1
2     12345       abc123      gs://fake-bucket/myimage-2
3     12345       abc123      gs://fake-bucket/myimage-3
4     12345       abc123      gs://fake-bucket/myimage-4
    """, normalize_space=True)

if __name__ == '__main__':
  test_case.main()
