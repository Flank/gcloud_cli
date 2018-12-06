# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Test of the 'describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class DescribeCommandTest(base.BigtableV2TestBase,
                          sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.cmd = 'bigtable instances describe theinstance'
    self.svc = self.client.projects_instances.Get
    self.msg = self.msgs.BigtableadminProjectsInstancesGetRequest(
        name='projects/{0}/instances/theinstance'.format(self.Project()))

  def _RunSuccessTest(self, track):
    self.track = track
    self.svc.Expect(request=self.msg,
                    response=self.msgs.Instance(
                        name='projects/theprojects/instances/theinstance',
                        displayName='thedisplayname'))
    self.Run(self.cmd)
    self.AssertOutputContains('theinstance')
    self.AssertOutputContains('thedisplayname')

  def testDescribe(self, track):
    self._RunSuccessTest(track)

  def testDescribeByUri(self, track):
    self.cmd = (
        'bigtable instances describe https://bigtableadmin.googleapis.com/v2/'
        'projects/{0}/instances/theinstance'.format(self.Project()))
    self._RunSuccessTest(track)

  def testErrorResponse(self, track):
    self.track = track
    with self.AssertHttpResponseError(self.svc, self.msg):
      self.Run(self.cmd)


if __name__ == '__main__':
  test_case.main()
