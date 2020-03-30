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
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.trace import base


class ProjectSinksDeleteTest(base.TraceTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDeletePromptNo(self):
    self.WriteInput('n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.RunTrace('sinks delete my-sink')

  def testDeletePromptYes(self):
    self.WriteInput('Y')
    self.mock_client_v2.projects_traceSinks.Delete.Expect(
        self.msgs.CloudtraceProjectsTraceSinksDeleteRequest(
            name='projects/12345/traceSinks/my-sink'), self.msgs.Empty())
    self.RunTrace('sinks delete my-sink')
    self.AssertErrContains('Deleted')

  def testDeleteNoPerms(self):
    self.mock_client_v2.projects_traceSinks.Delete.Expect(
        self.msgs.CloudtraceProjectsTraceSinksDeleteRequest(
            name='projects/12345/traceSinks/my-sink'),
        exception=http_error.MakeHttpError(403))
    self.WriteInput('Y')
    self.RunWithoutPerms('sinks delete my-sink')

  def testDeleteNoProject(self):
    self.WriteInput('Y')
    self.RunWithoutProject('sinks delete my-sink')

  def testDeleteNoAuth(self):
    self.WriteInput('Y')
    self.RunWithoutAuth('sinks delete my-sink')


if __name__ == '__main__':
  test_case.main()
