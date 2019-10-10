# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud monitoring policies describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class MonitoringDescribeTest(base.MonitoringTestBase):

  def _MakePolicy(self):
    policy_name = ('projects/{}/'
                   'alertPolicies/policy-id').format(self.Project())
    return self.messages.AlertPolicy(
        name=policy_name,
        displayName='Policy Display Name',
    )

  def _ExpectDescribe(self, policy):
    self.client.projects_alertPolicies.Get.Expect(
        self.messages.MonitoringProjectsAlertPoliciesGetRequest(
            name=policy.name,
        ),
        policy)

  def testDescribe(self):
    policy = self._MakePolicy()
    self._ExpectDescribe(policy)

    self.Run('monitoring policies describe policy-id')

  def testDescribe_Uri(self):
    policy = self._MakePolicy()
    self._ExpectDescribe(policy)
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')

    url = ('http://monitoring.googleapis.com/v3/projects/{}'
           '/alertPolicies/policy-id').format(self.Project())
    self.Run('monitoring policies describe ' + url)

  def testDescribe_RelativeName(self):
    policy = self._MakePolicy()
    self._ExpectDescribe(policy)
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')

    relative_name = ('projects/{}/alertPolicies/'
                     'policy-id').format(self.Project())
    self.Run('monitoring policies describe ' + relative_name)


if __name__ == '__main__':
  test_case.main()
