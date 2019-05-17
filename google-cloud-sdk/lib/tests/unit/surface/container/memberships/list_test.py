# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.container.memberships import base


class ListTestAlpha(base.MembershipsTestBase):
  """gcloud Alpha track using gkehub v1 API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testListDefaults(self):
    membership = self._MakeMembership(
        name=self.MEMBERSHIP_NAME, description=self.MEMBERSHIP_DESCRIPTION)
    self.ExpectListMemberships([membership])

    self.WriteInput('y')
    self._RunMembershipCommand(['list'])
    expected_output = """\
NAME DESCRIPTION
{} {}
""".format(self.MEMBERSHIP_NAME, self.MEMBERSHIP_DESCRIPTION)
    self.AssertOutputEquals(expected_output, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
