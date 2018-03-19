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
"""Tests for the target-pools describe subcommand."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetPoolsDescribeTest(test_base.BaseTest, test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_POOLS[0]],
    ])

    self.Run("""
        compute target-pools describe pool-1
          --region region-1
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'Get',
          messages.ComputeTargetPoolsGetRequest(
              project='my-project',
              region='region-1',
              targetPool='pool-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            backupPool: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-2
            name: pool-1
            region: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
            sessionAffinity: CLIENT_IP
            """))

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_POOLS[0]],
    ])

    self.Run("""
        compute target-pools describe
          https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'Get',
          messages.ComputeTargetPoolsGetRequest(
              project='my-project',
              region='region-1',
              targetPool='pool-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            backupPool: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-2
            name: pool-1
            region: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
            sessionAffinity: CLIENT_IP
            """))

  def testRegionPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Region(name='region-1'),
            messages.Region(name='region-2'),
            messages.Region(name='region-3'),
        ],

        [test_resources.TARGET_POOLS[0]],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute target-pools describe pool-1
        """)

    self.AssertErrContains('region-1')
    self.AssertErrContains('region-2')
    self.AssertErrContains('region-3')
    self.CheckRequests(
        self.regions_list_request,

        [(self.compute_v1.targetPools,
          'Get',
          messages.ComputeTargetPoolsGetRequest(
              project='my-project',
              region='region-1',
              targetPool='pool-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            backupPool: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-2
            name: pool-1
            region: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
            sessionAffinity: CLIENT_IP
            """))


if __name__ == '__main__':
  test_case.main()
