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

"""Tests of the 'sinks' subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class SinksListTestBase(base.LoggingTestBase):

  def SetUp(self):
    self._sinks = [
        self.msgs.LogSink(
            name='first-sink',
            destination='first-destination'),
        self.msgs.LogSink(
            name='second-sink',
            destination='second-destination')]

  def _setProjectSinksListResponse(self, sinks):
    self.mock_client_v2.projects_sinks.List.Expect(
        self.msgs.LoggingProjectsSinksListRequest(parent='projects/my-project'),
        self.msgs.ListSinksResponse(sinks=sinks))


class ProjectSinksListTest(SinksListTestBase):

  def testListLimit(self):
    self._setProjectSinksListResponse(self._sinks)
    self.RunLogging('sinks list --limit 1')
    self.AssertOutputContains(self._sinks[0].name)
    self.AssertOutputNotContains(self._sinks[1].name)

  def testList(self):
    self._setProjectSinksListResponse(self._sinks)
    self.RunLogging('sinks list')
    for sink in self._sinks:
      self.AssertOutputContains(sink.name)
      self.AssertOutputContains(sink.destination)

  def testListNoPerms(self):
    self.mock_client_v2.projects_sinks.List.Expect(
        self.msgs.LoggingProjectsSinksListRequest(parent='projects/my-project'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('sinks list')

  def testListNoProject(self):
    self.RunWithoutProject('sinks list')

  def testListNoAuth(self):
    self.RunWithoutAuth('sinks list')


if __name__ == '__main__':
  test_case.main()
