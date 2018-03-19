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
"""ml products catalogs delete tests."""

from tests.lib import test_case
from tests.lib.surface.ml.products import base


class DeleteTest(base.MlProductsTestBase):
  """ml products catalogs delete command tests."""

  def SetUp(self):
    self.test_resources.ExpectDeleteCatalog()

  def testDeleteById(self):
    self.WriteInput('y')
    result = self.RunProductsCommand('catalogs', 'delete 12345')
    self.assertEqual(result, 'productSearch/catalogs/12345')
    self.AssertErrContains('Deleted Catalog [12345].')

  def testDeleteByName(self):
    self.WriteInput('y')
    result = self.RunProductsCommand('catalogs',
                                     'delete productSearch/catalogs/12345')
    self.assertEqual(result, 'productSearch/catalogs/12345')
    self.AssertErrContains('Deleted Catalog [12345].')

if __name__ == '__main__':
  test_case.main()
