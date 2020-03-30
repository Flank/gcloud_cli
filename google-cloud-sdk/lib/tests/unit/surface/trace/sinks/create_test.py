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


class SinksCreateTest(base.TraceTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateSuccess(self):
    new_sink = self.msgs.TraceSink(
        name='projects/12345/traceSinks/my-sink',
        outputConfig={'destination': 'dest'})
    created_new_sink = self.msgs.TraceSink(
        name='projects/12345/traceSinks/my-sink',
        outputConfig={'destination': 'dest'},
        writerIdentity='serviceaccount@gserviceaccount.com')
    self.mock_client_v2.projects_traceSinks.Create.Expect(
        self.msgs.CloudtraceProjectsTraceSinksCreateRequest(
            parent='projects/my-project', traceSink=new_sink), created_new_sink)
    self.RunTrace('sinks create my-sink dest')

  def testListNoPerms(self):
    new_sink = self.msgs.TraceSink(
        name='projects/12345/traceSinks/my-sink',
        outputConfig={'destination': 'dest'})
    self.mock_client_v2.projects_traceSinks.Create.Expect(
        self.msgs.CloudtraceProjectsTraceSinksCreateRequest(
            parent='projects/my-project', traceSink=new_sink),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('sinks create my-sink dest')

  def testListNoProject(self):
    self.RunWithoutProject('sinks create my-sink dest')

  def testListNoAuth(self):
    self.RunWithoutAuth('sinks create my-sink dest')


if __name__ == '__main__':
  test_case.main()
