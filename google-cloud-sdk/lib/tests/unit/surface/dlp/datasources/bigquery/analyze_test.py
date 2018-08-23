# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""dlp datasources bigquery analyze tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class AnalyzeTest(base.DlpUnitTestBase):
  """dlp datasources bigquery analyze tests."""

  @parameterized.named_parameters(
      ('CatStatField', calliope_base.ReleaseTrack.ALPHA, 'myjob', 'myds',
       'mytable', 'col1.subcol.id', None, None, None, ['mycooltopic'], None),
      ('NumStatField', calliope_base.ReleaseTrack.ALPHA, 'myjob', 'myds',
       'mytable', None, 'col2.subcol.id', None, None, None,
       ['fakeproject.myds.mytable1', 'fakeproject.myds.mytable2']),
      ('LDiversity', calliope_base.ReleaseTrack.ALPHA, 'myjob', 'myds',
       'mytable', None, None, ['col1', 'col2.subcol.id'], 'col1',
       ['mycooltopic'], None),
  )
  def testAnalyze(self, track, jobid, dataset, table, cat_stat_field,
                  num_stat_field, quasi_ids, sensitive_field, output_topics,
                  output_tables):
    self.track = track
    job = self.MakeAnalysisJob(jobid, dataset, table, self.Project(),
                               cat_stat_field, num_stat_field, quasi_ids,
                               sensitive_field)
    create_job_request = self.MakeJobCreateRequest(
        jobid,
        risk_config=self.MakeAnalysisConfig(
            dataset, table, self.Project(), cat_stat_field, num_stat_field,
            quasi_ids, sensitive_field, output_topics, output_tables))
    self.client.projects_dlpJobs.Create.Expect(
        request=create_job_request, response=job)
    table_flag = '{}.{}.{}'.format(self.Project(), dataset, table)
    if output_tables:
      output_flag = '--output-tables {}'.format(','.join(output_tables))
    else:  # topics
      output_flag = '--output-topics {}'.format(','.join(output_topics))

    if cat_stat_field:
      privacy_metric = '--categorical-stat-field ' + cat_stat_field
    elif num_stat_field:
      privacy_metric = '--numerical-stat-field ' + num_stat_field
    else:
      quasi_id_flag = '--quasi-ids ' + ','.join(quasi_ids)
      if sensitive_field:
        sensitive_attribute_flag = '--sensitive-attribute ' + sensitive_field
      else:
        sensitive_attribute_flag = ''
      privacy_metric = '{} {}'.format(quasi_id_flag, sensitive_attribute_flag)

    self.assertEqual(job, self.Run(
        'dlp datasources bigquery analyze {table} --job-id {job} '
        '{output} {privacy_metric}'.format(
            table=table_flag,
            job=jobid,
            output=output_flag,
            privacy_metric=privacy_metric)))

  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testAnalyzeMissingQuasiIdFails(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           '--quasi-ids must be specified'):
      self.Run(
          'dlp datasources bigquery analyze fakeproject.myds.mytable2 '
          '--output-topics mytopic --sensitive-attribute col1')

  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testAnalyzeMultiplePrivacyMetricsFails(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'Exactly one of (--categorical-stat-field | --numerical-stat-field | '
        '[--quasi-ids : --sensitive-attribute]) must be specified.'):
      self.Run(
          'dlp datasources bigquery analyze fakeproject.myds.mytable2 '
          '--output-topics mytopic --categorical-stat-field col1 '
          '--numerical-stat-field col2')

if __name__ == '__main__':
  test_case.main()
