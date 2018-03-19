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
"""category-manager version tests."""

from googlecloudsdk.api_lib.category_manager import store
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.category_manager import base


class CategoryManagerVerTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.get_iam_policy_mock = self.StartObjectPatch(
        store, 'GetIamPolicy', autospec=True)

  def testCategoryManagerNotGa(self):
    """Make sure category-manager is not a GA command."""
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, "Invalid choice: 'category-manager'"):
      self.Run('category-manager stores get-iam-policy')

  def testCategoryManagerBeta(self):
    """Make sure category-manager is not in beta yet."""
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, "Invalid choice: 'category-manager'"):
      self.Run('beta category-manager stores get-iam-policy')

  def testCategoryManagerAlpha(self):
    """Make sure category-manager is an alpha command."""
    self.ExpectGetTaxonomyStore('1', '0')
    self.Run('alpha category-manager stores get-iam-policy 1')
    self.AssertErrNotContains('Invalid')
    self.get_iam_policy_mock.assert_called_once()


if __name__ == '__main__':
  test_case.main()
