# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Unit tests for the projects api."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.projects import util as command_lib_util
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.projects import util

import mock


class ProjectsApiTest(sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudresourcemanager', 'v1')
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1'),
        real_client=core_apis.GetClientInstance(
            'cloudresourcemanager', 'v1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def HttpError(self):
    url = 'url.../v1beta1/projects/BAD_ID:method?prettyPrint=True&alt=json'
    return http_error.MakeHttpError(
        code=403, message='The caller does not have permission', url=url)

  def testList(self):
    test_project = util.GetTestActiveProject()
    self.mock_client.projects.List.Expect(
        self.messages.CloudresourcemanagerProjectsListRequest(
            pageSize=500,
            filter='lifecycleState:ACTIVE'),
        self.messages.ListProjectsResponse(projects=[test_project]))
    results_generator = projects_api.List()
    results = [x for x in results_generator]
    self.assertEqual([test_project], results)

  def testListFilter(self):
    test_project = util.GetTestActiveProject()
    self.mock_client.projects.List.Expect(
        self.messages.CloudresourcemanagerProjectsListRequest(
            pageSize=500,
            filter='lifecycleState:ACTIVE AND (id:foo)'),
        self.messages.ListProjectsResponse(projects=[test_project]))
    results_generator = projects_api.List(filter='id:foo')
    results = [x for x in results_generator]
    self.assertEqual([test_project], results)

  def testListFilterWithLifecycleState(self):
    test_project = util.GetTestActiveProject()
    self.mock_client.projects.List.Expect(
        self.messages.CloudresourcemanagerProjectsListRequest(
            pageSize=500,
            filter='lifecycleState:DELETE_REQUESTED'),
        self.messages.ListProjectsResponse(projects=[test_project]))
    results_generator = projects_api.List(
        filter='lifecycleState:DELETE_REQUESTED')
    results = [x for x in results_generator]
    self.assertEqual([test_project], results)

  def testGet(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        test_project)
    response = projects_api.Get(test_project_ref)
    self.assertEqual(response, test_project)

  def testGetHttpError(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        exception=self.HttpError())
    with self.assertRaises(exceptions.HttpError):
      projects_api.Get(test_project_ref)

  def testCreate(self):
    test_project = util.GetTestActiveProjectWithSameNameAndId()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    op = self.messages.Operation(
        done=True, response=operations.ToOperationResponse(test_project))
    test_project = util.GetTestActiveProjectWithSameNameAndId()
    self.mock_client.projects.Create.Expect(
        self.messages.Project(
            projectId=test_project.projectId,
            name=test_project.name,
            labels=None),
        op)
    response = projects_api.Create(test_project_ref, test_project.name)
    self.assertEqual(response, op)

  def testDelete(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    self.mock_client.projects.Delete.Expect(
        self.messages.CloudresourcemanagerProjectsDeleteRequest(
            projectId=test_project.projectId),
        self.messages.Empty())
    response = projects_api.Delete(test_project_ref)
    self.assertEqual(response.projectId, test_project.projectId)

  def testDeleteHttpError(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    self.mock_client.projects.Delete.Expect(
        self.messages.CloudresourcemanagerProjectsDeleteRequest(
            projectId=test_project.projectId),
        exception=self.HttpError())
    with self.assertRaises(exceptions.HttpError):
      projects_api.Delete(test_project_ref)

  def testUndelete(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    self.mock_client.projects.Undelete.Expect(
        self.messages.CloudresourcemanagerProjectsUndeleteRequest(
            projectId=test_project.projectId),
        self.messages.Empty())
    response = projects_api.Undelete(test_project_ref)
    self.assertEqual(response.projectId, test_project.projectId)

  def testUndeleteHttpError(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    self.mock_client.projects.Undelete.Expect(
        self.messages.CloudresourcemanagerProjectsUndeleteRequest(
            projectId=test_project.projectId),
        exception=self.HttpError())
    with self.assertRaises(exceptions.HttpError):
      projects_api.Undelete(test_project_ref)

  def testUpdate(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    updated_test_project = util.GetTestActiveProject()
    updated_test_project.name = 'Test Project, New and Improved'
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        test_project)
    self.mock_client.projects.Update.Expect(updated_test_project,
                                            updated_test_project)
    response = projects_api.Update(
        test_project_ref, name=updated_test_project.name)
    self.assertEqual(response, updated_test_project)

  def testUpdateHttpError(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId),
        exception=self.HttpError())
    with self.assertRaises(exceptions.HttpError):
      projects_api.Update(test_project_ref, name='new name')

  def testTestIamPermissions(self):
    requested_permissions = ['storage.buckets.create', 'storage.buckets.delete']
    expected_permissions = ['storage.buckets.create']
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    self.mock_client.projects.TestIamPermissions.Expect(
        self.messages.CloudresourcemanagerProjectsTestIamPermissionsRequest(
            resource=test_project_ref.Name(),
            testIamPermissionsRequest=self.messages.TestIamPermissionsRequest(
                permissions=requested_permissions)),
        self.messages.TestIamPermissionsResponse(
            permissions=expected_permissions))
    response = projects_api.TestIamPermissions(test_project_ref,
                                               requested_permissions)
    self.assertEqual(response.permissions, expected_permissions)


class IamPolicyBindings(test_case.TestCase):

  def SetUp(self):
    self.mock_get_iam_policy = self.StartObjectPatch(
        projects_api,
        'GetIamPolicy'
    )
    self.mock_set_iam_policy = self.StartObjectPatch(
        projects_api,
        'SetIamPolicy'
    )
    self.mock_add_binding = self.StartObjectPatch(
        iam_util,
        'AddBindingToIamPolicy'
    )

  def testAddIamPolicyBindings(self):
    test_project = util.GetTestActiveProject()
    test_project_ref = command_lib_util.ParseProject(test_project.projectId)
    policy = self.mock_get_iam_policy.return_value

    projects_api.AddIamPolicyBindings(
        test_project_ref,
        [('member_1', 'role_1'), ('member_2', 'role_2')])

    self.mock_get_iam_policy.assert_called_once_with(
        test_project_ref,
        projects_api.DEFAULT_API_VERSION)

    self.mock_set_iam_policy.assert_called_once_with(
        test_project_ref,
        policy,
        api_version=projects_api.DEFAULT_API_VERSION)

    messages = core_apis.GetMessagesModule('cloudresourcemanager', 'v1')
    expected_binding_calls = [
        mock.call(messages.Binding, policy, 'member_1', 'role_1'),
        mock.call(messages.Binding, policy, 'member_2', 'role_2'),
    ]
    self.mock_add_binding.assert_has_calls(expected_binding_calls)


if __name__ == '__main__':
  test_case.main()
