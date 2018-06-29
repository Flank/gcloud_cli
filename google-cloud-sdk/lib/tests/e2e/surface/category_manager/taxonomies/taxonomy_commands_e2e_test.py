# Copyright 2018 Google Inc. All Rights Reserved.
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
"""E2e test for 'category-manager taxonomies' command group."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.category_manager import utils
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import e2e_base as base


class TaxonomyCommandsE2eTest(base.CategoryManagerE2eBase):
  """E2e test for taxonomy commands."""

  def testAllTaxonomyCommands(self):
    description = 'test-taxonomy-description'
    with self.CreateTaxonomyResource(description) as taxonomy:
      self.assertEqual(taxonomy.description, description)

      new_description = 'new-test-taxonomy-description'
      expected_taxonomy = utils.GetMessagesModule().Taxonomy(
          name=taxonomy.name,
          displayName=taxonomy.displayName,
          description=new_description)

      args = '"{}" --description "{}"'.format(taxonomy.name, new_description)
      updated_taxonomy = self.Run('category-manager taxonomies update ' + args)
      self.assertEqual(updated_taxonomy, expected_taxonomy)

      described_taxonomy = self.Run('category-manager taxonomies describe ' +
                                    taxonomy.name)
      self.assertEqual(described_taxonomy, expected_taxonomy)

      found_taxonomy = self._ListTaxonomiesAndReturnMatch(taxonomy.displayName)
      self.assertEqual(found_taxonomy, expected_taxonomy)


if __name__ == '__main__':
  sdk_test_base.main()
