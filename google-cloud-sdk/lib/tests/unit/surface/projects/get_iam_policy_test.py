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

"""Tests for projects get-iam-policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util as test_util


class ProjectsGetIamPolicyTestGA(base.ProjectsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testGetIamPolicyProject(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            getIamPolicyRequest=self.messages.GetIamPolicyRequest(
                options=self.messages.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
            resource=test_project.projectId),
        copy.deepcopy(test_util.GetTestIamPolicy()))
    response = self.RunProjects('get-iam-policy', test_project.projectId)
    self.assertEqual(response, test_util.GetTestIamPolicy())

  def testGetIamPolicyProjectOutput(self):
    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            getIamPolicyRequest=self.messages.GetIamPolicyRequest(
                options=self.messages.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
            resource=test_project.projectId),
        copy.deepcopy(test_util.GetTestIamPolicy()))
    self.RunProjects('get-iam-policy', test_project.projectId)
    self.AssertOutputEquals("""\
auditConfigs:
- auditLogConfigs:
  - logType: ADMIN_READ
  service: allServices
bindings:
- members:
  - serviceAccount:123hash@developer.gserviceaccount.com
  role: roles/editor
- members:
  - user:tester@gmail.com
  - user:slick@gmail.com
  role: roles/owner
etag: PDwgVW5pcXVlIHZlcnNpb25pbmcgZXRhZyBieXRlZmllbGQgPj4=
""")

  def testListCommandFilter(self):
    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            getIamPolicyRequest=self.messages.GetIamPolicyRequest(
                options=self.messages.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
            resource=test_project.projectId),
        copy.deepcopy(test_util.GetTestIamPolicy()))
    command = [
        'get-iam-policy',
        test_project.projectId,
        '--flatten=bindings[].members',
        '--filter=bindings.role:roles/owner',
        '--format=table[no-heading](bindings.members:sort=1)',
    ]
    self.RunProjects(*command)
    self.AssertOutputEquals('user:slick@gmail.com\nuser:tester@gmail.com\n')


class ProjectsGetIamPolicyTestBeta(ProjectsGetIamPolicyTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ProjectsGetIamPolicyTestAlpha(ProjectsGetIamPolicyTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
