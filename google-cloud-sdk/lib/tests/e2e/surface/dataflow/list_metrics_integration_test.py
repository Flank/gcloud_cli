# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Integration test for the 'dataflow metrics list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.dataflow import e2e_base

REGION = 'europe-west1'


class ListMetricsIntegrationTest(e2e_base.DataflowIntegrationTestBase):
  """Integration test for the 'dataflow metrics list' command.

  Dataflow requires the Apache Beam Java (or python) SDK in order to create a
  job and there is no API to create a job. This means for user facing code
  like the UI and the CLI there is no way to create a job; thre needs to be a
  project that already has the Dataflow jobs. All jobs are kept in the
  'dataflow-monitoring' project. This is an external project that only the
  Dataflow team has access to this. For every CLI integration test, do a
  'gcloud config set project dataflow-monitoring' to be in the proper project.
  """

  def testListMetrics(self):
    job = self.FindOldTerminatedJob()
    metrics = self.ListMetrics(job.id)
    self.assertGreater(len(metrics), 0)
    for metric in metrics:
      # Do we have a name and a value?
      self.assertIsNotNone(metric.name, 'Metric missing a name: %s' % metric)
      self.assertTrue(metric.scalar or metric.distribution,
                      'Metric missing a value: %s' % metric.name)

      # Proper origin types.
      self.assertIn(metric.name.origin, ['dataflow/v1b3', 'user'])

  def testListMetricsWithRegion(self):
    try:
      job = self.FindOldTerminatedJob(region=REGION)
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')
    metrics = self.ListMetrics(job.id, region=REGION)
    self.assertGreater(len(metrics), 0)
    for metric in metrics:
      # Do we have a name and a value?
      self.assertIsNotNone(metric.name, 'Metric missing a name: %s' % metric)
      self.assertTrue(metric.scalar or metric.distribution,
                      'Metric missing a value: %s' % metric.name)

      # Proper origin types.
      self.assertIn(metric.name.origin, ['dataflow/v1b3', 'user'])

  def testListMetricsServiceSource(self):
    job = self.FindOldTerminatedJob()
    metrics = self.ListMetrics(job.id, 'service')
    self.assertGreater(len(metrics), 0)
    for metric in metrics:
      # Do we have a name and a value?
      self.assertIsNotNone(metric.name, 'Metric missing a name: %s' % metric)
      self.assertTrue(metric.scalar or metric.distribution,
                      'Metric missing a value: %s' % metric.name)

      # Proper origin types.
      self.assertEqual(metric.name.origin, 'dataflow/v1b3')


if __name__ == '__main__':
  test_case.main()
