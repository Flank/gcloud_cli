# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests of the 'metrics create' subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
import os

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import yaml
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class MetricsCreateTest(base.LoggingTestBase):

  def testCreateSuccess(self):
    new_metric = util.GetMessages().LogMetric(
        name='my-metric', description='my-desc', filter='my-filter')
    self.mock_client_v2.projects_metrics.Create.Expect(
        util.GetMessages().LoggingProjectsMetricsCreateRequest(
            parent='projects/my-project', logMetric=new_metric),
        new_metric)
    self.RunLogging('metrics create my-metric --description=my-desc '
                    '--log-filter=my-filter')
    self.AssertOutputContains('')
    self.AssertErrContains('Created [%s].' % new_metric.name)

  def testCreateNoPerms(self):
    new_metric = util.GetMessages().LogMetric(
        name='my-metric', description='my-desc', filter='my-filter')
    self.mock_client_v2.projects_metrics.Create.Expect(
        util.GetMessages().LoggingProjectsMetricsCreateRequest(
            parent='projects/my-project', logMetric=new_metric),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('metrics create my-metric --description=my-desc '
                         '--log-filter=my-filter')

  def testCreateNoProject(self):
    self.RunWithoutProject('metrics create new-metric --description=my-desc '
                           '--log-filter=my-filter')

  def testCreateNoAuth(self):
    self.RunWithoutAuth('metrics create new-metric --description=my-desc '
                        '--log-filter=my-filter')


class MetricsCreateBetaTest(base.LoggingTestBase, sdk_test_base.WithTempCWD):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateWithFlags(self):
    new_metric = util.GetMessages().LogMetric(
        name='my-metric', description='my-desc', filter='my-filter')
    self.mock_client_v2.projects_metrics.Create.Expect(
        util.GetMessages().LoggingProjectsMetricsCreateRequest(
            parent='projects/my-project', logMetric=new_metric),
        new_metric)
    self.RunLogging('metrics create my-metric --description=my-desc '
                    '--log-filter=my-filter')
    self.AssertOutputContains('')
    self.AssertErrContains('Created [my-metric]')

  def testCreateMetricFromYamlFile(self):
    msgs = util.GetMessages()
    new_metric = msgs.LogMetric(
        name='my-metric',
        description='My fun filter.',
        filter='severity>=ERROR',
        labelExtractors=msgs.LogMetric.LabelExtractorsValue(
            additionalProperties=[
                msgs.LogMetric.LabelExtractorsValue.AdditionalProperty(
                    key='label1', value='REGEXP_EXTRACT(jsonPayload.request, '
                    '"before ([a-zA-Z ]+) after")')]
        ),
        metricDescriptor=msgs.MetricDescriptor(
            displayName='displayname',
            valueType=msgs.MetricDescriptor.ValueTypeValueValuesEnum.DOUBLE,
            labels=[
                msgs.LabelDescriptor(
                    description=None,
                    key='label1',
                    valueType=msgs.LabelDescriptor
                    .ValueTypeValueValuesEnum.STRING)
            ],
            metricKind=msgs.MetricDescriptor.MetricKindValueValuesEnum.DELTA),
        valueExtractor='REGEXP_EXTRACT(jsonPayload.request, '
        '".*quantity=(\d+).*")')  # pylint: disable=anomalous-backslash-in-string
    self.mock_client_v2.projects_metrics.Create.Expect(
        msgs.LoggingProjectsMetricsCreateRequest(
            parent='projects/my-project', logMetric=new_metric),
        new_metric)
    self.RunLogging('metrics create my-metric --config-from-file {}'.format(
        sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface', 'logging',
                                       'metrics', 'testdata', 'config.yaml')
    ))

  def testCreateMetricFromJsonFile(self):
    msgs = util.GetMessages()
    # The only difference in this 'expected' type from the one in the YAML test
    # is that it has unicode strings (u'xxx') in some additional places to match
    # what is produced when parsing JSON.
    new_metric = msgs.LogMetric(
        name='my-metric',
        description='My fun filter.',
        filter='severity>=ERROR',
        labelExtractors=msgs.LogMetric.LabelExtractorsValue(
            additionalProperties=[
                msgs.LogMetric.LabelExtractorsValue.AdditionalProperty(
                    key='label1', value='REGEXP_EXTRACT(jsonPayload.request, '
                    '"before ([a-zA-Z ]+) after")')]
        ),
        metricDescriptor=msgs.MetricDescriptor(
            displayName='displayname',
            valueType=msgs.MetricDescriptor.ValueTypeValueValuesEnum.DOUBLE,
            labels=[
                msgs.LabelDescriptor(
                    description=None,
                    key='label1',
                    valueType=msgs.LabelDescriptor
                    .ValueTypeValueValuesEnum.STRING)
            ],
            metricKind=msgs.MetricDescriptor.MetricKindValueValuesEnum.DELTA),
        valueExtractor='REGEXP_EXTRACT(jsonPayload.request, '
        '".*quantity=(\d+).*")')  # pylint: disable=anomalous-backslash-in-string
    self.mock_client_v2.projects_metrics.Create.Expect(
        msgs.LoggingProjectsMetricsCreateRequest(
            parent='projects/my-project', logMetric=new_metric),
        new_metric)
    self.RunLogging('metrics create my-metric --config-from-file {}'.format(
        sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface', 'logging',
                                       'metrics', 'testdata', 'config.json')
    ))

  def testCreateMetricBadFile(self):
    self.Touch(self.cwd_path, 'bad.yaml', contents='[')
    with self.assertRaisesRegex(yaml.Error, 'Failed to parse YAML'):
      self.RunLogging('metrics create my-metric --config-from-file {}'.format(
          os.path.join(self.cwd_path, 'bad.yaml')))


if __name__ == '__main__':
  test_case.main()
