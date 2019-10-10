# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud compute shared-vpc associated-projects add`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import shared_vpc_test_base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class AddTest(shared_vpc_test_base.SharedVpcTestBase):

  def testAdd_NoProject(self, track):
    self._SetUp(track)
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID --host-project: Must be specified.'):
      self.Run('compute shared-vpc associated-projects add')
    self.xpn_client.EnableXpnAssociatedProject.assert_not_called()

  def testAdd(self, track):
    self._SetUp(track)
    self.Run('compute shared-vpc associated-projects add --host-project '
             'xpn-host xpn-user')
    self.xpn_client.EnableXpnAssociatedProject.assert_called_once_with(
        'xpn-host', 'xpn-user')
    self.get_xpn_client_mock.assert_called_once_with(self.track)


if __name__ == '__main__':
  test_case.main()
