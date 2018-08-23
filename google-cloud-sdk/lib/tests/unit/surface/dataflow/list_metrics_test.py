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
"""Test of the 'dataflow metrics list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types

from googlecloudsdk.api_lib.dataflow import exceptions
from googlecloudsdk.core.util import times
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.dataflow import base
import six

JOB_1_ID = base.JOB_1_ID


class MetricsListUnitTest(base.DataflowMockingTestBase,
                          sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.job_id = JOB_1_ID
    self.example_metrics = [
        self._Metric('s5-ByteCount', 130194921.0),
        self._Metric(
            's5-ByteCount', 13019492.0, props={'tentative': 'true'}),
        self._Metric('s05-s5-finish-msecs', 0.0),
        self._Metric(
            's05-other-msecs', 3669.0, props={'tentative': 'true'}),
        self._Metric(
            'ElementCount',
            164656.0,
            props={'output_user_name': 'some/transform/Read-out0'}),
        self._Metric(
            'MeanByteCount',
            164656.0,
            props={'output_user_name': 'some/transform/Write-out0'}),
        self._Metric(
            'ElementCount',
            164656.0,
            props={'output_user_name': 'BigQueryIO.Read3-out0'}),
        self._Metric(
            'ElementCount',
            164657.0,
            props={'output_user_name': 'BigQueryIO.Read3-out0',
                   'tentative': 'true'}),
        self._Metric('BigQueryIO.Read3-out0-MeanByteCount', 77.0),
    ]
    self.sentinel_mentrics = [
        self._Metric('BigQueryIO.Read3-out0-MeanByteCount', -2),
        self._Metric('F39-windmill-data-watermark', 1123.0),
        self._Metric('F40-windmill-data-watermark', -1),
        self._Metric('F40-windmill-data-watermark', -2),
        self._Metric('F38-windmill-data-watermark', -2.0),
    ]
    self.user_metrics = [self._Metric('my-metric', 1337.0, origin='user')]
    self.unknown_watermark = [self._Metric('F41-windmill-data-watermark', -3)]

  def testListMetricsNone(self):
    self._MockRequest([])
    self.Run('beta dataflow metrics list ' + self.job_id)
    self.AssertOutputEquals('')

  def testListMetricsEmptyContext(self):
    metric = self.example_metrics[0]
    metric.name.context = None
    self._MockRequest([metric])
    self.Run('beta dataflow metrics list ' + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 130194921.0
updateTime: '2015-01-15 12:31:07'
""")

  def testListMetricsExample(self):
    self._MockRequest(self.example_metrics[0:1])
    self.Run('beta dataflow metrics list ' + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context: {}
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 130194921.0
updateTime: '2015-01-15 12:31:07'
""")

  def testListMetricsExampleWithRegion(self):
    my_region = 'europe-west1'
    self._MockRequest(self.example_metrics[0:1], region=my_region)
    self.Run('beta dataflow metrics list --region=%s %s' % (my_region,
                                                            self.job_id))
    self.AssertOutputEquals("""\
---
name:
  context: {}
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 130194921.0
updateTime: '2015-01-15 12:31:07'
""")

  def testListMetricsSentinelValues(self):
    self._MockRequest(self.example_metrics[0:1] + self.sentinel_mentrics)
    self.Run('beta dataflow metrics list ' + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context: {}
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 130194921.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: BigQueryIO.Read3-out0-MeanByteCount
  origin: dataflow/v1b3
scalar: -2
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: F39-windmill-data-watermark
  origin: dataflow/v1b3
scalar: 1123.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: F40-windmill-data-watermark
  origin: dataflow/v1b3
scalar: Unknown watermark
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: F40-windmill-data-watermark
  origin: dataflow/v1b3
scalar: Max watermark
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: F38-windmill-data-watermark
  origin: dataflow/v1b3
scalar: -2.0
updateTime: '2015-01-15 12:31:07'
""")

  def testListMetricsCommittedOnly(self):
    self._MockRequest(self.example_metrics)
    self.Run('beta dataflow metrics list ' + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context: {}
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 130194921.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: s05-s5-finish-msecs
  origin: dataflow/v1b3
scalar: 0.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Read-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Write-out0
  name: MeanByteCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: BigQueryIO.Read3-out0-MeanByteCount
  origin: dataflow/v1b3
scalar: 77.0
updateTime: '2015-01-15 12:31:07'
""")

  def testListMetricsCommittedAndTentative(self):
    self._MockRequest(self.example_metrics)
    self.Run('beta dataflow metrics list --tentative ' + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context: {}
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 130194921.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    tentative: 'true'
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 13019492.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: s05-s5-finish-msecs
  origin: dataflow/v1b3
scalar: 0.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    tentative: 'true'
  name: s05-other-msecs
  origin: dataflow/v1b3
scalar: 3669.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Read-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Write-out0
  name: MeanByteCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
    tentative: 'true'
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164657.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: BigQueryIO.Read3-out0-MeanByteCount
  origin: dataflow/v1b3
scalar: 77.0
updateTime: '2015-01-15 12:31:07'
""")

  def testListMetricsTentativeOnly(self):
    self._MockRequest(self.example_metrics)
    self.Run('beta dataflow metrics list --tentative --hide-committed ' +
             self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context:
    tentative: 'true'
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 13019492.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    tentative: 'true'
  name: s05-other-msecs
  origin: dataflow/v1b3
scalar: 3669.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
    tentative: 'true'
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164657.0
updateTime: '2015-01-15 12:31:07'
""")

  def testServiceMetricsOnly(self):
    self._MockRequest(self.example_metrics + self.user_metrics)
    self.Run('beta dataflow metrics list --source=service ' + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context: {}
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 130194921.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: s05-s5-finish-msecs
  origin: dataflow/v1b3
scalar: 0.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Read-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Write-out0
  name: MeanByteCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: BigQueryIO.Read3-out0-MeanByteCount
  origin: dataflow/v1b3
scalar: 77.0
updateTime: '2015-01-15 12:31:07'
""")

  def testUserMetricsOnly(self):
    self._MockRequest(self.example_metrics + self.user_metrics)
    self.Run('beta dataflow metrics list --source=user ' + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context: {}
  name: my-metric
  origin: user
scalar: 1337.0
updateTime: '2015-01-15 12:31:07'
""")

  def testNamedMetricsOnly(self):
    self._MockRequest(self.example_metrics + self.user_metrics)
    self.Run('beta dataflow metrics list --filter=\'name.name~ElementCount\' '
             + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context:
    output_user_name: some/transform/Read-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
""")

  def testExactTransform(self):
    self._MockRequest(self.example_metrics + self.user_metrics)
    self.Run('beta dataflow metrics list --transform=BigQueryIO.Read3-out0 ' +
             self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
""")

  def testPrefixTransform(self):
    self._MockRequest(self.example_metrics + self.user_metrics)
    self.Run('beta dataflow metrics list --transform=some/transform ' +
             self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context:
    output_user_name: some/transform/Read-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Write-out0
  name: MeanByteCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
""")

  def testRegexTransform(self):
    self._MockRequest(self.example_metrics + self.user_metrics)
    self.Run('beta dataflow metrics list --transform=.*out ' + self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context:
    output_user_name: some/transform/Read-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Write-out0
  name: MeanByteCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
""")

  def testChangedAfterAll(self):
    self._MockRequest(
        self.example_metrics, start_time=times.FormatDateTime(
            times.ParseDateTime('2000-01-01 00:00:00')))
    self.Run(
        'beta dataflow metrics list %s --changed-after="2000-01-01 00:00:00"' %
        self.job_id)
    self.AssertOutputEquals("""\
---
name:
  context: {}
  name: s5-ByteCount
  origin: dataflow/v1b3
scalar: 130194921.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: s05-s5-finish-msecs
  origin: dataflow/v1b3
scalar: 0.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Read-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: some/transform/Write-out0
  name: MeanByteCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context:
    output_user_name: BigQueryIO.Read3-out0
  name: ElementCount
  origin: dataflow/v1b3
scalar: 164656.0
updateTime: '2015-01-15 12:31:07'
---
name:
  context: {}
  name: BigQueryIO.Read3-out0-MeanByteCount
  origin: dataflow/v1b3
scalar: 77.0
updateTime: '2015-01-15 12:31:07'
""")

  def testChangedAfterNone(self):
    self._MockRequest(
        self.example_metrics, start_time=times.FormatDateTime(
            times.ParseDateTime('2100-01-01 00:00:00')))
    self.Run(
        'beta dataflow metrics list %s --changed-after="2100-01-01 00:00:00"' %
        self.job_id)
    self.AssertOutputEquals("""\
""")

  def testListMetricsFailure(self):
    request_class = (
        base.MESSAGE_MODULE.DataflowProjectsLocationsJobsGetMetricsRequest)
    request = request_class(
        projectId=self.Project(), jobId=JOB_1_ID, location=base.DEFAULT_REGION)
    self.mocked_client.projects_locations_jobs.GetMetrics.Expect(
        request=request, exception=http_error.MakeHttpError(500, 'Failure'))
    with self.AssertRaisesHttpExceptionRegexp(r'Failure'):
      self.Run('beta dataflow metrics list ' + JOB_1_ID)

  def testListMetricsHideCommittedAndTentative(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidExclusionException,
        r'Cannot exclude both tentative and committed metrics.'.format(
            normalize_space=True)):
      self.Run('beta dataflow metrics list %s --hide-committed ' % JOB_1_ID)

  def _MockRequest(self,
                   metrics,
                   start_time=None,
                   metric_time=None,
                   region=None):
    region = region or base.DEFAULT_REGION

    request_class = (
        base.MESSAGE_MODULE.DataflowProjectsLocationsJobsGetMetricsRequest)
    request = request_class(
        projectId=self.Project(),
        jobId=self.job_id,
        startTime=start_time,
        location=region)
    response = base.MESSAGE_MODULE.JobMetrics(
        metrics=metrics, metricTime=metric_time)
    self.mocked_client.projects_locations_jobs.GetMetrics.Expect(
        request=request, response=response)

  def _Metric(self,
              name,
              value,
              props=None,
              origin='dataflow/v1b3',
              update_time=None):
    msg = base.MESSAGE_MODULE
    context = msg.MetricStructuredName.ContextValue(additionalProperties=[
        msg.MetricStructuredName.ContextValue.AdditionalProperty(
            key=k, value=v) for (k, v) in six.iteritems((props or {}))
    ])

    if not update_time:
      update_time = '2015-01-15 12:31:07'

    scalar = extra_types.JsonValue()
    if isinstance(value, int):
      scalar = extra_types.JsonValue(integer_value=value)
    elif isinstance(value, float):
      scalar = extra_types.JsonValue(double_value=value)
    elif isinstance(value, str):
      scalar = extra_types.JsonValue(string_value=value)

    return msg.MetricUpdate(
        name=msg.MetricStructuredName(
            origin=origin, name=name, context=context),
        updateTime=update_time,
        scalar=scalar)


if __name__ == '__main__':
  test_case.main()
