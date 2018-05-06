# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for projects set-iam-policy."""

import copy

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util as test_util


class ProjectsAddIamPolicyBindingTest(base.ProjectsUnitTestBase):

  def testAddIamPolicyBinding(self):
    test_project = test_util.GetTestActiveProject()
    new_role = 'roles/editor'
    new_user = 'user:fox@google.com'
    start_policy = copy.deepcopy(test_util.GetTestIamPolicy())
    new_policy = copy.deepcopy(start_policy)
    new_policy.bindings[0].members.append(new_user)

    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId),
        start_policy)
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)),
        new_policy)

    response = self.RunProjectsBeta(
        'add-iam-policy-binding',
        test_project.projectId,
        '--role={0}'.format(new_role),
        '--member={0}'.format(new_user))
    self.assertEqual(response, new_policy)


class ProjectsAddIamPolicyBindingCompletionTest(base.ProjectsUnitTestBase):

  def testRoleCompletion(self):
    test_project = test_util.GetTestActiveProject()

    iam_client = mock.Client(core_apis.GetClientClass('iam', 'v1'))
    iam_client.Mock()
    self.addCleanup(iam_client.Unmock)
    iam_msgs = core_apis.GetMessagesModule('iam', 'v1')

    returned_roles = [
        iam_msgs.Role(
            description='Read access to all resources.',
            name='roles/viewer',
            title='Viewer',
        ),
        iam_msgs.Role(
            description='Read-only access to GCE networking resources.',
            name='roles/compute.networkViewer',
            title='Compute Network Viewer',
        ),
    ]
    iam_client.roles.QueryGrantableRoles.Expect(
        request=iam_msgs.QueryGrantableRolesRequest(
            fullResourceName=(
                '//cloudresourcemanager.googleapis.com/projects/{0}'.format(
                    test_project.projectId)),
            pageSize=100),
        response=iam_msgs.QueryGrantableRolesResponse(roles=returned_roles),)

    self.RunCompletion(
        'beta projects add-iam-policy-binding {0} --role '.format(
            test_project.projectId),
        ['roles/viewer', 'roles/compute.networkViewer'])


if __name__ == '__main__':
  test_case.main()
