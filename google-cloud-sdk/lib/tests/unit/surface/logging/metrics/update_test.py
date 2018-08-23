# -*- coding: utf-8 -*- #
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

"""Tests of the 'metrics update' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import yaml
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class MetricsUpdateTest(base.LoggingTestBase):

  def testUpdateSuccess(self):
    test_metric = util.GetMessages().LogMetric(
        name='my-metric',
        description='my-metric description',
        filter='my-metric filter')
    self.mock_client_v2.projects_metrics.Get.Expect(
        util.GetMessages().LoggingProjectsMetricsGetRequest(
            metricName='projects/my-project/metrics/my-metric'),
        test_metric)
    updated_metric = util.GetMessages().LogMetric(
        name=test_metric.name, description='metricfoo', filter='foo')
    self.mock_client_v2.projects_metrics.Update.Expect(
        util.GetMessages().LoggingProjectsMetricsUpdateRequest(
            metricName='projects/my-project/metrics/my-metric',
            logMetric=updated_metric),
        updated_metric)
    self.RunLogging('metrics update my-metric '
                    '--description=metricfoo --log-filter=foo --format=default')
    self.AssertErrContains('Updated [%s].' % test_metric.name)
    self.AssertOutputContains('metricfoo')
    self.AssertOutputContains('foo')
    self.AssertOutputNotContains('my-metric description')
    self.AssertOutputNotContains('my-metric filter')

  def testUpdateNoPerms(self):
    self.mock_client_v2.projects_metrics.Get.Expect(
        util.GetMessages().LoggingProjectsMetricsGetRequest(
            metricName='projects/my-project/metrics/my-metric'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('metrics update my-metric --log-filter=foo')

  def testUpdateNoProject(self):
    self.RunWithoutProject('metrics update my-metric --log-filter=foo')

  def testUpdateNoAuth(self):
    self.RunWithoutAuth('metrics update my-metric --log-filter=foo')

  def testUpdateNoDescriptionNoLogFilter(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunLogging('metrics update my-metric')
    self.AssertErrContains('--description --log-filter')


class MetricsUpdateBetaTest(base.LoggingTestBase, sdk_test_base.WithTempCWD):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testUpdateNoFlags(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunLogging('metrics update my-metric')
    self.AssertErrContains('--description --log-filter')

  def testUpdateWithFlags(self):
    test_metric = util.GetMessages().LogMetric(
        name='my-metric',
        description='my-metric description',
        filter='my-metric filter')
    self.mock_client_v2.projects_metrics.Get.Expect(
        util.GetMessages().LoggingProjectsMetricsGetRequest(
            metricName='projects/my-project/metrics/my-metric'),
        test_metric)
    updated_metric = util.GetMessages().LogMetric(
        name=test_metric.name, description='metricfoo', filter='foo')
    self.mock_client_v2.projects_metrics.Update.Expect(
        util.GetMessages().LoggingProjectsMetricsUpdateRequest(
            metricName='projects/my-project/metrics/my-metric',
            logMetric=updated_metric),
        updated_metric)
    self.RunLogging('metrics update my-metric '
                    '--description=metricfoo --log-filter=foo --format=default')
    self.AssertErrContains('Updated [my-metric]')
    self.AssertOutputContains('metricfoo')
    self.AssertOutputContains('foo')
    self.AssertOutputNotContains('my-metric description')
    self.AssertOutputNotContains('my-metric filter')

  def testUpdateMetricFromFileAllData(self):
    msgs = util.GetMessages()
    test_metric = msgs.LogMetric(
        name='my-metric',
        description='my-metric description',
        filter='my-metric filter')
    self.mock_client_v2.projects_metrics.Get.Expect(
        msgs.LoggingProjectsMetricsGetRequest(
            metricName='projects/my-project/metrics/my-metric'),
        test_metric)
    updated_metric = msgs.LogMetric(
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
    self.mock_client_v2.projects_metrics.Update.Expect(
        msgs.LoggingProjectsMetricsUpdateRequest(
            metricName='projects/my-project/metrics/my-metric',
            logMetric=updated_metric),
        updated_metric)
    self.RunLogging('metrics update my-metric --config-from-file {}'.format(
        sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface', 'logging',
                                       'metrics', 'testdata', 'config.yaml')))

  def testUpdateMetricFromFileSomeData(self):
    msgs = util.GetMessages()
    self.Touch(self.cwd_path, 'update.yaml', contents=(
        'description: My fun filter.\n'
        'filter: severity>=ERROR'))
    test_metric = msgs.LogMetric(
        name='my-metric',
        description='my-metric description',
        filter='my-metric filter',
        labelExtractors=msgs.LogMetric.LabelExtractorsValue(
            additionalProperties=[
                msgs.LogMetric.LabelExtractorsValue.AdditionalProperty(
                    key='label1', value='extractor1')]
        ))
    self.mock_client_v2.projects_metrics.Get.Expect(
        msgs.LoggingProjectsMetricsGetRequest(
            metricName='projects/my-project/metrics/my-metric'),
        test_metric)
    updated_metric = msgs.LogMetric(
        name='my-metric',
        description='My fun filter.',
        filter='severity>=ERROR',
        labelExtractors=msgs.LogMetric.LabelExtractorsValue(
            additionalProperties=[
                msgs.LogMetric.LabelExtractorsValue.AdditionalProperty(
                    key='label1', value='extractor1')]
        ))
    self.mock_client_v2.projects_metrics.Update.Expect(
        msgs.LoggingProjectsMetricsUpdateRequest(
            metricName='projects/my-project/metrics/my-metric',
            logMetric=updated_metric),
        updated_metric)
    self.RunLogging('metrics update my-metric --config-from-file {}'.format(
        os.path.join(self.cwd_path, 'update.yaml')))

  def testUpdateMetricBadFile(self):
    test_metric = util.GetMessages().LogMetric(
        name='my-metric',
        description='my-metric description',
        filter='my-metric filter')
    self.mock_client_v2.projects_metrics.Get.Expect(
        util.GetMessages().LoggingProjectsMetricsGetRequest(
            metricName='projects/my-project/metrics/my-metric'),
        test_metric)
    self.Touch(self.cwd_path, 'bad.yaml', contents='[')
    with self.assertRaises(yaml.Error):
      self.RunLogging('metrics update my-metric --config-from-file {}'.format(
          os.path.join(self.cwd_path, 'bad.yaml')))


if __name__ == '__main__':
  test_case.main()
