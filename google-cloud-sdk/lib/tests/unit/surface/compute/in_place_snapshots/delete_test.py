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
"""Tests for google3.third_party.py.tests.unit.surface.compute.in_place_snapshot.delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class ZoneInPlaceSnapshotsDeleteTestGA(test_base.BaseTest,
                                       sdk_test_base.WithLogCapture):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi(self.api_version)
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)


class ZoneInPlaceSnapshotsDeleteTestBeta(ZoneInPlaceSnapshotsDeleteTestGA):
  """Tests for features only available in beta."""

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class ZoneInPlaceSnapshotsDeleteTestAlpha(ZoneInPlaceSnapshotsDeleteTestBeta):
  """Tests for features only available in alpha."""

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testWithSingleZoneIPS(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute in-place-snapshots delete ips-1 --zone central2-a
        """)

    self.CheckRequests([
        (self.compute.zoneInPlaceSnapshots, 'Delete',
         self.messages.ComputeZoneInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-1', project='my-project', zone='central2-a'))
    ],)

  def testWithManyZoneIPS(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute in-place-snapshots delete ips-1 ips-2 ips-3 --zone central2-a
        """)

    self.CheckRequests([
        (self.compute.zoneInPlaceSnapshots, 'Delete',
         self.messages.ComputeZoneInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-1', project='my-project', zone='central2-a')),
        (self.compute.zoneInPlaceSnapshots, 'Delete',
         self.messages.ComputeZoneInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-2', project='my-project', zone='central2-a')),
        (self.compute.zoneInPlaceSnapshots, 'Delete',
         self.messages.ComputeZoneInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-3', project='my-project', zone='central2-a'))
    ],)

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute in-place-snapshots delete ips-1 ips-2 ips-3 --zone central2-a
        """)
    self.CheckRequests([
        (self.compute.zoneInPlaceSnapshots, 'Delete',
         self.messages.ComputeZoneInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-1', project='my-project', zone='central2-a')),
        (self.compute.zoneInPlaceSnapshots, 'Delete',
         self.messages.ComputeZoneInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-2', project='my-project', zone='central2-a')),
        (self.compute.zoneInPlaceSnapshots, 'Delete',
         self.messages.ComputeZoneInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-3', project='my-project', zone='central2-a'))
    ],)
    # pylint: disable=line-too-long
    self.AssertErrContains(
        r'The following zone in place snapshots will be deleted:\n'
        r' - [ips-1] in [central2-a]\n'
        r' - [ips-2] in [central2-a]\n'
        r' - [ips-3] in [central2-a]\n')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute in-place-snapshots delete ips-1 ips-2 ips-3 --zone central2-a
          """)

    self.CheckRequests()


class RegionInPlaceSnapshotsDeleteTestGA(test_base.BaseTest):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi(self.api_version)
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)


class RegionInPlaceSnapshotsDeleteTestBeta(ZoneInPlaceSnapshotsDeleteTestGA):
  """Tests for features only available in beta."""

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class RegionInPlaceSnapshotsDeleteTestAlpha(ZoneInPlaceSnapshotsDeleteTestBeta):
  """Tests for features only available in alpha."""

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testWithSingleRegionIPS(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute in-place-snapshots delete ips-1 --region central2
        """)

    self.CheckRequests([
        (self.compute.regionInPlaceSnapshots, 'Delete',
         self.messages.ComputeRegionInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-1', project='my-project', region='central2'))
    ],)

  def testWithManyRegionIPS(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute in-place-snapshots delete ips-1 ips-2 ips-3 --region central2
        """)

    self.CheckRequests([
        (self.compute.regionInPlaceSnapshots, 'Delete',
         self.messages.ComputeRegionInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-1', project='my-project', region='central2')),
        (self.compute.regionInPlaceSnapshots, 'Delete',
         self.messages.ComputeRegionInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-2', project='my-project', region='central2')),
        (self.compute.regionInPlaceSnapshots, 'Delete',
         self.messages.ComputeRegionInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-3', project='my-project', region='central2'))
    ],)

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute in-place-snapshots delete ips-1 ips-2 ips-3 --region central2
        """)
    self.CheckRequests([
        (self.compute.regionInPlaceSnapshots, 'Delete',
         self.messages.ComputeRegionInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-1', project='my-project', region='central2')),
        (self.compute.regionInPlaceSnapshots, 'Delete',
         self.messages.ComputeRegionInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-2', project='my-project', region='central2')),
        (self.compute.regionInPlaceSnapshots, 'Delete',
         self.messages.ComputeRegionInPlaceSnapshotsDeleteRequest(
             inPlaceSnapshot='ips-3', project='my-project', region='central2'))
    ],)
    # pylint: disable=line-too-long
    self.AssertErrContains(
        r'The following region in place snapshots will be deleted:\n'
        r' - [ips-1] in [central2]\n'
        r' - [ips-2] in [central2]\n'
        r' - [ips-3] in [central2]\n')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute in-place-snapshots delete ips-1 ips-2 ips-3 --region central2
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
