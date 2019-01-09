# -*- coding: utf-8 -*- #
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
"""E2e test for 'category-manager stores get-common' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.category_manager import utils
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class GetCommonE2eTest(e2e_base.WithServiceAuth):
  """E2e test for get-common command."""

  @test_case.Filters.skip('Failing', 'b/121190998')
  def testGetCommon(self):
    """Test getting common store."""
    common_store = self.Run('alpha category-manager stores get-common')
    self.assertEqual(
        common_store,
        utils.GetMessagesModule().TaxonomyStore(
            name='taxonomyStores/predefined'))


if __name__ == '__main__':
  sdk_test_base.main()
