# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the zones list subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class ZonesListTest(test_base.BaseTest):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.ZONES))

  def testTabularOutput(self):
    self.Run("""
        compute zones list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.zones,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url='https://www.googleapis.com/batch/compute/v1',
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
NAME REGION STATUS NEXT_MAINTENANCE TURNDOWN_DATE
us-central1-a us-central1 UP (DEPRECATED) 2015-03-29T00:00:00.000-07:00
us-central1-b us-central1 UP
europe-west1-a europe-west1 UP
europe-west1-b europe-west1 DOWN (DELETED) 2015-03-29T00:00:00.000-07:00
            """), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
