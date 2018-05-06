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

"""Tests of the 'metrics' subcommand."""

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class MetricsDeleteTest(base.LoggingTestBase):

  def testDeletePromptNo(self):
    self.WriteInput('n')
    with self.assertRaisesRegex(
        console_io.OperationCancelledError, 'Aborted by user.'):
      self.RunLogging('metrics delete my-metric')
    self.AssertErrNotContains('Deleted [my-metric].')

  def testDeletePromptYes(self):
    self.WriteInput('Y')
    self.mock_client_v2.projects_metrics.Delete.Expect(
        util.GetMessages().LoggingProjectsMetricsDeleteRequest(
            metricName='projects/my-project/metrics/my-metric'),
        util.GetMessages().Empty())
    self.RunLogging('metrics delete my-metric')
    self.AssertErrContains('Deleted [my-metric]')

  def testDeleteNoPerms(self):
    self.mock_client_v2.projects_metrics.Delete.Expect(
        util.GetMessages().LoggingProjectsMetricsDeleteRequest(
            metricName='projects/my-project/metrics/my-metric'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('metrics delete my-metric')

  def testDeleteNoProject(self):
    self.RunWithoutProject('metrics delete my-metric')

  def testDeleteNoAuth(self):
    self.RunWithoutAuth('metrics delete my-metric')


if __name__ == '__main__':
  test_case.main()
