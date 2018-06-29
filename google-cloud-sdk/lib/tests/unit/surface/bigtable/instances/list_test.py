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
"""Test of the 'list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class ListCommandTest(base.BigtableV2TestBase, cli_test_base.CliTestBase):

  def SetUp(self):
    self.cmd = 'bigtable instances list'
    self.svc = self.client.projects_instances.List
    self.msg = self.msgs.BigtableadminProjectsInstancesListRequest(
        parent='projects/' + self.Project())

  def testList(self):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.ListInstancesResponse(instances=[self.msgs.Instance(
            name='projects/theprojects/instances/theinstance',
            displayName='thedisplayname',
            state=self.msgs.Instance.StateValueValuesEnum.READY)]))
    self.Run(self.cmd)
    self.AssertOutputEquals('NAME         DISPLAY_NAME    STATE\n'
                            'theinstance  thedisplayname  READY\n')

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc, self.msg):
      self.Run(self.cmd)

  def testCompletion(self):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.ListInstancesResponse(instances=[self.msgs.Instance(
            name='projects/theprojects/instances/theinstance',
            displayName='thedisplayname',
            state=self.msgs.Instance.StateValueValuesEnum.READY)]))
    self.RunCompletion('beta bigtable instances update t',
                       ['theinstance\\ --project=theprojects'])


if __name__ == '__main__':
  test_case.main()
