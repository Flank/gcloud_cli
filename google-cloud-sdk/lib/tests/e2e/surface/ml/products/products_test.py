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
"""e2e tests for ml products catalogs command group."""
import contextlib

from googlecloudsdk.api_lib.ml.products import product_util
from googlecloudsdk.calliope import base
from tests.lib import e2e_base
from tests.lib import test_case

PRODUCT_ID = 'gcloud-test-shoes'
BUCKET_URI_ROOT = 'gs://gcloud-ml-productsearch-test/{}'


class ProductsTests(e2e_base.WithServiceAuth):
  """E2E tests for ml products catalogs command group."""

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

  @contextlib.contextmanager
  def _CreateCatalog(self):
    try:
      catalog = self.Run('ml products catalogs create')
      self.assertTrue(catalog)
      yield catalog
    finally:
      api_client = product_util.ProductsClient()
      api_client.DeleteCatalog(catalog.name)

  def testCatalogWorkflow(self):
    with self._CreateCatalog() as catalog:
      image_path = BUCKET_URI_ROOT.format('ref-image-test/shoe1.jpg')
      ref_image = self.Run('ml products reference-images add {} --catalog {}'
                           ' --product-id {}'.format(
                               image_path, catalog.name, PRODUCT_ID))
      self.assertTrue(ref_image)
      image_list = self.Run(
          'ml products reference-images list --catalog {}'.format(catalog.name))
      self.assertTrue(image_list)
      image_desc = self.Run(
          'ml products reference-images describe {}'.format(ref_image.name))
      self.assertTrue(image_desc)

      image_search = self.Run(
          'ml products search {} --catalog {}'.format(image_path, catalog.name))
      self.assertTrue(image_search)

if __name__ == '__main__':
  test_case.main()
