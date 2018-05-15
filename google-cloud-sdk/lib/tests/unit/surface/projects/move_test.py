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
"""Tests for projects move."""

from __future__ import absolute_import
from __future__ import unicode_literals
import collections

from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.resource_manager import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.projects import base


Resources = collections.namedtuple('Resources', [
    'TEST_ORGANIZATION_RESOURCE_ID', 'TEST_FOLDER_RESOURCE_ID',
    'TEST_PROJECT_WITHOUT_PARENT', 'TEST_PROJECT_WITH_ORGANIZATION',
    'TEST_PROJECT_WITH_FOLDER'
])


def MakeTestResources():
  messages = projects_util.GetMessages()

  def MakeTestProject(parent=None):
    return messages.Project(
        lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
        projectId='feisty-catcher-644',
        projectNumber=925276746377,
        name='My Project 5',
        parent=parent)

  org_resource_id = messages.ResourceId(id='57935028', type='organization')
  folder_resource_id = messages.ResourceId(id='12345', type='folder')

  return Resources(
      org_resource_id, folder_resource_id, MakeTestProject(),
      MakeTestProject(parent=org_resource_id),
      MakeTestProject(parent=folder_resource_id))


class ProjectsMoveTest(base.ProjectsUnitTestBase):

  def testMoveProjectToOrganization(self):
    resources = MakeTestResources()
    test_project = resources.TEST_PROJECT_WITHOUT_PARENT
    test_parent = resources.TEST_ORGANIZATION_RESOURCE_ID
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        test_project)
    self.mock_client.projects.Update.Expect(
        resources.TEST_PROJECT_WITH_ORGANIZATION,
        resources.TEST_PROJECT_WITH_ORGANIZATION)
    response = self.RunProjectsBeta('move', test_project.projectId,
                                    '--organization', test_parent.id)
    self.assertEqual(response.parent, test_parent)

  def testMoveProjectToFolder(self):
    resources = MakeTestResources()
    test_project = resources.TEST_PROJECT_WITHOUT_PARENT
    test_parent = resources.TEST_FOLDER_RESOURCE_ID
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        test_project)
    self.mock_client.projects.Update.Expect(resources.TEST_PROJECT_WITH_FOLDER,
                                            resources.TEST_PROJECT_WITH_FOLDER)
    response = self.RunProjectsBeta('move', test_project.projectId, '--folder',
                                    test_parent.id)
    self.assertEqual(response.parent, test_parent)

  def testMoveProjectWithBothFolderAndOrganizationSpecified(self):
    resources = MakeTestResources()
    test_project = resources.TEST_PROJECT_WITHOUT_PARENT
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --folder, --organization'):
      self.RunProjectsAlpha('move', test_project.projectId, '--folder', '12345',
                            '--organization', '2048')

  def testMoveProjectWithoutDestination(self):
    resources = MakeTestResources()
    test_project = resources.TEST_PROJECT_WITHOUT_PARENT
    with self.AssertRaisesExceptionMatches(
        exceptions.ArgumentError,
        'Neither --folder nor --organization provided, exactly one required'):
      self.RunProjectsAlpha('move', test_project.projectId)


if __name__ == '__main__':
  test_case.main()
