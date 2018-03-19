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
"""Tests for `gcloud compute shared-vpc get-host-project`."""
from tests.lib import test_case
from tests.lib.surface.compute import xpn_test_base


class GetHostProjectTest(xpn_test_base.XpnTestBase):

  def testGetHostProject_NoProject(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID: Must be specified.'):
      self.Run('compute shared-vpc get-host-project')
    self.xpn_client.EnableHost.assert_not_called()

  def testGetHostProject(self):
    self._testGetHostProject('shared-vpc')

  def testGetHostProject_xpn(self):
    self._testGetHostProject('xpn')

  def _testGetHostProject(self, module_name):
    project_status_enum = self.messages.Project.XpnProjectStatusValueValuesEnum
    project = self.messages.Project(
        name='xpn-host',
        creationTimestamp='2013-09-06T17:54:10.636-07:00',
        selfLink='https://www.googleapis.com/compute/alpha/projects/xpn-host/',
        xpnProjectStatus=project_status_enum.HOST
    )
    self.xpn_client.GetHostProject.return_value = project

    self.Run('compute {} get-host-project foo'.format(module_name))

    self.AssertOutputEquals("""\
        creationTimestamp: '2013-09-06T17:54:10.636-07:00'
        name: xpn-host
        selfLink: https://www.googleapis.com/compute/alpha/projects/xpn-host/
        xpnProjectStatus: HOST
        """, normalize_space=True)
    self.xpn_client.GetHostProject.assert_called_once_with('foo')


if __name__ == '__main__':
  test_case.main()
