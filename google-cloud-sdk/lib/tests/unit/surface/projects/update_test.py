# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests for projects update."""

from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util


class ProjectsUpdateTestAlpha(base.ProjectsUnitTestBase):

  def testUpdateValidProjectWithNewName(self):
    test_project = util.GetTestActiveProject()
    updated_test_project = util.GetTestActiveProject()
    updated_test_project.name = 'Test Project, New and Improved'
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        test_project)
    self.mock_client.projects.Update.Expect(updated_test_project,
                                            updated_test_project)
    response = self.RunProjectsAlpha('update', test_project.projectId, '--name',
                                     updated_test_project.name)
    self.assertEqual(response, updated_test_project)

  def testUpdateMissingNameOrLabels(self):
    test_project = util.GetTestActiveProject()
    with self.AssertRaisesArgumentErrorMatches(
        'argument (--name --update-labels --clear-labels | --remove-labels): '
        'Must be specified.'):
      self.RunProjectsAlpha('update', test_project.projectId)

  def testUpdateValidProjectWithLabelsAndRemoveLabels(self):
    labels = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
    update_labels = {'key2': 'update2', 'key4': 'value4'}
    edited_labels = {'key2': 'update2', 'key3': 'value3', 'key4': 'value4'}
    test_project = util.GetTestActiveProjectWithLabels(labels)
    updated_test_project = util.GetTestActiveProjectWithLabels(edited_labels)
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId,
        ),
        test_project)
    self.mock_client.projects.Update.Expect(updated_test_project,
                                            updated_test_project)
    response = self.RunProjectsAlpha(
        'update', test_project.projectId,
        '--update-labels', util.GetLabelsFlagValue(update_labels),
        '--remove-labels', 'key1,key0')
    self.assertEqual(response, updated_test_project)

  def testUpdateValidProjectClearLabels(self):
    labels = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
    edited_labels = {}
    test_project = util.GetTestActiveProjectWithLabels(labels)
    updated_test_project = util.GetTestActiveProjectWithLabels(edited_labels)
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId,
        ),
        test_project)
    self.mock_client.projects.Update.Expect(updated_test_project,
                                            updated_test_project)
    response = self.RunProjectsAlpha(
        'update', test_project.projectId, '--clear-labels')
    self.assertEqual(response, updated_test_project)


class ProjectsUpdateTest(base.ProjectsUnitTestBase):

  def testUpdateValidProjectWithNewName(self):
    test_project = util.GetTestActiveProject()
    updated_test_project = util.GetTestActiveProject()
    updated_test_project.name = 'Test Project, New and Improved'
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        test_project)
    self.mock_client.projects.Update.Expect(updated_test_project,
                                            updated_test_project)
    response = self.RunProjectsBeta('update', test_project.projectId, '--name',
                                    updated_test_project.name)
    self.assertEqual(response, updated_test_project)

  def testUpdateValidProjectWithNewNameExistingLabels(self):
    test_project = util.GetTestActiveProjectWithLabels({'foo': 'bar'})
    updated_test_project = util.GetTestActiveProjectWithLabels({'foo': 'bar'})
    updated_test_project.name = 'Test Project, New and Improved'
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        test_project)
    self.mock_client.projects.Update.Expect(updated_test_project,
                                            updated_test_project)
    response = self.RunProjectsBeta('update', test_project.projectId, '--name',
                                    updated_test_project.name)
    self.assertEqual(response, updated_test_project)

  def testUpdateMissingName(self):
    test_project = util.GetTestActiveProject()
    with self.AssertRaisesArgumentErrorMatches(
        'argument --name: Must be specified.'):
      self.RunProjectsBeta('update', test_project.projectId)


if __name__ == '__main__':
  test_case.main()
