# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the `gcloud dataflow sql query` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import tempfile
from googlecloudsdk.api_lib.dataflow import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID


class SqlQueryTestBeta(base.DataflowMockingTestBase,
                       sdk_test_base.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.command = 'dataflow sql query'
    self.test_parameters = (
        '[{"name": "a", "parameterType": {"type": "STRING"}, '
        '"parameterValue": {"value": "foo"}}, '
        '{"name": "b", "parameterType": {"type": "FLOAT64"}, '
        '"parameterValue": {"value": "1.0"}}]')
    self.test_bq_output = ('[{"type": "bigquery", '
                           '"table": {'
                           '"projectId": "%s", '
                           '"datasetId": "fake-dataset", '
                           '"tableId": "fake-table"'
                           '}, "writeDisposition": "WRITE_EMPTY"}]' %
                           self.Project())
    self.test_pubsub_output = ('[{"type": "pubsub", '
                               '"projectId": "%s", '
                               '"topic": "fake-topic", '
                               '"createDisposition": "CREATE_IF_NOT_FOUND"}]' %
                               self.Project())

  def expectParameters(self, params):
    self.MockLaunchDynamicTemplate(
        gcs_location='gs://dataflow-sql-templates-us-central1/latest/sql_launcher_template',
        job=self.SampleJob(
            JOB_1_ID,
            environment=base.MESSAGE_MODULE.Environment(),
            job_name='myjob'),
        job_name='myjob',
        location='us-central1',
        parameters=params)

  def testQuery_bqDefaultProject(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': self.test_bq_output,
        'queryParameters': '[]',
        'queryString': 'SELECT 1 AS x',
    })
    result = self.Run('{} "SELECT 1 AS x" '
                      '--job-name=myjob '
                      '--region=us-central1 '
                      '--bigquery-table=fake-table '
                      '--bigquery-dataset=fake-dataset'.format(self.command))
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testQuery_pubsubDefaultProject(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': self.test_pubsub_output,
        'queryParameters': '[]',
        'queryString': 'SELECT 1 AS x',
    })
    result = self.Run('{} "SELECT 1 AS x" '
                      '--job-name=myjob '
                      '--region=us-central1 '
                      '--pubsub-topic=fake-topic'.format(self.command))
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testQuery_bqDifferentProject(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': '[{"type": "bigquery", '
                   '"table": {'
                   '"projectId": "other-project", '
                   '"datasetId": "fake-dataset", '
                   '"tableId": "fake-table"'
                   '}, "writeDisposition": "WRITE_EMPTY"}]',
        'queryParameters': '[]',
        'queryString': 'SELECT 1 AS x',
    })
    result = self.Run('{} "SELECT 1 AS x" '
                      '--job-name=myjob '
                      '--region=us-central1 '
                      '--bigquery-project=other-project '
                      '--bigquery-table=fake-table '
                      '--bigquery-dataset=fake-dataset'.format(self.command))
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testQuery_pubsubDifferentProject(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': '[{"type": "pubsub", '
                   '"projectId": "other-project", '
                   '"topic": "fake-topic", '
                   '"createDisposition": "CREATE_IF_NOT_FOUND"}]',
        'queryParameters': '[]',
        'queryString': 'SELECT 1 AS x',
    })
    result = self.Run('{} "SELECT 1 AS x" '
                      '--job-name=myjob '
                      '--region=us-central1 '
                      '--pubsub-project=other-project '
                      '--pubsub-topic=fake-topic'.format(self.command))
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testQuery_withCommandLineParameters(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': self.test_bq_output,
        'queryParameters': self.test_parameters,
        'queryString': 'SELECT @a AS x, @b AS y'
    })
    result = self.Run('{} "SELECT @a AS x, @b AS y" '
                      '--job-name=myjob '
                      '--region=us-central1 '
                      '--bigquery-table=fake-table '
                      '--bigquery-dataset=fake-dataset '
                      '--parameter=a::foo '
                      '--parameter=b:FLOAT64:1.0'.format(self.command))
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testQuery_withParametersFile(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': self.test_bq_output,
        'queryParameters': self.test_parameters,
        'queryString': 'SELECT @a AS x, @b AS y'
    })
    # Cannot read already open tempfile in Windows.
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as parameters_file:
      parameters_file_name = parameters_file.name
      parameters_file.write(self.test_parameters)
    try:
      result = self.Run('{} "SELECT @a AS x, @b AS y" '
                        '--job-name=myjob '
                        '--region=us-central1 '
                        '--bigquery-table=fake-table '
                        '--bigquery-dataset=fake-dataset '
                        '--parameters-file={}'.format(self.command,
                                                      parameters_file_name))
      self.assertEqual(JOB_1_ID, result.job.id)
      self.assertEqual('myjob', result.job.name)
    finally:
      os.remove(parameters_file_name)

  def testQuery_noRegion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --region: Must be specified.'):
      self.Run('{} "SELECT 1 AS x" '
               '--job-name=myjob '
               '--pubsub-topic=wordcounts'.format(self.command))

  def testQuery_noBigQueryDataset(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.Error, 'argument --bigquery-dataset: Must be specified.'):
      self.Run('{} "SELECT 1 AS x" '
               '--job-name=myjob '
               '--region=us-central1 '
               '--bigquery-table=wordcounts'.format(self.command))

  def testQuery_withCommandLineArrayParameter(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': self.test_bq_output,
        'queryParameters':
            '[{"name": "a", '
            '"parameterType": {"arrayType": {"type": "STRING"}, '
            '"type": "ARRAY"}, "parameterValue": {"arrayValues": '
            '[{"value": "foo"}, {"value": "bar"}]}}]',
        'queryString': 'SELECT @a AS x'
    })
    param_value = 'a:ARRAY<STRING>:["foo", "bar"]'
    result = self.Run('{} "SELECT @a AS x" '
                      '--job-name=myjob '
                      '--region=us-central1 '
                      '--bigquery-table=fake-table '
                      '--bigquery-dataset=fake-dataset '
                      "--parameter='{}'".format(self.command, param_value))
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  # Note: structs are not yet supported by Beam ZetaSQL.
  # https://issues.apache.org/jira/browse/BEAM-9300
  def testQuery_withCommandLineStructParameter(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': self.test_bq_output,
        'queryParameters':
            '[{"name": "struct_value", '
            '"parameterType": {"structTypes": '
            '[{"name": "a", "type": {"type": "INT64"}}, '
            '{"name": "b", "type": {"type": "STRING"}}], '
            '"type": "STRUCT"}, "parameterValue": {"structValues": '
            '{"a": {"value": 1}, "b": {"value": "foo"}}}}]',
        'queryString': 'SELECT @struct_value.a AS x, @struct_value.b AS y'
    })
    param_value = 'struct_value:STRUCT<a INT64, b STRING>:{"a": 1, "b": "foo"}'
    result = self.Run('{} "SELECT @struct_value.a AS x, @struct_value.b AS y" '
                      '--job-name=myjob '
                      '--region=us-central1 '
                      '--bigquery-table=fake-table '
                      '--bigquery-dataset=fake-dataset '
                      "--parameter='{}'".format(self.command, param_value))
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testQuery_noOutput(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument ([--bigquery-table : --bigquery-dataset --bigquery-project] [--pubsub-topic : --pubsub-project]): Must be specified.'
    ):
      self.Run('{} "SELECT 1 AS x" '
               '--region=us-central1 '
               '--job-name=myjob'.format(self.command))

  def testQuery_bqAndPubsubOutputs(self):
    self.expectParameters({
        'dryRun': 'false',
        'outputs': ('[{"type": "bigquery", '
                    '"table": {'
                    '"projectId": "%s", '
                    '"datasetId": "fake-dataset", '
                    '"tableId": "fake-table"'
                    '}, "writeDisposition": "WRITE_EMPTY"}, '
                    '{"type": "pubsub", '
                    '"projectId": "%s", '
                    '"topic": "fake-topic", '
                    '"createDisposition": "CREATE_IF_NOT_FOUND"}]' %
                    (self.Project(), self.Project())),
        'queryParameters': '[]',
        'queryString': 'SELECT 1 AS x',
    })
    result = self.Run('{} "SELECT 1 AS x" '
                      '--job-name=myjob '
                      '--region=us-central1 '
                      '--bigquery-table=fake-table '
                      '--bigquery-dataset=fake-dataset '
                      '--pubsub-topic=fake-topic'.format(self.command))
    self.assertEqual(JOB_1_ID, result.job.id)
    self.assertEqual('myjob', result.job.name)

  def testQuery_noJobName(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --job-name: Must be specified.'):
      self.Run('{} "SELECT 1 AS x" '
               '--region=us-central1 '
               '--pubsub-topic=wordcounts'.format(self.command))

  def testqueryParametersAndParameterFile(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --parameter: At most one of --parameter | --parameters-file may be specified.'
    ):
      self.Run('{} "SELECT @a AS x" '
               '--job-name=myjob '
               '--region=us-central1 '
               '--pubsub-topic=fake-topic '
               '--parameter=a::foo '
               '--parameters-file=params.txt'.format(self.command))


class SqlQueryTestAlpha(SqlQueryTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
