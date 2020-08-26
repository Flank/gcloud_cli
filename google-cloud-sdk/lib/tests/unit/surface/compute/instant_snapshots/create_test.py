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
"""Tests for google3.third_party.py.tests.unit.surface.compute.instant_snapshot.create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import six


class ZoneInstantSnapshotsCreateTestGA(test_base.BaseTest,
                                       sdk_test_base.WithLogCapture):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi(self.api_version)


class ZoneInstantSnapshotsCreateTestBeta(ZoneInstantSnapshotsCreateTestGA):
  """Tests for features only available in beta."""

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SelectApi(self.api_version)


class ZoneInstantSnapshotsCreateTestAlpha(ZoneInstantSnapshotsCreateTestBeta):
  """Tests for features only available in alpha."""

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.SelectApi(self.api_version)

  def testCreateZonalIPS(self):
    self.Run("""
        compute instant-snapshots create ips-1 --zone zone-1
          --source-disk disk-1
        """)

    self.CheckRequests(
        [(self.compute.zoneInstantSnapshots, 'Insert',
          self.messages.ComputeZoneInstantSnapshotsInsertRequest(
              instantSnapshot=self.messages.InstantSnapshot(
                  name='ips-1',
                  sourceDisk=self.compute_uri + '/projects/my-project/zones/'
                  'zone-1/disks/disk-1'),
              project='my-project',
              zone='zone-1',
          ))],)

  def testCreateWithLabels(self):

    self.Run("""
       compute instant-snapshots create ips-with-labels
         --zone zone-1
         --source-disk my-disk
         --labels k0=v0,k-1=v-1
         --labels foo=bar
       """)

    labels_in_request = {'k0': 'v0', 'k-1': 'v-1', 'foo': 'bar'}
    self.CheckRequests(
        [(
            self.compute.zoneInstantSnapshots,
            'Insert',
            self.messages.ComputeZoneInstantSnapshotsInsertRequest(
                instantSnapshot=self.messages.InstantSnapshot(
                    labels=self.messages.InstantSnapshot.LabelsValue(
                        additionalProperties=[
                            self.messages.InstantSnapshot.LabelsValue  # pylint:disable=g-complex-comprehension
                            .AdditionalProperty(key=key, value=value)
                            for key, value in sorted(
                                six.iteritems(labels_in_request))
                        ]),
                    name='ips-with-labels',
                    sourceDisk=(self.compute_uri + '/projects/'
                                'my-project/zones/zone-1/disks/my-disk')),
                project='my-project',
                zone='zone-1'))],)

  def testCreateWithInvalidLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
          compute instant-snapshots create ips-with-labels
            --source-disk my-disk
            --source-disk-zone us-central1-a
            --labels inv@lid-key=inv@l!d-value
          """)


class RegionInstantSnapshotsCreateTestGA(test_base.BaseTest,
                                         sdk_test_base.WithLogCapture):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi(self.api_version)
    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(name='central2',),
        ],
        [],
    ])


class RegionInstantSnapshotsCreateTestBeta(ZoneInstantSnapshotsCreateTestGA):
  """Tests for features only available in beta."""

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SelectApi(self.api_version)


class RegionInstantSnapshotsCreateTestAlpha(RegionInstantSnapshotsCreateTestBeta
                                           ):
  """Tests for features only available in alpha."""

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.SelectApi(self.api_version)

  def testCreateRegionalIPS(self):
    self.Run("""
        compute instant-snapshots create ips-1 --region central2
          --source-disk disk-1
        """)

    self.CheckRequests(
        [(self.compute.regionInstantSnapshots, 'Insert',
          self.messages.ComputeRegionInstantSnapshotsInsertRequest(
              instantSnapshot=self.messages.InstantSnapshot(
                  name='ips-1',
                  sourceDisk=self.compute_uri + '/projects/my-project/regions/'
                  'central2/disks/disk-1'),
              project='my-project',
              region='central2',
          ))],)


if __name__ == '__main__':
  test_case.main()
