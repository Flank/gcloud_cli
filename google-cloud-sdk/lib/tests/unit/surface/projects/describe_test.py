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

"""Tests for projects describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util

import httplib2


class ProjectsDescribeTest(base.ProjectsUnitTestBase):

  def testDescribeValidProject(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    test_project = util.GetTestActiveProject()
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId), test_project)
    response = self.RunProjects('describe', test_project.projectId)
    self.assertEqual(response, test_project)

  def testDescribeValidProjectOutput(self):
    test_project = util.GetTestActiveProject()
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId), test_project)
    self.RunProjects('describe', test_project.projectId)
    self.AssertOutputEquals("""\
lifecycleState: ACTIVE
name: My Project 5
projectId: feisty-catcher-644
projectNumber: '925276746377'
""", normalize_space=True)

  def testDescribeValidProjectBeta(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    test_project = util.GetTestActiveProject()
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId), test_project)
    response = self.RunProjectsBeta('describe', test_project.projectId)
    self.assertEqual(response, test_project)

  def testDescribeValidProjectBetaOutput(self):
    test_project = util.GetTestActiveProject()
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId=test_project.projectId), test_project)
    self.RunProjectsBeta('describe', test_project.projectId)
    self.AssertOutputEquals("""\
lifecycleState: ACTIVE
name: My Project 5
projectId: feisty-catcher-644
projectNumber: '925276746377'
""", normalize_space=True)

  def testDescribe403(self):
    url = ('http://cloudresourcemanager.googleapis.com/v1/projects/BAD_ID'
           '?prettyPrint=True&alt=json')
    error = http_error.MakeHttpError(
        code=403, message='The caller does not have permission', url=url)
    self.mock_client.projects.Get.Expect(
        self.messages.CloudresourcemanagerProjectsGetRequest(
            projectId='BAD_ID'),
        exception=error
    )
    with self.assertRaises(exceptions.HttpException):
      self.RunProjects('describe', 'BAD_ID')
    self.AssertErrContains(
        'does not have permission to access projects instance [BAD_ID]')


# DO NOT REMOVE THIS TEST.
# The projects API should always use gcloud's shared quota.
class QuotaHeaderTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                      parameterized.TestCase):
  """Make sure user project quota is disabled for this API."""

  def SetUp(self):
    properties.VALUES.core.project.Set('foo')
    mock_http_client = self.StartObjectPatch(http, 'Http')
    mock_http_client.return_value.request.return_value = \
      (httplib2.Response({
          'status': 200
      }), b'')
    self.request_mock = mock_http_client.return_value.request

  @parameterized.parameters(
      (None, 'beta', None),
      (None, '', None),
      (properties.VALUES.billing.LEGACY, 'beta', None),
      (properties.VALUES.billing.LEGACY, '', None),
      (properties.VALUES.billing.CURRENT_PROJECT, 'beta', b'foo'),
      (properties.VALUES.billing.CURRENT_PROJECT, '', b'foo'),
      ('bar', 'beta', b'bar'),
      ('bar', '', b'bar'),
  )
  def testQuotaHeader(self, prop_value, track, header_value):
    properties.VALUES.billing.quota_project.Set(prop_value)
    self.Run(track + ' projects describe asdf')
    header = self.request_mock.call_args[0][3].get(b'X-Goog-User-Project', None)
    self.assertEqual(header, header_value)


if __name__ == '__main__':
  test_case.main()
