# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the instant snapshots describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instant_snapshots import test_resources

messages = core_apis.GetMessagesModule('compute', 'alpha')


class InstantSnapshotDescribeTestAlpha(test_base.BaseTest,
                                       test_case.WithOutputCapture):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.SelectApi(self.api_version)

  def testSimpleCaseZonal(self):
    self.make_requests.side_effect = iter([
        [test_resources.INSTANT_SNAPSHOT_ALPHA[0]],
    ])

    self.Run("""
        compute instant-snapshots describe ips-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.zoneInstantSnapshots, 'Get',
          messages.ComputeZoneInstantSnapshotsGetRequest(
              project='my-project', instantSnapshot='ips-1', zone='zone-1'))],)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            ---
            diskSizeGb: '10'
            name: ips-1
            selfLink: https://compute.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/instantsnapshots/ips-1
            sourceDisk: https://compute.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/disks/disk-1
            status: READY
            zone: https://compute.googleapis.com/compute/alpha/projects/my-project/zones/zone-1
            """))

  def testSimpleCaseRegional(self):
    self.make_requests.side_effect = iter([
        [test_resources.INSTANT_SNAPSHOT_ALPHA[2]],
    ])

    self.Run("""
        compute instant-snapshots describe ips-3 --region region-1
        """)

    self.CheckRequests([
        (self.compute.regionInstantSnapshots, 'Get',
         messages.ComputeRegionInstantSnapshotsGetRequest(
             project='my-project', instantSnapshot='ips-3', region='region-1'))
    ],)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            ---
            diskSizeGb: '10'
            name: ips-3
            region: https://compute.googleapis.com/compute/alpha/projects/my-project/regions/region-1
            selfLink: https://compute.googleapis.com/compute/alpha/projects/my-project/regions/region-1/instantsnapshots/ips-3
            sourceDisk: https://compute.googleapis.com/compute/alpha/projects/my-project/regions/region-1/disks/disk-3
            status: READY
           """))


if __name__ == '__main__':
  test_case.main()
