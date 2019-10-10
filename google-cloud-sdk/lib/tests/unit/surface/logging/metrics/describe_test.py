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

"""Tests of the 'metrics' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class MetricsGetTest(base.LoggingTestBase):

  def testGet(self):
    test_metric = util.GetMessages().LogMetric(
        name='my-metric',
        description='my-metric description',
        filter='my-metric filter')
    self.mock_client_v2.projects_metrics.Get.Expect(
        util.GetMessages().LoggingProjectsMetricsGetRequest(
            metricName='projects/my-project/metrics/my-metric'),
        test_metric)
    self.RunLogging('metrics describe my-metric')
    self.AssertOutputContains(test_metric.name)
    self.AssertOutputContains(test_metric.description)
    self.AssertOutputContains(test_metric.filter)

  def testGetNoPerms(self):
    self.mock_client_v2.projects_metrics.Get.Expect(
        util.GetMessages().LoggingProjectsMetricsGetRequest(
            metricName='projects/my-project/metrics/my-metric'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('metrics describe my-metric')

  def testGetNoProject(self):
    self.RunWithoutProject('metrics describe my-metric')

  def testGetNoAuth(self):
    self.RunWithoutAuth('metrics describe my-metric')


if __name__ == '__main__':
  test_case.main()
