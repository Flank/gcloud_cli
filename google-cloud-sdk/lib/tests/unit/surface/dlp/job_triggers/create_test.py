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
"""dlp job-triggers create tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.dlp import hooks
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class CreateTest(base.DlpUnitTestBase):
  """dlp job-triggers create tests."""

  @parameterized.named_parameters(
      ('DefaultGCSTrigger', calliope_base.ReleaseTrack.ALPHA, 'my_gcs_trigger',
       None, None, ['PHONE_NUMBER', 'PERSON_NAME'], None, None, None, None,
       None, ['test.ds.table'], None, '84000s',
       {'gcs_bucket': 'gs://my-bucket/'}, 'gcs'),

      ('DefaultGCSTriggerMultipleOutput', calliope_base.ReleaseTrack.ALPHA,
       'my_gcs_trigger', None, None, ['PHONE_NUMBER', 'PERSON_NAME'], None,
       None, None, None, None, ['test.ds.table1', 'test.ds.table2'], None,
       '84000s', {'gcs_bucket': 'gs://my-bucket/'}, 'gcs'),

      ('DataStoreTrigger', calliope_base.ReleaseTrack.ALPHA,
       'my_ds_trigger', 'My Description', 'My-Trigger',
       ['PHONE_NUMBER', 'PERSON_NAME'], 'very-likely', 100, 3, True, True,
       None, ['topic1', 'topic2'], '84000s',
       {'ds_namespace_id': 'My', 'ds_kind': 'dskind'}, 'datastore'),

      ('BigTableTrigger', calliope_base.ReleaseTrack.ALPHA,
       'my_bt_trigger', None, None, ['PHONE_NUMBER', 'PERSON_NAME'], None,
       None, None, None, None, ['test.ds.table1', 'test.ds.table2'], None,
       '84000s', {'bt_data_set_id': 'mydataset', 'bt_table_id': 'mytable'},
       'table'),
  )
  def testCreate(self, track, trigger_name, description, display_name,
                 info_types, min_likelihood, max_findings, max_findings_item,
                 include_quote, exclude_info_types, output_tables,
                 output_topics, schedule, input_params, input_type):
    self.track = track
    input_params['project_id'] = self.Project()
    if min_likelihood:
      likelyhood_enum_string = min_likelihood.replace('-', '_').upper()
    else:
      likelyhood_enum_string = 'POSSIBLE'

    job_trigger = self.MakeJobTrigger(
        description=description or None,
        display_name=display_name or None,
        info_types=info_types,
        include_quote=include_quote,
        exclude_info_types=exclude_info_types,
        min_likelihood=likelyhood_enum_string,
        request_limit=max_findings or None,
        item_limit=max_findings_item or None,
        input_params=input_params,
        input_type=input_type,
        output_topics=output_topics,
        output_tables=output_tables,
        duration=schedule
    )

    create_request = self.MakeJobTriggerCreateRequest(trigger_name, job_trigger)
    self.client.projects_jobTriggers.Create.Expect(request=create_request,
                                                   response=job_trigger)

    include_qt_flag = '--include-quote' if include_quote else ''
    exclude_it_flag = '--exclude-info-types' if exclude_info_types else ''
    likelihood_flag = (
        '--min-likelihood ' + min_likelihood if min_likelihood else '')
    info_type_values = ','.join(info_types)
    max_findings_flag = (
        '--max-findings {}'.format(max_findings) if max_findings else '')
    item_findings_flag = ('--max-findings-per-item {}'.format(max_findings_item)
                          if max_findings_item else '')
    description_flag = (
        '--description "{}" '.format(description) if description else '')
    display_name_flag = '--display-name ' + display_name if display_name else ''

    if input_type == 'gcs':
      input_flag = '--path ' + input_params['gcs_bucket']
    elif input_type == 'table':
      input_flag = '--input-table {}.{}.{}'.format(
          input_params['project_id'], input_params['bt_data_set_id'],
          input_params['bt_table_id'])
    else:  # datastore
      input_flag = '--datastore-kind {}:{}'.format(
          input_params['ds_namespace_id'], input_params['ds_kind'])

    if output_tables:
      output_flag = '--output-tables {}'.format(','.join(output_tables))
    else:  # topics
      output_flag = '--output-topics {}'.format(','.join(output_topics))

    self.assertEqual(job_trigger,
                     self.Run(
                         'dlp job-triggers create {triggername} {displayname} '
                         '--info-types {infotypes} {quote} {exclude_types} '
                         '--trigger-schedule {schedule} {input_flg} '
                         '{output_flg} {description} {req_findings} '
                         '{item_findings} {likelihood}'.format(
                             triggername=trigger_name,
                             infotypes=info_type_values,
                             quote=include_qt_flag,
                             exclude_types=exclude_it_flag,
                             schedule=schedule,
                             displayname=display_name_flag,
                             input_flg=input_flag,
                             output_flg=output_flag,
                             description=description_flag,
                             req_findings=max_findings_flag,
                             item_findings=item_findings_flag,
                             likelihood=likelihood_flag)))

  @parameterized.parameters((calliope_base.ReleaseTrack.ALPHA, 'foo',
                             'given value must be of the form INTEGER[UNIT]'),
                            (calliope_base.ReleaseTrack.ALPHA, '100M',
                             'unit must be one of s, m, h, d; received: M'))
  def testCreateBadScheduleFails(self, track, schedule, error):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, error):
      self.Run('dlp job-triggers create test-trigger '
               '--info-types PHONE_NUMBER --trigger-schedule {} '
               '--input-table test.fake.foo -output-topics topic'.format(
                   schedule))

  @parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,
                             'too.many.seg.ments'),
                            (calliope_base.ReleaseTrack.ALPHA,
                             'too.fewsegments'))
  def testCreateWithBadTableNameFails(self, track, tablename):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        hooks.BigQueryTableNameError,
        ('Invalid BigQuery table name [{}]. BigQuery tables are uniquely '
         'identified by their project_id, dataset_id, and table_id in the '
         'format `<project_id>.<dataset_id>.<table_id>`.'.format(tablename))):
      self.Run('dlp job-triggers create test-trigger '
               '--info-types PHONE_NUMBER --trigger-schedule 100h '
               '--input-table {} --output-topics topic'.format(
                   tablename))

  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testCreateWithTableNameAndTopicFails(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'Exactly one of (--output-tables | --output-topics) '
        'must be specified.'):
      self.Run('dlp job-triggers create test-trigger '
               '--info-types PHONE_NUMBER --trigger-schedule 100h '
               '--input-table my.tab.le --output-tables not.that.good '
               '--output-topics topic')


if __name__ == '__main__':
  test_case.main()
