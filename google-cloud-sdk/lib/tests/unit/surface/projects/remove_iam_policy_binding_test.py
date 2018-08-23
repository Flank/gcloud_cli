# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util as test_util


class ProjectsRemoveIamPolicyBindingTest(base.ProjectsUnitTestBase):

  def testAddIamPolicyBinding(self):
    test_project = test_util.GetTestActiveProject()
    start_policy = copy.deepcopy(test_util.GetTestIamPolicy())
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:tester@gmail.com'
    remove_role = 'roles/owner'
    # In the test policy the first binding is for editors, second for owners.
    new_policy.bindings[1].members.remove(remove_user)

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
        'remove-iam-policy-binding',
        test_project.projectId,
        '--role={0}'.format(remove_role),
        '--member={0}'.format(remove_user))
    self.assertEqual(response, new_policy)


if __name__ == '__main__':
  test_case.main()
