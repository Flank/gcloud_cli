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
"""Tests for the resource policies list command."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import resource_policies_base

import mock


class ListTest(resource_policies_base.TestBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = (
        resource_projector.MakeSerializable(self.resource_policies))

  def testList_Simple(self):
    self.Run('compute resource-policies list')
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute.resourcePolicies,
        project=self.Project(),
        http=self.mock_http(),
        requested_regions=[],
        filter_expr=None,
        batch_url='https://www.googleapis.com/batch/compute/alpha',
        errors=[])
    self.AssertOutputEquals("""\
        NAME     DESCRIPTION   REGION       CREATION_TIMESTAMP
        pol1                   us-central1  2017-10-26T17:54:10.636-07:00
        pol2     desc          us-central1  2017-10-27T17:54:10.636-07:00
      """, normalize_space=True)

if __name__ == '__main__':
  test_case.main()
