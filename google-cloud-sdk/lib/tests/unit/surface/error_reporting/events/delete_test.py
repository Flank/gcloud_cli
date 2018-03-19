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

"""Tests of the 'delete' subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.error_reporting import base

cer_api = core_apis.GetMessagesModule('clouderrorreporting', 'v1beta1')


class DeleteTest(base.ErrorReportingTestBase):

  COMMAND = 'events delete'

  def testDeletePromptNo(self):
    self.WriteInput('n')
    expected = r'Aborted by user.'
    with self.assertRaisesRegexp(console_io.OperationCancelledError, expected):
      self.RunCmd(self.COMMAND)

  def testDeletePromptYes(self):
    properties.VALUES.core.project.Set(self.FAKE_PROJECT)

    self.WriteInput('Y')
    self.mock_client.projects.DeleteEvents.Expect(
        cer_api.ClouderrorreportingProjectsDeleteEventsRequest(
            projectName='projects/' + self.FAKE_PROJECT),
        cer_api.DeleteEventsResponse())
    self.RunCmd(self.COMMAND)
    self.AssertErrContains('deleted')

  def testDeleteEventsNonExistingProject(self):
    base_url = 'http://clouderrorreporting.googleapis.com/v1beta1'
    url = base_url + '/project/{0}/events'.format(self.FAKE_PROJECT)
    self.mock_client.projects.DeleteEvents.Expect(
        cer_api.ClouderrorreportingProjectsDeleteEventsRequest(
            projectName='projects/' + self.FAKE_PROJECT),
        exception=http_error.MakeHttpError(404, url=url))
    with self.AssertRaisesHttpExceptionMatches(
        'Project [{0}] not found: Resource not found.'.format(
            self.FAKE_PROJECT)):
      self.RunCmd(self.COMMAND)

  def testDeleteNoProject(self):
    self.RunWithoutProject(self.COMMAND)

  def testDeleteNoAuth(self):
    self.RunWithoutAuth(self.COMMAND)

if __name__ == '__main__':
  test_case.main()
