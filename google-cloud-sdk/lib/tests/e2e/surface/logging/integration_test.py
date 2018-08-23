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

"""Integration tests for Cloud Logging commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.logging import base


class LoggingIntegrationTest(base.LoggingIntegrationTestBase):
  """Test commands that operate on sinks."""

  def PreSetUp(self):
    # This is required to disable the use of service account. Service accounts
    # do not have OWNER permission, which some tested commands require.
    self.requires_refresh_token = True

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='logging', sequence_start=1)

    self._parents_and_flags = [
        ('projects/{0}'.format(self.Project()), ''),
        ('organizations/961309089256', '--organization=961309089256'),
        ('folders/79536718298', '--folder=79536718298')]

  def testLogMetrics(self):
    metric_name = next(self._name_generator)

    def FindMetric():
      """Get the list of metrics, and check if metric_name is on the list."""
      metrics = self.RunLogging('metrics list')
      return any(metric_name in metric.name for metric in metrics)

    try:
      metric = self.RunLogging(
          'metrics create {0} --description=hello '
          '--log-filter=severity=WARNING'.format(metric_name))
      self.assertEqual(metric_name, metric.name)

      metric = self.RunLogging('metrics describe {0}'.format(metric_name))
      self.assertEqual(metric_name, metric.name)

      self.assertTrue(FindMetric())
    finally:
      self.RunLogging('metrics delete {0}'.format(metric_name))

    self.assertFalse(FindMetric())

  def testSinks(self):
    def FindSink(sink_name, flag):
      """Get the list of sinks, and check if sink_name is on the list."""
      sinks = self.RunLogging('sinks list {0}'.format(flag))
      return any(sink_name in sink.name for sink in sinks)

    destination = ('bigquery.googleapis.com/projects/{0}/datasets/my-dataset'
                   .format(self.Project()))
    sink_filter = 'logName=test'

    for _, flag in self._parents_and_flags:
      sink_name = next(self._name_generator)

      try:
        # TODO(b/36050234): Add cleanup for non-project sinks.
        sink = self.RunLogging(
            'sinks create {0} {1} --log-filter={2} {3}'.format(
                sink_name, destination, sink_filter, flag))
        self.assertEqual(sink_name, sink.name)

        sink = self.RunLogging('sinks describe {0} {1}'.format(sink_name, flag))
        self.assertEqual(sink_name, sink.name)

        self.assertTrue(FindSink(sink_name, flag))
      finally:
        self.RunLogging('sinks delete {0} {1}'.format(sink_name, flag))

        self.assertFalse(FindSink(sink_name, flag))

  def testLogEntries(self):
    def FindLogEntry(parent, log_id, flag):
      """Try to read one of the entries we just wrote."""
      log_filter = 'logName={0}/logs/{1}'.format(parent, log_id)
      entry = self.RunLogging(
          'read {0} --freshness=1h --limit=1 {1}'.format(
              log_filter, flag))
      return any(entry)

    for parent, flag in self._parents_and_flags:
      log_id = next(self._name_generator)

      self.RunLogging('write {0} hello {1}'.format(log_id, flag))
      self.RunLogging(
          'write {0} urgent_hello --severity=ERROR {1}'.format(log_id, flag))
      self.RunLogging('write %s \'{"a": "hello"}\' --payload-type=json %s'
                      % (log_id, flag))

      try:
        # Total retry time of 120 sec.
        retries_ms = (15000, 30000, 30000, 45000)
        # Retry if log id was not found, it should be visible shortly after
        # the "write" command.
        retry.Retryer().RetryOnResult(
            FindLogEntry, args=[parent, log_id, flag], should_retry_if=False,
            sleep_ms=retries_ms)
      except retry.MaxRetrialsException:
        raise Exception('Retry limit exceeded. Note that this test relies on '
                        'Bigtable replication and may occasionally be flaky')


if __name__ == '__main__':
  test_case.main()
