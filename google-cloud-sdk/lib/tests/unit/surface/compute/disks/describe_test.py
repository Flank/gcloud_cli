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
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_projector
from tests.lib import cli_test_base
from tests.lib import completer_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class DisksDescribeTestGA(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)

  def testSimpleCaseZonal(self):
    self.mock_client.disks.Get.Expect(
        self.messages.ComputeDisksGetRequest(
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

  def testSimpleCaseRegional(self):
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


class DisksDescribeTestBeta(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class DisksDescribeTestAlpha(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


class CompletionTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def testDescribeCompletion(self):

    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.MultiScopeLister',
        autospec=True)
    lister_mock.return_value.return_value = resource_projector.MakeSerializable(
        test_resources.DISKS)
    self.RunCompletion('compute disks describe --zone zone-1 d',
                       ['disk-1', 'disk-2', 'disk-3'])


if __name__ == '__main__':
  test_case.main()
