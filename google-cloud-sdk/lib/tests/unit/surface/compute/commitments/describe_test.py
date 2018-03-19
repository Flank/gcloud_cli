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
"""Tests for the disks describe subcommand."""
import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


def SetUpMockClient(api):
  mock_client = mock.Client(
      core_apis.GetClientClass('compute', api),
      real_client=core_apis.GetClientInstance('compute', api, no_http=True))
  mock_client.Mock()
  return mock_client


class RegionalDisksDescribeTest(sdk_test_base.WithFakeAuth,
                                cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.GA
    self.mock_client = SetUpMockClient('v1')
    self.addCleanup(self.mock_client.Unmock)
    self.messages = core_apis.GetMessagesModule('compute', 'v1')
    self.compute_uri = 'https://www.googleapis.com/compute/{}'.format(
        self.track.prefix or 'v1')

  def testSimpleCase(self):
    commitment = self.messages.Commitment(
        name='erech',
        plan=self.messages.Commitment.PlanValueValuesEnum.TWELVE_MONTH,
        region='{}/projects/my-project/regions/us-central1'.format(
            self.compute_uri),
        endTimestamp='2038-01-19T01:00:00Z',
        resources=[
            self.messages.ResourceCommitment(
                amount=500,
                type=(self.messages.ResourceCommitment.
                      TypeValueValuesEnum.VCPU),
            ),
            self.messages.ResourceCommitment(
                amount=12,
                type=(self.messages.ResourceCommitment.
                      TypeValueValuesEnum.MEMORY),
            ),
        ],
    )

    self.mock_client.regionCommitments.Get.Expect(
        self.messages.ComputeRegionCommitmentsGetRequest(
            commitment='erech',
            project='fake-project',
            region='region-1'),
        commitment,
    )
    self.Run("""
        compute commitments describe erech --region region-1
        """)

    self.assertMultiLineEqual(
        self.stdout.getvalue(),
        textwrap.dedent("""\
            endTimestamp: '2038-01-19T01:00:00Z'
            name: erech
            plan: TWELVE_MONTH
            region: https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1
            resources:
            - amount: '500'
              type: VCPU
            - amount: '12'
              type: MEMORY
            """))

