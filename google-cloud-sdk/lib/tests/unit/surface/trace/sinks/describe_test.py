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


class ProjectSinksGetTest(base.TraceTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testGet(self):
    test_sink = self.msgs.TraceSink(
        name='projects/12345/traceSinks/my-sink',
        outputConfig={'destination': 'dest'},
        writerIdentity='serviceaccount@gserviceaccount.com')
    self.mock_client_v2.projects_traceSinks.Get.Expect(
        self.msgs.CloudtraceProjectsTraceSinksGetRequest(
            name='projects/12345/traceSinks/my-sink'), test_sink)
    self.RunTrace('sinks describe my-sink')
    self.AssertOutputContains('my-sink')
    self.AssertOutputContains(test_sink.outputConfig.destination)
    self.AssertOutputContains(test_sink.writerIdentity)

  def testGetNoPerms(self):
    self.mock_client_v2.projects_traceSinks.Get.Expect(
        self.msgs.CloudtraceProjectsTraceSinksGetRequest(
            name='projects/12345/traceSinks/my-sink'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('sinks describe my-sink')

  def testGetNoProject(self):
    self.RunWithoutProject('sinks describe my-sink')

  def testGetNoAuth(self):
    self.RunWithoutAuth('sinks describe my-sink')


if __name__ == '__main__':
  test_case.main()
