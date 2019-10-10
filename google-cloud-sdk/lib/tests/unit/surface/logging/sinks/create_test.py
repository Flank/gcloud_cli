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

"""Tests of the 'sinks' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class SinksCreateTest(base.LoggingTestBase):

  def testCreateSuccess(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', filter='foo', includeChildren=False)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project', logSink=new_sink,
            uniqueWriterIdentity=True),
        new_sink)
    self.RunLogging('sinks create my-sink dest --log-filter=foo')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Created [https://logging.googleapis.com/v2/projects/my-project/sinks/my-sink].
More information about sinks can be found at https://cloud.google.com/logging/docs/export/configure_export
""")

  def testCreateProjectSinkWithChildrenSuccess(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', filter='foo', includeChildren=True)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project', logSink=new_sink,
            uniqueWriterIdentity=True),
        new_sink)
    self.RunLogging(
        'sinks create my-sink dest --log-filter=foo --include-children')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
WARNING: include-children only has an effect for sinks at the folder or organization level
Created [https://logging.googleapis.com/v2/projects/my-project/sinks/my-sink].
More information about sinks can be found at https://cloud.google.com/logging/docs/export/configure_export
""")

  def testCreateWithChildrenSuccess(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', filter='foo', includeChildren=True)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='organizations/my-org', logSink=new_sink,
            uniqueWriterIdentity=True),
        new_sink)
    self.RunLogging(
        'sinks create my-sink dest --organization=my-org --log-filter=foo '
        '--include-children')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Created [https://logging.googleapis.com/v2/organizations/my-org/sinks/my-sink].
More information about sinks can be found at https://cloud.google.com/logging/docs/export/configure_export
""")

  def testCreateSuccessEmptyFilter(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', includeChildren=False)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project', logSink=new_sink,
            uniqueWriterIdentity=True),
        new_sink)
    self.WriteInput('Y')
    self.RunLogging('sinks create my-sink dest')
    self.AssertOutputEquals('')
    self.AssertErrContains('Sink with empty filter matches all entries.')
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrContains(
        'Created [https://logging.googleapis.com/v2/projects/my-project/'
        'sinks/my-sink].\n'
        'More information about sinks can be found at '
        'https://cloud.google.com/logging/docs/export/configure_export')

  def testListNoPerms(self):
    new_sink = self.msgs.LogSink(
        name='my-sink', destination='dest', includeChildren=False)
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project', logSink=new_sink,
            uniqueWriterIdentity=True),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('sinks create my-sink dest')

  def testListNoProject(self):
    self.RunWithoutProject('sinks create my-sink dest')

  def testListNoAuth(self):
    self.RunWithoutAuth('sinks create my-sink dest')


class SinksCreateTestAlpha(SinksCreateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateSuccessWithDlp(self):
    expected_sink = self.msgs.LogSink(
        name='my-sink',
        destination='dest',
        filter='foo',
        includeChildren=False,
        dlpOptions=self.msgs.DlpOptions(
            inspectTemplateName='my-inspect-template',
            deidentifyTemplateName='my-deidentify-template'))
    new_sink = copy.deepcopy(expected_sink)
    new_sink.writerIdentity = (
        'p12345678-5432@gcp-sa-logging.iam.gserviceaccount.com')
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project',
            logSink=expected_sink,
            uniqueWriterIdentity=True), new_sink)
    self.RunLogging('sinks create my-sink dest --log-filter=foo '
                    '--dlp-inspect-template=my-inspect-template '
                    '--dlp-deidentify-template=my-deidentify-template')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Created [https://logging.googleapis.com/v2/projects/my-project/sinks/my-sink].
Also remember to grant `p12345678-5432@gcp-sa-logging.iam.gserviceaccount.com` DLP User and DLP Reader roles on the project that owns the sink destination.
More information about sinks can be found at https://cloud.google.com/logging/docs/export/configure_export
""")

  def testCreateSuccessWithPartitionedTables(self):
    expected_sink = self.msgs.LogSink(
        name='my-sink',
        destination='dest',
        filter='foo',
        includeChildren=False,
        bigqueryOptions=self.msgs.BigQueryOptions(
            usePartitionedTables=True))
    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project',
            logSink=expected_sink,
            uniqueWriterIdentity=True), expected_sink)
    self.RunLogging('sinks create my-sink dest --log-filter=foo '
                    '--use-partitioned-tables')
    self.AssertOutputEquals('')

  def testCreateSuccessWithExclusions(self):
    expected_sink = self.msgs.LogSink(
        name='my-sink',
        destination='dest',
        filter='foo',
        includeChildren=False,
        exclusions=[
            self.msgs.LogExclusion(name='ex1', filter='filter1'),
            self.msgs.LogExclusion(
                name='ex2', filter='f2', description='desc', disabled=True),
        ])

    self.mock_client_v2.projects_sinks.Create.Expect(
        self.msgs.LoggingProjectsSinksCreateRequest(
            parent='projects/my-project',
            logSink=expected_sink,
            uniqueWriterIdentity=True), expected_sink)
    self.RunLogging(
        'sinks create my-sink dest --log-filter=foo '
        '--exclusion=name=ex1,filter=filter1 '
        '--exclusion=name=ex2,filter=f2,description=desc,disabled=True')
    self.AssertOutputEquals('')

  def testCreateFailsWithBadExclusionKey(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunLogging(
          'sinks create my-sink dest --log-filter=foo '
          '--exclusion=pork=pie')
      self.AssertErrContains('argument --exclusion')


if __name__ == '__main__':
  test_case.main()
