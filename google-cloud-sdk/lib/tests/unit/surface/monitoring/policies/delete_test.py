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
"""Tests for `gcloud monitoring policies delete`."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class MonitoringDeleteTest(base.MonitoringTestBase):

  def _ExpectDelete(self):
    policy_name = ('projects/{}/'
                   'alertPolicies/policy-id').format(self.Project())
    self.client.projects_alertPolicies.Delete.Expect(
        self.messages.MonitoringProjectsAlertPoliciesDeleteRequest(
            name=policy_name,
        ),
        self.messages.Empty())

  def testDelete(self):
    self._ExpectDelete()
    self.WriteInput('y')
    self.Run('monitoring policies delete policy-id')

    self.AssertOutputEquals('')
    self.AssertErrContains('Do you want to continue')

  def testDelete_Cancel(self):
    self.WriteInput('n')

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('monitoring policies delete policy-id')

    self.AssertOutputEquals('')
    self.AssertErrContains('Do you want to continue')

  def testDelete_Uri(self):
    self._ExpectDelete()
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')
    self.WriteInput('y')

    url = ('http://monitoring.googleapis.com/v3/projects/{}'
           '/alertPolicies/policy-id').format(self.Project())
    self.Run('monitoring policies delete ' + url)

    self.AssertOutputEquals('')
    self.AssertErrContains('Do you want to continue')

  def testDelete_RelativeName(self):
    self._ExpectDelete()
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')
    self.WriteInput('y')

    relative_name = ('projects/{}/alertPolicies/'
                     'policy-id').format(self.Project())
    self.Run('monitoring policies delete ' + relative_name)

    self.AssertOutputEquals('')
    self.AssertErrContains('Do you want to continue')


if __name__ == '__main__':
  test_case.main()
