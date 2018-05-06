# Copyright 2017 Google Inc. All Rights Reserved.
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
"""ml-engine operations cancel tests."""
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class WaitTestBase(object):

  NUM_POLLS = 10

  def _ExpectGetOp(self, name, done=False):
    self.client.projects_operations.Get.Expect(
        self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/{}'.format(self.Project(), name)),
        self.msgs.GoogleLongrunningOperation(name=name, done=done))

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.StartPatch('time.sleep')

  def testWait_DoneAlready(self):
    self._ExpectGetOp('opId', done=True)
    self.assertEqual(
        self.Run('ml-engine operations wait opId'),
        self.msgs.GoogleLongrunningOperation(name='opId', done=True))

  def testWait_Polls(self):
    for _ in range(self.NUM_POLLS):
      self._ExpectGetOp('opId', done=False)
    self._ExpectGetOp('opId', done=True)
    self.assertEqual(
        self.Run('ml-engine operations wait opId'),
        self.msgs.GoogleLongrunningOperation(name='opId', done=True))


class WaitGaTest(WaitTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(WaitGaTest, self).SetUp()


class WaitBetaTest(WaitTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(WaitBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
