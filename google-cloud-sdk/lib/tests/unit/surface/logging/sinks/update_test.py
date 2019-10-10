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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class SinksUpdateTest(base.LoggingTestBase):

  def testUpdateSuccess(self):
    test_sink = self.msgs.LogSink(
        name='my-sink', destination='base', filter='foo',
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    updated_sink = self.msgs.LogSink(
        name=test_sink.name, destination='dest', filter='bar')
    self.mock_client_v2.projects_sinks.Patch.Expect(
        self.msgs.LoggingProjectsSinksPatchRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=updated_sink,
            uniqueWriterIdentity=True,
            updateMask='destination,filter'), updated_sink)
    self.RunLogging(
        'sinks update my-sink dest --log-filter=bar --format=default')
    self.AssertErrContains('Updated')
    self.AssertOutputContains('dest')
    self.AssertOutputContains('bar')
    self.AssertOutputNotContains(test_sink.destination)

  def testUpdateSuccessOtherFieldsPreserved(self):
    test_sink = self.msgs.LogSink(
        name='my-sink', destination='base', filter='foo',
        writerIdentity='foo@bar.com', includeChildren=True)
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    expected_sink = self.msgs.LogSink(name=test_sink.name, destination='dest')
    updated_sink = self.msgs.LogSink(
        name=test_sink.name, destination='dest', filter='foo',
        includeChildren=True)
    self.mock_client_v2.projects_sinks.Patch.Expect(
        self.msgs.LoggingProjectsSinksPatchRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=expected_sink,
            uniqueWriterIdentity=True,
            updateMask='destination'), updated_sink)
    self.RunLogging('sinks update my-sink dest --format=default')
    self.AssertErrContains('Updated')
    self.AssertOutputContains('destination: dest')
    self.AssertOutputNotContains(test_sink.destination)

  def testUpdateSuccessToEmptyFilter(self):
    test_sink = self.msgs.LogSink(
        name='my-sink', destination='base', filter='foo',
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    expected_sink = self.msgs.LogSink(name=test_sink.name, filter='')
    updated_sink = self.msgs.LogSink(
        name=test_sink.name, destination=test_sink.destination, filter='')
    self.mock_client_v2.projects_sinks.Patch.Expect(
        self.msgs.LoggingProjectsSinksPatchRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=expected_sink,
            uniqueWriterIdentity=True,
            updateMask='filter'), updated_sink)
    self.RunLogging('sinks update my-sink --log-filter="" --format=default')
    self.AssertErrContains('Updated')
    self.AssertOutputNotContains(test_sink.filter)

  def testUpdatePrompt(self):
    test_sink = self.msgs.LogSink(
        name='my-sink', destination='base', filter='foo',
        writerIdentity='cloud-logs@google.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.RunLogging('sinks update my-sink --log-filter=new')

    # Now answer Yes.
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    expected_sink = self.msgs.LogSink(name=test_sink.name, filter='new')
    updated_sink = self.msgs.LogSink(
        name=test_sink.name, destination=test_sink.destination, filter='new')
    self.mock_client_v2.projects_sinks.Patch.Expect(
        self.msgs.LoggingProjectsSinksPatchRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=expected_sink,
            uniqueWriterIdentity=True,
            updateMask='filter'), updated_sink)
    self.WriteInput('Y')
    self.RunLogging('sinks update my-sink --log-filter=new')
    self.AssertErrContains('Updated')

  def testUpdateMissingSink(self):
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        exception=http_error.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches('not found'):
      self.RunLogging('sinks update my-sink new-dest')
    self.AssertErrContains('not found')

  def testUpdateMissingRequiredFlag(self):
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        self.msgs.LogSink())
    with self.AssertRaisesExceptionRegexp(exceptions.MinimumArgumentException,
                                          r'Please specify.*'):
      self.RunLogging('sinks update my-sink')

  def testListNoPerms(self):
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('sinks update my-sink dest')

  def testListNoProject(self):
    self.RunWithoutProject('sinks update my-sink dest')

  def testListNoAuth(self):
    self.RunWithoutAuth('sinks update my-sink dest')


