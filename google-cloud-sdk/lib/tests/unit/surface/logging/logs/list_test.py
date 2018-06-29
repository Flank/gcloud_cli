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

"""Tests of the 'logs' subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.logging import util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class LogsListTest(base.LoggingTestBase):

  def SetUp(self):
    self.log_names = [
        'projects/my-project/logs/first',
        'projects/my-project/logs/second']

  def _setListResponse(self, log_names):
    self.mock_client_v2.projects_logs.List.Expect(
        util.GetMessages().LoggingProjectsLogsListRequest(
            parent='projects/my-project'),
        util.GetMessages().ListLogsResponse(logNames=log_names))

  def testListLimit(self):
    self._setListResponse(self.log_names)
    self.RunLogging('logs list --limit 1')
    self.AssertOutputContains('first')
    self.AssertOutputNotContains('second')

  def testList(self):
    self._setListResponse(self.log_names)
    self.RunLogging('logs list')
    self.AssertOutputContains(self.log_names[0])
    self.AssertOutputContains(self.log_names[1])

  def testListNoPerms(self):
    self.mock_client_v2.projects_logs.List.Expect(
        util.GetMessages().LoggingProjectsLogsListRequest(
            parent='projects/my-project'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('logs list')

  def testListNoProject(self):
    self.RunWithoutProject('logs list')

  def testListNoAuth(self):
    self.RunWithoutAuth('logs list')


if __name__ == '__main__':
  test_case.main()
