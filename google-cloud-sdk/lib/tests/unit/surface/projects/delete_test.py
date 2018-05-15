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
"""Tests for projects delete."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util


class ProjectsDeleteTest(base.ProjectsUnitTestBase):

  def testDeleteValidProject(self):
    test_project_id = util.GetTestActiveProject().projectId
    self.mock_client.projects.Delete.Expect(
        self.messages.CloudresourcemanagerProjectsDeleteRequest(
            projectId=test_project_id),
        self.messages.Empty())
    self.WriteInput('y\n')
    result = self.RunProjectsBeta('delete', '--format=disable', test_project_id)
    self.assertEqual([{
        'projectId': 'feisty-catcher-644'
    }], resource_projector.MakeSerializable(list(result)))
    self.AssertOutputEquals('')
    self.AssertErrContains('Your project will be deleted')
    self.AssertErrContains('Do you want to continue (Y/n)?')
    self.AssertErrContains(
        'You can undo this operation for a limited period by running:\n'
        '  $ gcloud projects undelete {0}'.format(test_project_id))

  def testNotDeleteValidProject(self):
    test_project_id = util.GetTestActiveProject().projectId
    self.WriteInput('n\n')
    result = self.RunProjectsBeta('delete', test_project_id)
    self.assertEqual([], list(result))
    self.AssertOutputEquals('')
    self.AssertErrContains('Your project will be deleted')
    self.AssertErrContains('Do you want to continue (Y/n)?')
    self.AssertErrNotContains(
        'You can undo this operation for a limited period by running:\n'
        '  $ gcloud projects undelete {0}'.format(test_project_id))

  def testDeleteValidProjectWithFormat(self):
    test_project_id = util.GetTestActiveProject().projectId
    self.mock_client.projects.Delete.Expect(
        self.messages.CloudresourcemanagerProjectsDeleteRequest(
            projectId=test_project_id),
        self.messages.Empty())
    self.WriteInput('y\n')
    self.RunProjectsBeta('delete', '--format=default', test_project_id)
    self.AssertOutputContains('projectId: {0}'.format(test_project_id))
    self.AssertErrContains('Your project will be deleted')
    self.AssertErrContains('Do you want to continue (Y/n)?')

  def testDeleteValidProjectWithFormatDisabled(self):
    test_project_id = util.GetTestActiveProject().projectId
    self.mock_client.projects.Delete.Expect(
        self.messages.CloudresourcemanagerProjectsDeleteRequest(
            projectId=test_project_id),
        self.messages.Empty())
    self.WriteInput('y\n')
    result = self.RunProjectsBeta('delete', '--format=disable', test_project_id)
    self.assertEqual([{
        'projectId': 'feisty-catcher-644'
    }], resource_projector.MakeSerializable(list(result)))
    self.AssertOutputEquals('')
    self.AssertErrContains('Your project will be deleted')
    self.AssertErrContains('Do you want to continue (Y/n)?')

  def testDeleteFails400(self):
    exception = http_error.MakeDetailedHttpError(
        url='https://cloudresourcemanager.googleapis.com/v1/projects/p123',
        reason='FAILED_PRECONDITION',
        message='Precondition check failed.',
        details=[{
            '@type':
                'type.googleapis.com/google.rpc.PreconditionFailure',
            'violations': [{
                'type':
                    'LIEN',
                'subject':
                    'liens/p123-l4c552089-e37c-4db7-bfee-cfaf268f1038',
                'description': ('A lien to prevent deletion was placed on the'
                                ' project by [buck]. Remove the lien to allow'
                                ' deletion.')
            }]
        }])
    test_project_id = util.GetTestActiveProject().projectId
    self.mock_client.projects.Delete.Expect(
        self.messages.CloudresourcemanagerProjectsDeleteRequest(
            projectId=test_project_id),
        exception=exception)
    self.WriteInput('y\n')
    with self.assertRaises(api_exceptions.HttpException):
      self.RunProjects('delete', test_project_id)
    self.AssertErrEquals("""\
Your project will be deleted.

Do you want to continue (Y/n)?
ERROR: (gcloud.projects.delete) FAILED_PRECONDITION: Precondition check failed.
- '@type': type.googleapis.com/google.rpc.PreconditionFailure
  violations:
  - description: A lien to prevent deletion was placed on the project by [buck]. Remove
      the lien to allow deletion.
    subject: liens/p123-l4c552089-e37c-4db7-bfee-cfaf268f1038
    type: LIEN
""",
                         normalize_space=True)


if __name__ == '__main__':
  test_case.main()
