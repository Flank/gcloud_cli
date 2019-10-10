# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tests of the 'metrics list' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class MetricsListTest(base.LoggingTestBase):

  def SetUp(self):
    self._metrics = [
        util.GetMessages().LogMetric(
            name='my-metric',
            description='my-metric description',
            filter='my-metric filter'),
        util.GetMessages().LogMetric(
            name='my-metric2',
            description='my-metric2 description',
            filter='my-metric2 filter')]

  def _setListResponse(self, metrics):
    self.mock_client_v2.projects_metrics.List.Expect(
        util.GetMessages().LoggingProjectsMetricsListRequest(
            parent='projects/my-project'),
        util.GetMessages().ListLogMetricsResponse(metrics=metrics))

  def testListLimit(self):
    self._setListResponse(self._metrics)
    self.RunLogging('metrics list --limit 1')
    self.AssertOutputContains(self._metrics[0].name)
    self.AssertOutputNotContains(self._metrics[1].name)

  def testList(self):
    self._setListResponse(self._metrics)
    self.RunLogging('metrics list')
    for metric in self._metrics:
      self.AssertOutputContains(metric.name)
      self.AssertOutputContains(metric.description)
      self.AssertOutputContains(metric.filter)

  def testListNoPerms(self):
    self.mock_client_v2.projects_metrics.List.Expect(
        util.GetMessages().LoggingProjectsMetricsListRequest(
            parent='projects/my-project'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('metrics list')

  def testListNoProject(self):
    self.RunWithoutProject('metrics list')

  def testListNoAuth(self):
    self.RunWithoutAuth('metrics list')

  def testListWithV2FeaturesBeta(self):
    self.track = calliope_base.ReleaseTrack.BETA
    msgs = util.GetMessages()
    full_metric = msgs.LogMetric(
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
        '".*quantity=(\d+).*")',  # pylint: disable=anomalous-backslash-in-string
        bucketOptions=msgs.BucketOptions(
            linearBuckets=msgs.Linear(numFiniteBuckets=2, offset=1, width=10)))
    self._setListResponse(self._metrics + [full_metric])
    self.RunLogging('metrics list')
    self.AssertOutputContains(textwrap.dedent("""\
    bucketOptions:
      linearBuckets:
        numFiniteBuckets: 2
        offset: 1.0
        width: 10.0"""))
    self.AssertOutputContains(textwrap.dedent("""\
    labelExtractors:
      label1: REGEXP_EXTRACT(jsonPayload.request, "before ([a-zA-Z ]+) after")
    """))
    self.AssertOutputContains(textwrap.dedent("""\
    metricDescriptor:
      displayName: displayname
      labels:
      - key: label1
        valueType: STRING
      metricKind: DELTA
      valueType: DOUBLE"""))
    self.AssertOutputContains(
        'valueExtractor: '
        'REGEXP_EXTRACT(jsonPayload.request, ".*quantity=(\d+).*")')  # pylint:disable=anomalous-backslash-in-string


if __name__ == '__main__':
  test_case.main()
