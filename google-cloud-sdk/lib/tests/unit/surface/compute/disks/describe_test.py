# -*- coding: utf-8 -*- #
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
"""Tests for the disks describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_projector
from tests.lib import cli_test_base
from tests.lib import completer_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


def SetUpMockClient(api):
  mock_client = mock.Client(
      core_apis.GetClientClass('compute', api),
      real_client=core_apis.GetClientInstance('compute', api, no_http=True))
  mock_client.Mock()
  return mock_client


class DisksDescribeTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_client = SetUpMockClient('v1')
    self.addCleanup(self.mock_client.Unmock)

  def testSimpleCase(self):
    self.mock_client.disks.Get.Expect(
        messages.ComputeDisksGetRequest(
            disk='my-disk',
            project='fake-project',
            zone='zone-1'),
        test_resources.DISKS[0]
    )

    self.Run("""
        compute disks describe my-disk --zone zone-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            name: disk-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/disks/disk-1
            sizeGb: '10'
            status: READY
            type: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/diskTypes/pd-ssd
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))


class CompletionTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def testDescribeCompletion(self):

    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.DISKS)
    self.RunCompletion('compute disks describe --zone zone-1 d',
                       ['disk-1', 'disk-2', 'disk-3'])


@parameterized.parameters((base.ReleaseTrack.ALPHA, 'alpha'),
                          (base.ReleaseTrack.BETA, 'beta'))
class RegionalDisksDescribeTest(sdk_test_base.WithFakeAuth,
                                cli_test_base.CliTestBase,
                                parameterized.TestCase):

  def _SetUp(self, track, api_version):
    self.mock_client = SetUpMockClient(api_version)
    self.addCleanup(self.mock_client.Unmock)
    self.messages = core_apis.GetMessagesModule('compute', api_version)
    self.track = track

  def testSimpleCase(self, track, api_version):
    self._SetUp(track, api_version)
    self.mock_client.regionDisks.Get.Expect(
        self.messages.ComputeRegionDisksGetRequest(
            disk='my-disk',
            project='fake-project',
            region='region-1'),
        self.messages.Disk(
            name='disk-1',
            selfLink=('https://www.googleapis.com/compute/v1/projects/'
                      'my-project/regions/region-1/disks/disk-1'),
            sizeGb=10,
            status=self.messages.Disk.StatusValueValuesEnum.READY,
            region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'regions/region-1'))
    )
    self.Run("""
        compute disks describe my-disk --region region-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            name: disk-1
            region: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/disks/disk-1
            sizeGb: '10'
            status: READY
            """))

if __name__ == '__main__':
  test_case.main()
