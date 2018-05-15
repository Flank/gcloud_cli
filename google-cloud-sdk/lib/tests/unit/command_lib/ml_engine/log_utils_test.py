# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the ML Engine log utilities library."""
from __future__ import absolute_import
from __future__ import unicode_literals
import collections

from googlecloudsdk.command_lib.ml_engine import log_utils
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


LogSeverity = collections.namedtuple('LogSeverity', ['name'])


# pylint: disable=invalid-name
class Log(object):
  """Fake log object."""

  def __init__(self,
               timestamp=None,
               severity=None,
               labels=None,
               insertId=None,
               textPayload=None,
               jsonPayload=None,
               protoPayload=None,
               resourceLabels=None):

    class Resource(object):
      """Resources for a log entry."""

      def __init__(self, labels=None):
        self.labels = labels

    self.timestamp = timestamp
    self.severity = severity
    self.labels = labels
    self.insertId = insertId
    self.textPayload = textPayload
    self.jsonPayload = jsonPayload
    self.protoPayload = protoPayload
    self.resource = Resource(resourceLabels)
# pylint: enable=invalid-name


class LogUtilsTest(base.MlGaPlatformTestBase):

  def SetUp(self):
    properties.VALUES.core.project.Set('proj')

  def _GetGenerator(self, items):
    """Returns a function that is a generator over items."""
    return iter(items)

  def testLogFilters(self):
    filters = log_utils.LogFilters('job1')
    self.assertIn('(resource.type="ml_job" OR resource.type="cloudml_job")',
                  filters)
    self.assertIn('resource.labels.job_id="job1"', filters)

  def testLogFiltersWithTask(self):
    filters = log_utils.LogFilters('job1', task_name='task1')
    self.assertIn('(resource.type="ml_job" OR resource.type="cloudml_job")',
                  filters)
    self.assertIn('resource.labels.job_id="job1"', filters)
    self.assertIn(
        '(resource.labels.task_name="task1" OR labels.task_name="task1")',
        filters)

  def testMakeContinueFunction(self):
    response1 = self.short_msgs.Job(endTime=None)
    response2 = self.short_msgs.Job(
        endTime='2017-01-20T17:28:19.002754Z')
    # Job is completed after the second check.
    self.client.projects_jobs.Get.Expect(
        request=self.msgs.MlProjectsJobsGetRequest(
            name='projects/proj/jobs/job1'),
        response=response1)
    self.client.projects_jobs.Get.Expect(
        request=self.msgs.MlProjectsJobsGetRequest(
            name='projects/proj/jobs/job1'),
        response=response2)

    should_continue = log_utils.MakeContinueFunction('job1')
    # Tests that we should always continue when we've had < 1 empty poll.
    self.assertTrue(should_continue(0))
    self.assertTrue(should_continue(1))
    # Tests that we should continue if job is still running
    self.assertTrue(should_continue(2))
    # Tests that we should stop after 2 empty polls and a finished job.
    self.assertFalse(should_continue(2))

  def testSplitMultilineWithOneLine(self):
    log_entry = Log(textPayload='foo',
                    severity=LogSeverity('INFO'),
                    timestamp='2017-01-20T17:28:19.002754Z')
    log_dict = {'message': 'foo',
                'severity': 'INFO',
                'task_name': 'unknown_task',
                'timestamp': '2017-01-20T17:28:19.002754Z'}
    log_generator = self._GetGenerator([log_entry])
    generator = log_utils.SplitMultiline(log_generator)
    self.assertEqual(log_dict, next(generator))
    with self.assertRaises(StopIteration):
      next(generator)

  def testSplitMultilineWithTwoLines(self):
    log_entry = Log(textPayload='foo\nfoo2',
                    severity=LogSeverity('INFO'),
                    timestamp='2017-01-20T17:28:19.002754Z')
    log_dict1 = {'message': 'foo',
                 'severity': 'INFO',
                 'task_name': 'unknown_task',
                 'timestamp': '2017-01-20T17:28:19.002754Z'}
    log_dict2 = {'message': 'foo2',
                 'severity': 'INFO',
                 'task_name': 'unknown_task',
                 'timestamp': '2017-01-20T17:28:19.002754Z'}
    log_generator = self._GetGenerator([log_entry])
    generator = log_utils.SplitMultiline(log_generator)
    self.assertEqual(log_dict1, next(generator))
    self.assertEqual(log_dict2, next(generator))
    with self.assertRaises(StopIteration):
      next(generator)

  def testSplitMultilineWrapper(self):
    log_entry = Log(textPayload='foo\nfoo2',
                    severity=LogSeverity('INFO'),
                    timestamp='2017-01-20T17:28:19.002754Z')
    log_dict = {'message': 'foo\nfoo2',
                'severity': 'INFO',
                'task_name': 'unknown_task',
                'timestamp': '2017-01-20T17:28:19.002754Z',}
    log_generator = self._GetGenerator([log_entry])
    generator = log_utils.SplitMultiline(log_generator, allow_multiline=True)
    self.assertEqual(log_dict, next(generator))
    with self.assertRaises(StopIteration):
      next(generator)

  def testFormatBasicLog(self):
    log_entry = Log(
        timestamp='2016-09-20T17:28:23.929735908Z',
        severity=LogSeverity('INFO'),
        labels={
            'ml.googleapis.com/task_name': 'my_task',
            'ml.googleapis.com/trial_id': 'my_trial'
        },
        textPayload='foo',
        insertId='foo')
    log_dict = {
        'timestamp': '2016-09-20T17:28:23.929735908Z',
        'severity': 'INFO',
        'task_name': 'my_task',
        'trial_id': 'my_trial',
        'message': 'foo'
    }
    self.assertEqual(log_utils._EntryToDict(log_entry), log_dict)

    log_entry = Log(
        timestamp='2016-09-20T17:28:23.929735908Z',
        severity=LogSeverity('INFO'),
        labels={'trial_id': 'my_trial'},
        resourceLabels={
            'task_name': 'my_task',
        },
        textPayload='foo',
        insertId='foo')
    log_dict = {
        'timestamp': '2016-09-20T17:28:23.929735908Z',
        'severity': 'INFO',
        'task_name': 'my_task',
        'trial_id': 'my_trial',
        'message': 'foo'
    }
    self.assertEqual(log_utils._EntryToDict(log_entry), log_dict)

  def testFormatLogWithoutLabels(self):
    log_entry = Log(
        timestamp='2016-09-20T17:28:23.929735908Z',
        severity=LogSeverity('INFO'),
        textPayload='no_label',
        insertId='foo3'
    )
    log_dict = {
        'timestamp': '2016-09-20T17:28:23.929735908Z',
        'severity': 'INFO',
        'task_name': 'unknown_task',
        'message': 'no_label',

    }
    self.assertEqual(log_utils._EntryToDict(log_entry), log_dict)

  def testFormatLogWithJsonPayload(self):
    log_entry = Log(
        timestamp='2016-09-20T17:28:24.929735908Z',
        severity=LogSeverity('WARN'),
        labels={
            'ml.googleapis.com/task_name': 'my_task',
            'ml.googleapis.com/trial_id': 'my_trial'
        },
        jsonPayload={
            'created': 1474392504.00175,
            'levelname': 'INFO',
            'lineno': 676,
            'message': 'Module completed; cleaning up.',
            'pathname': '/runcloudml.py'
        },
        insertId='afoo-bar'
    )
    log_dict = {
        'timestamp': '2016-09-20T17:28:24.929735908Z',
        'severity': 'WARN',
        'task_name': 'my_task',
        'trial_id': 'my_trial',
        'message': 'Module completed; cleaning up.',
        'json': {
            'created': 1474392504.00175,
            'lineno': 676,
            'pathname': '/runcloudml.py'
        }
    }
    self.assertEqual(log_utils._EntryToDict(log_entry), log_dict)

  def testFormatLogWithNoneJsonPayload(self):
    log_entry = Log(
        timestamp='2016-09-20T17:29:23.929735908Z',
        severity=LogSeverity('DEBUG'),
        labels={
            'ml.googleapis.com/trial_id': 'my_trial3'
        },
        jsonPayload=None,
        insertId='abc124'
    )
    log_dict = {
        'timestamp': '2016-09-20T17:29:23.929735908Z',
        'severity': 'DEBUG',
        'trial_id': 'my_trial3',
        'task_name': 'unknown_task',
        'message': ''
    }
    self.assertEqual(log_utils._EntryToDict(log_entry), log_dict)

  def testFormatLogWithNoneTextPayload(self):
    log_entry = Log(
        timestamp='2016-09-20T17:29:24.929735908Z',
        severity=LogSeverity('WARN'),
        labels={
            'ml.googleapis.com/trial_id': 'my_trial3'
        },
        textPayload=None,
        jsonPayload={
            'message': None,
        },
        insertId='abc125'
    )
    log_dict = {
        'timestamp': '2016-09-20T17:29:24.929735908Z',
        'severity': 'WARN',
        'trial_id': 'my_trial3',
        'task_name': 'unknown_task',
        'message': '',
        'json': {}
    }
    self.assertEqual(log_utils._EntryToDict(log_entry), log_dict)


if __name__ == '__main__':
  test_case.main()
