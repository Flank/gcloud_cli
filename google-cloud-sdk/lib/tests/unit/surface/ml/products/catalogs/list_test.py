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

"""ml products catalogs list tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.ml.products import base


class ListTest(base.MlProductsTestBase):
  """ml products catalogs list command tests."""

  def SetUp(self):
    self.catalogs = self.test_resources.MakeCatalogList(5)
    self.mock_client.productSearch_catalogs.List.Expect(
        self.messages.AlphaVisionProductSearchCatalogsListRequest(),
        self.messages.GoogleCloudVisionV1alpha1ListCatalogsResponse(
            catalogs=self.catalogs))

  def testList(self):
    results = self.RunProductsCommand('catalogs', 'list')
    self.assertEqual(results, self.catalogs)

  def testListFormat(self):
    self.RunProductsCommand('catalogs', 'list')
    self.AssertOutputContains("""\
NAME                      CATALOG_ID
productSearch/catalogs/0  0
productSearch/catalogs/1  1
productSearch/catalogs/2  2
productSearch/catalogs/3  3
productSearch/catalogs/4  4
    """, normalize_space=True)

if __name__ == '__main__':
  test_case.main()
