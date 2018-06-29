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
"""dlp datasources datastore inspect tests."""
from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class InspectTest(base.DlpUnitTestBase):
  """dlp datasources datastore inspect tests."""

  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testInspectDefaults(self, track):
    self.track = track
    job = self.MakeJob(
        None,
        input_ds_kind='mykind',
        input_ds_namespace='mynamespace',
        output_topics=['my_topic'],
        mintime=None,
        maxtime=None)
    create_job_request = self.MakeJobCreateRequest(
        None,
        inspect_config=job.inspectDetails.requestedOptions.jobConfig)
    self.client.projects_dlpJobs.Create.Expect(
        request=create_job_request, response=job)
    self.Run('dlp datasources datastore inspect mynamespace:mykind '
             '--output-topics my_topic --info-types LAST_NAME,EMAIL_ADDRESS')

  @parameterized.named_parameters(
      ('TopicOutput', calliope_base.ReleaseTrack.ALPHA, 'mykind', 'mynamespace',
       ['PHONE_NUMBER', 'LAST_NAME'], ['mytopic1', 'mytopic2'], None, True,
       False, 500, 10, 'LIKELY',
       '2018-05-01T12:00:00.000Z', '2018-05-31T12:00:00.000Z'),
      ('TableOutput', calliope_base.ReleaseTrack.ALPHA, 'mykind', 'mynamespace',
       ['PHONE_NUMBER', 'LAST_NAME'], None, [
           'fakeproject.myds.mytable1', 'fakeproject.myds.mytable2'], False,
       True, 100, 5, 'VERY-LIKELY', '2018-05-01T12:00:00.000Z', None))
  def testInspectWithOptionalParams(
      self, track, ds_kind, ds_namespace, info_types, output_topics,
      output_tables, exclude_info_types, include_quote,
      max_findings, max_findings_per_item, min_likelihood, mintime, maxtime):
    self.track = track
    job_ref = resources.REGISTRY.Parse(
        'my_job',
        params={'projectsId': self.Project()},
        collection='dlp.projects.dlpJobs')

    job = self.MakeJob(
        job_ref.RelativeName(),
        info_types=info_types,
        input_ds_kind=ds_kind,
        input_ds_namespace=ds_namespace,
        output_topics=output_topics,
        output_tables=output_tables,
        exclude_info_types=exclude_info_types,
        include_quote=include_quote,
        max_findings=max_findings,
        min_likelihood=min_likelihood,
        max_findings_per_item=max_findings_per_item,
        maxtime=maxtime,
        mintime=mintime)

    create_job_request = self.MakeJobCreateRequest(
        job_ref.Name(),
        inspect_config=job.inspectDetails.requestedOptions.jobConfig)
    self.client.projects_dlpJobs.Create.Expect(
        request=create_job_request, response=job)

    include_qt_flag = '--include-quote' if include_quote else ''
    exclude_it_flag = '--exclude-info-types' if exclude_info_types else ''
    likelihood_flag = (
        '--min-likelihood ' + min_likelihood if min_likelihood else '')
    info_type_values = ','.join(info_types)
    max_findings_flag = '--max-findings {}'.format(max_findings)
    max_item_findings_flag = '--max-findings-per-item {}'.format(
        max_findings_per_item)
    min_time_flag = '--min-time '+ mintime if mintime else ''
    max_time_flag = '--max-time ' + maxtime if maxtime else ''
    if output_tables:
      output_flag = '--output-tables {}'.format(','.join(output_tables))
    else:  # topics
      output_flag = '--output-topics {}'.format(','.join(output_topics))
    likelihood_flag = (
        '--min-likelihood ' + min_likelihood.replace('_', '-').lower())

    self.Run('dlp datasources datastore inspect mynamespace:mykind '
             '--job-id my_job {outputflag} --info-types {infotypes} '
             '{includeqt} {exlude_types} {likelihood} {maxfindings} '
             '{maxitemfindings} {mintime} {maxtime}'.format(
                 outputflag=output_flag,
                 infotypes=info_type_values,
                 includeqt=include_qt_flag,
                 exlude_types=exclude_it_flag,
                 likelihood=likelihood_flag,
                 maxfindings=max_findings_flag,
                 maxitemfindings=max_item_findings_flag,
                 mintime=min_time_flag,
                 maxtime=max_time_flag
             ))


if __name__ == '__main__':
  test_case.main()
