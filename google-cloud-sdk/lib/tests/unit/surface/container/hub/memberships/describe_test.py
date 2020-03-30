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
"""Tests for the 'memberships describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import yaml
from tests.lib import test_case
from tests.lib.surface.container.hub.memberships import base


class DescribeTest(base.MembershipsTestBase):
  """gcloud GA track using GKE Hub API."""

  # TODO(b/116715821): add more negative tests.
  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testDescribeDefaults(self):
    membership = self._MakeMembership(
        name=self.MEMBERSHIP_NAME,
        description=self.MEMBERSHIP_DESCRIPTION,
        external_id=self.MEMBERSHIP_EXTERNAL_ID)
    self.ExpectGetMembership(membership)

    self.WriteInput('y')
    self._RunMembershipCommand(['describe', self.MEMBERSHIP_NAME])

    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)

    self.ShowTestOutput()
    kwargs = {
        'name': self.MEMBERSHIP_NAME,
        'description': self.MEMBERSHIP_DESCRIPTION,
        'externalId': self.MEMBERSHIP_EXTERNAL_ID
    }
    for k in out:
      self.assertEqual(out[k], kwargs[k])


class DescribeTestBeta(DescribeTest):
  """gcloud Beta track using GKE Hub API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DescribeTestAlpha(DescribeTestBeta):
  """gcloud Alpha track using GKE Hub API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