class SinksUpdateTestAlpha(SinksUpdateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testUpdateSuccessDlp(self):
    test_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'), test_sink)
    expected_sink = self.msgs.LogSink(
        name=test_sink.name,
        dlpOptions=self.msgs.DlpOptions(
            inspectTemplateName='my-inspect-template',
            deidentifyTemplateName='my-deidentify-template'))
    updated_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        writerIdentity='foo@bar.com',
        dlpOptions=self.msgs.DlpOptions(
            inspectTemplateName='my-inspect-template',
            deidentifyTemplateName='my-deidentify-template'))
    self.mock_client_v2.projects_sinks.Patch.Expect(
        self.msgs.LoggingProjectsSinksPatchRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=expected_sink,
            uniqueWriterIdentity=True,
            updateMask=('dlp_options.inspect_template_name,'
                        'dlp_options.deidentify_template_name')), updated_sink)
    self.RunLogging('sinks update my-sink '
                    '--dlp-inspect-template=my-inspect-template '
                    '--dlp-deidentify-template=my-deidentify-template '
                    '--format=default')
    self.AssertErrContains('Updated')
    self.AssertOutputContains('inspectTemplateName: my-inspect-template')
    self.AssertOutputContains('deidentifyTemplateName: my-deidentify-template')

  def testUpdateSuccessPartitionedTables(self):
    test_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'), test_sink)
    expected_sink = self.msgs.LogSink(
        name=test_sink.name,
        bigqueryOptions=self.msgs.BigQueryOptions(usePartitionedTables=True))
    updated_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        writerIdentity='foo@bar.com',
        bigqueryOptions=self.msgs.BigQueryOptions(usePartitionedTables=True))
    self.mock_client_v2.projects_sinks.Patch.Expect(
        self.msgs.LoggingProjectsSinksPatchRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=expected_sink,
            uniqueWriterIdentity=True,
            updateMask='bigquery_options.use_partitioned_tables'),
        updated_sink)
    self.RunLogging('sinks update my-sink '
                    '--use-partitioned-tables '
                    '--format=default')
    self.AssertErrContains('Updated')
    self.AssertOutputContains('usePartitionedTables: true')

  def testUpdateSuccessClearExclusions(self):
    test_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        exclusions=[
            self.msgs.LogExclusion(name='ex1', filter='filter1')
        ],
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'), test_sink)
    expected_sink = self.msgs.LogSink(name=test_sink.name)
    updated_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Patch.Expect(
        self.msgs.LoggingProjectsSinksPatchRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=expected_sink,
            uniqueWriterIdentity=True,
            updateMask='exclusions'),
        updated_sink)
    self.RunLogging('sinks update my-sink --clear-exclusions')
    self.AssertErrContains('Updated')
    self.AssertOutputNotContains('exclusions')

  def testUpdateRemoveNonexistentExclusion(self):
    test_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        exclusions=[
            self.msgs.LogExclusion(name='ex1', filter='filter1')
        ],
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'), test_sink)

    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException, r'Exclusions.*'):
      self.RunLogging('sinks update my-sink --remove-exclusions porkpie')

  def testUpdateRemoveExclusionsSuccess(self):
    test_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        exclusions=[
            self.msgs.LogExclusion(name='ex1', filter='filter'),
            self.msgs.LogExclusion(name='ex2', filter='filter'),
            self.msgs.LogExclusion(name='ex3', filter='filter'),
            self.msgs.LogExclusion(name='ex4', filter='filter')
        ],
        writerIdentity='foo@bar.com')
    updated_sink = self.msgs.LogSink(
        name='my-sink',
        exclusions=[
            self.msgs.LogExclusion(name='ex1', filter='filter'),
            self.msgs.LogExclusion(name='ex3', filter='filter'),
        ])
    new_sink = self.msgs.LogSink(
        name='my-sink',
        destination='base',
        filter='foo',
        exclusions=[
            self.msgs.LogExclusion(name='ex1', filter='filter'),
            self.msgs.LogExclusion(name='ex3', filter='filter'),
        ])
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'), test_sink)
    self.mock_client_v2.projects_sinks.Patch.Expect(
        self.msgs.LoggingProjectsSinksPatchRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=updated_sink,
            uniqueWriterIdentity=True,
            updateMask='exclusions'),
        new_sink)

    self.RunLogging('sinks update my-sink --remove-exclusions ex2,ex4')
    self.AssertErrContains('Updated')

if __name__ == '__main__':
  test_case.main()
