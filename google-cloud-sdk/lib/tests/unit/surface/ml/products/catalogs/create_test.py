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

"""ml products catalogs create tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.ml.products import base


class CreateTest(base.MlProductsTestBase):
  """ml products catalogs create command tests."""

  def testCreate(self):
    expected_catalog = self.test_resources.ExpectCreateCatalog()
    created_catalog = self.RunProductsCommand('catalogs', 'create')
    self.assertEqual(expected_catalog, created_catalog)
    self.AssertErrContains('Created Catalog [productSearch/catalogs/12345]')


if __name__ == '__main__':
  test_case.main()
