# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import test_case
from tests.lib.surface.projects import base


class ProjectIntegrationTest(base.ProjectsTestBase, e2e_base.WithServiceAuth):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.retryer = retry.Retryer(max_wait_ms=60000)

  def getIntegrationTestingProject(self):
    return self.messages.Project(
        createTime='2014-09-30T14:51:18.935Z',
        lifecycleState=self.messages.Project.LifecycleStateValueValuesEnum.
        ACTIVE,
        projectId='cloud-sdk-integration-testing',
        projectNumber=462803083913,
        name='Cloud SDK Integration Testing')

  def compareProjects(self, expected, project):
    return (expected.projectId == project.projectId and
            expected.name == project.name and
            expected.projectNumber == project.projectNumber)

  def testListProjects(self):
    result = self.RunProjects('list')
    # Result is a generator. Get everything into a list so we can iterate over
    # multiple times.
    projects = list(result)
    expected = self.getIntegrationTestingProject()
    matching_projects = [p for p in projects
                         if self.compareProjects(expected, p)]
    self.assertEqual(1, len(matching_projects), 'projects list command should '
                     'contain exactly one cloud-sdk-integration-testing '
                     'project. We received {0}'.format(projects))

  def testListProjectsFilterMatch(self):
    filter_expr = ('(lifecycleState=ACTIVE AND '
                   '(projectId=cloud-sdk-integration-testing))')
    result = self.RunProjects('list', '--filter', filter_expr)
    projects = list(result)
    self.assertEqual(1, len(projects), 'projects list command should '
                     'contain exactly one cloud-sdk-integration-testing '
                     'project. We received {0}'.format(projects))

  def testListProjectsFilterNoMatch(self):
    filter_expr = ('projectId=cloud-sdk-integration-testing AND '
                   'projectNumber=1234')
    result = self.RunProjects('list', '--filter', filter_expr)
    projects = list(result)
    expected = self.getIntegrationTestingProject()
    matching_projects = [p for p in projects
                         if self.compareProjects(expected, p)]
    self.assertEqual(0, len(matching_projects))

  def testDescribeProject(self):
    result = self.RunProjects('describe', 'cloud-sdk-integration-testing')
    self.assertTrue(self.compareProjects(self.getIntegrationTestingProject(),
                                         result))

  def testGetIamPolicy(self):
    policy = self.RunProjects(
        'get-iam-policy',
        'cloud-sdk-integration-testing')
    self.assertIsInstance(policy, self.messages.Policy)

if __name__ == '__main__':
  test_case.main()
