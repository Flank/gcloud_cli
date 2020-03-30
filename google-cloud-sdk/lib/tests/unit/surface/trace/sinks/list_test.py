# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.trace import base


class SinksListTestBase(base.TraceTestBase):

  def SetUp(self):
    self._sinks = [
        self.msgs.TraceSink(
            name='projects/12345/traceSinks/first-sink',
            outputConfig={'destination': 'first-destination'},
            writerIdentity='service-first@gserviceaccount.com'),
        self.msgs.TraceSink(
            name='projects/12345/traceSinks/second-sink',
            outputConfig={'destination': 'second-destination'},
            writerIdentity='service-second@gserviceaccount.com')
    ]
    self._display_name = ['first-sink', 'second-sink']

  def _setProjectSinksListResponse(self, sinks):
    self.mock_client_v2.projects_traceSinks.List.Expect(
        self.msgs.CloudtraceProjectsTraceSinksListRequest(
            parent='projects/my-project'),
        self.msgs.ListTraceSinksResponse(sinks=sinks))


class ProjectSinksListTest(SinksListTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testList(self):
    self._setProjectSinksListResponse(self._sinks)
    self.RunTrace('sinks list')
    for name in self._display_name:
      self.AssertOutputContains(name)
    for sink in self._sinks:
      self.AssertOutputContains(sink.outputConfig.destination)
      self.AssertOutputContains(sink.writerIdentity)

  def testListNoPerms(self):
    self.mock_client_v2.projects_traceSinks.List.Expect(
        self.msgs.CloudtraceProjectsTraceSinksListRequest(
            parent='projects/my-project'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('sinks list')

  def testListNoProject(self):
    self.RunWithoutProject('sinks list')

  def testListNoAuth(self):
    self.RunWithoutAuth('sinks list')


if __name__ == '__main__':
  test_case.main()
