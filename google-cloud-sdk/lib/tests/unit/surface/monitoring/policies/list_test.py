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
"""Tests for `gcloud monitoring policies list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.monitoring import base
from six.moves import range


class MonitoringListTest(base.MonitoringTestBase):

  def _MakePolicies(self, project=None, n=10):
    project = project or self.Project()
    policies = []
    for i in range(n):
      policy_name = ('projects/{0}/'
                     'alertPolicies/policy-id{1}').format(project, i)
      policy = self.messages.AlertPolicy(
          name=policy_name,
          displayName='Policy Display Name',
      )
      policies.append(policy)
    return policies

  def _ExpectList(self, policies, project=None, page_size=None, page_token=None,
                  next_page_token=None, order_by=None):
    project = project or self.Project()
    self.client.projects_alertPolicies.List.Expect(
        self.messages.MonitoringProjectsAlertPoliciesListRequest(
            name='projects/{}'.format(project),
            pageToken=page_token,
            pageSize=page_size,
            orderBy=order_by,
        ),
        self.messages.ListAlertPoliciesResponse(
            alertPolicies=policies,
            nextPageToken=next_page_token))

  def testList(self):
    policies = self._MakePolicies()
    self._ExpectList(policies)

    results = self.Run('monitoring policies list')

    self.assertEqual(results, policies)

  def testList_Uri(self):
    jobs = self._MakePolicies(n=3)
    self._ExpectList(jobs)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('monitoring policies list --uri')

    self.AssertOutputEquals(
        """\
https://monitoring.googleapis.com/v3/projects/{project}/alertPolicies/policy-id0
https://monitoring.googleapis.com/v3/projects/{project}/alertPolicies/policy-id1
https://monitoring.googleapis.com/v3/projects/{project}/alertPolicies/policy-id2
        """.format(project=self.Project()), normalize_space=True)

  def testList_DifferentProject(self):
    project = 'other-project'
    policies = self._MakePolicies(project=project)
    self._ExpectList(policies, project=project)

    results = self.Run('monitoring policies list --project ' + project)

    self.assertEqual(results, policies)

  def testList_MultiplePages(self):
    policies = self._MakePolicies(n=10)
    self._ExpectList(policies[:5], page_size=5, next_page_token='token')
    self._ExpectList(policies[5:], page_size=5, page_token='token')

    results = self.Run('monitoring policies list --page-size 5')

    self.assertEqual(results, policies)

  def testList_SortBy(self):
    policies = self._MakePolicies()
    self._ExpectList(policies, order_by='-displayName,enabled')

    results = self.Run('monitoring policies list '
                       '--sort-by ~displayName,enabled')

    self.assertEqual(results, policies)


if __name__ == '__main__':
  test_case.main()
