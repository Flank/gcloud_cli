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
"""Tests for google3.third_party.py.tests.unit.surface.compute.in_place_snapshot.list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_projector
from tests.lib import sdk_test_base
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class InPlaceSnapshotsListTestGA(test_base.BaseTest,
                                 sdk_test_base.WithLogCapture):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA


class InPlaceSnapshotsListTestBeta(InPlaceSnapshotsListTestGA):
  """Tests for features only available in beta."""

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InPlaceSnapshotsListTestAlpha(InPlaceSnapshotsListTestBeta):
  """Tests for features only available in alpha."""

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.MultiScopeLister', autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_multi_scope_lister = lister_patcher.start()
    self.mock_multi_scope_lister.return_value.return_value = (
        resource_projector.MakeSerializable(
            test_resources.IN_PLACE_SNAPSHOT_ALPHA))

  def testSimpleCaseUrl(self):
    self.Run("""
        compute in-place-snapshots list --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/inPlacesnapshots/ips-1
            https://compute.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/inPlacesnapshots/ips-2
            https://compute.googleapis.com/compute/alpha/projects/my-project/regions/region-1/inPlacesnapshots/ips-3
            https://compute.googleapis.com/compute/alpha/projects/my-project/regions/region-1/inPlacesnapshots/ips-4
            """))
    self.AssertErrEquals('')

  def testSimpleCase(self):
    self.Run("""
        compute in-place-snapshots list
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
              NAME LOCATION LOCATION_SCOPE STATUS
              ips-1 zone-1 zone READY
              ips-2 zone-1 zone READY
              ips-3 region-1 region READY
              ips-4 region-1 region READY
              """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testNameRegexes(self):
    self.Run("""
        compute in-place-snapshots list
          --uri
          --regexp "ips-1"
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/inPlacesnapshots/ips-1
            """))
