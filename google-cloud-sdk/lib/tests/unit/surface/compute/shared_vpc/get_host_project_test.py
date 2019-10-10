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
"""Tests for `gcloud compute shared-vpc get-host-project`."""

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
class GetHostProjectTest(shared_vpc_test_base.SharedVpcTestBase):

  def testGetHostProject_NoProject(self, track):
    self._SetUp(track)
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID: Must be specified.'):
      self.Run('compute shared-vpc get-host-project')
    self.xpn_client.EnableHost.assert_not_called()

  def testGetHostProject(self, track):
    self._SetUp(track)
    project_status_enum = self.messages.Project.XpnProjectStatusValueValuesEnum
    project = self.messages.Project(
        name='xpn-host',
        creationTimestamp='2013-09-06T17:54:10.636-07:00',
        selfLink='https://compute.googleapis.com/compute/alpha/projects/xpn-host/',
        xpnProjectStatus=project_status_enum.HOST
    )
    self.xpn_client.GetHostProject.return_value = project

    self.Run('compute shared-vpc get-host-project foo')

    self.AssertOutputEquals("""\
        creationTimestamp: '2013-09-06T17:54:10.636-07:00'
        name: xpn-host
        selfLink: https://compute.googleapis.com/compute/alpha/projects/xpn-host/
        xpnProjectStatus: HOST
        """, normalize_space=True)
    self.xpn_client.GetHostProject.assert_called_once_with('foo')
    self.get_xpn_client_mock.assert_called_once_with(self.track)


if __name__ == '__main__':
  test_case.main()
