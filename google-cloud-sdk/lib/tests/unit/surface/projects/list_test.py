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

"""Tests for projects list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import filter_rewrite
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util


class ProjectsListTest(base.ProjectsUnitTestBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def testListOneProject(self):
    test_project = util.GetTestActiveProject()
    self.mock_client.projects.List.Expect(
        self.messages.CloudresourcemanagerProjectsListRequest(
            pageSize=500,
            filter='lifecycleState:ACTIVE'),
        self.messages.ListProjectsResponse(projects=[test_project]))
    results_generator = self.RunProjects('list')
    results = [x for x in results_generator]
    self.assertEqual([test_project], results)

  def testListMultipleProjects(self):
    test_projects = util.GetTestActiveProjectsList()
    self.mock_client.projects.List.Expect(
        self.messages.CloudresourcemanagerProjectsListRequest(
            pageSize=500,
            filter='lifecycleState:ACTIVE'),
        self.messages.ListProjectsResponse(projects=test_projects))
    results_generator = self.RunProjects('list')
    results = [x for x in results_generator]
    self.assertEqual(test_projects, results)

  def testListMultipleProjectsBeta(self):
    test_projects = util.GetTestActiveProjectsList()
    self.mock_client.projects.List.Expect(
        self.messages.CloudresourcemanagerProjectsListRequest(
            pageSize=500,
            filter='lifecycleState:ACTIVE'),
        self.messages.ListProjectsResponse(projects=test_projects))
    results_generator = self.RunProjectsBeta('list')
    results = [x for x in results_generator]
    self.assertEqual(test_projects, results)

  def testListClientLimit(self):
    test_project = util.GetTestActiveProject()
    self.StartObjectPatch(
        filter_rewrite.ListRewriter,
        'Rewrite',
        return_value=('args.filter', ''))

    # Expect server-side default limit of 500, as limit is applied client-side
    self.mock_client.projects.List.Expect(
        self.messages.CloudresourcemanagerProjectsListRequest(
            pageSize=500,
            filter='lifecycleState:ACTIVE'),
        self.messages.ListProjectsResponse(projects=[test_project]))
    self.RunProjects('list', '--limit=1')

  def testListServerLimit(self):
    test_project = util.GetTestActiveProject()
    self.StartObjectPatch(
        filter_rewrite.ListRewriter,
        'Rewrite',
        return_value=(None, ''))

    # Expect server-side limit to be set to 1, per the provided flag
    self.mock_client.projects.List.Expect(
        self.messages.CloudresourcemanagerProjectsListRequest(
            pageSize=1,
            filter='lifecycleState:ACTIVE'),
        self.messages.ListProjectsResponse(projects=[test_project]))
    self.RunProjects('list', '--limit=1')


if __name__ == '__main__':
  test_case.main()
