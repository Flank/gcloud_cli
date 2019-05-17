# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for 'memberships describe' command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import yaml
from tests.lib import test_case
from tests.lib.surface.container.memberships import base


class DescribeTestAlpha(base.MembershipsTestBase):
  """gcloud Alpha track using container v1 API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDescribeDefaults(self):
    self.ExpectGetMembership(self._MakeMembership())

    self.WriteInput('y')
    self._RunMembershipCommand(['describe', self.MEMBERSHIP_NAME])

    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)
    kwargs = {
        'name': self.MEMBERSHIP_NAME,
        'description': self.MEMBERSHIP_DESCRIPTION,
    }
    for k in out:
      self.assertEquals(out[k], kwargs[k])


if __name__ == '__main__':
  test_case.main()
