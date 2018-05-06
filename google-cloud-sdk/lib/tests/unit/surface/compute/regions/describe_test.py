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
"""Tests for the regions describe subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class RegionsDescribeTest(test_base.BaseTest,
                          completer_test_base.CompleterBase,
                          test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.REGIONS[0]],
    ])

    self.Run("""
        compute regions describe region-1
        """)

    self.CheckRequests(
        [(self.compute_v1.regions,
          'Get',
          messages.ComputeRegionsGetRequest(
              project='my-project',
              region='region-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
              deprecated:
                deleted: '2015-03-29T00:00:00.000-07:00'
                replacement: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-2
                state: DEPRECATED
              name: region-1
              quotas:
              - limit: 24.0
                metric: CPUS
                usage: 0.0
              - limit: 5120.0
                metric: DISKS_TOTAL_GB
                usage: 30.0
              - limit: 7.0
                metric: STATIC_ADDRESSES
                usage: 1.0
              - limit: 24.0
                metric: IN_USE_ADDRESSES
                usage: 2.0
              selfLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1
              status: UP
            """))

  def testDescribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.REGIONS)
    self.RunCompletion('compute regions describe ',
                       ['region-1', 'region-2', 'region-3'])

if __name__ == '__main__':
  test_case.main()
