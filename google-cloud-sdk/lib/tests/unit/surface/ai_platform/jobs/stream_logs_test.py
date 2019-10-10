# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""ai-platform jobs stream-logs tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
from dateutil import tz

from googlecloudsdk.command_lib.logs import stream
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base

import mock

LogSeverity = collections.namedtuple('LogSeverity', ['name'])


# pylint: disable=invalid-name
class Log(object):
  """Fake log object."""

  def __init__(self,
               timestamp=None,
               severity=None,
               resourceType=None,
               labels=None,
               insertId=None,
               textPayload=None,
               jsonPayload=None,
               protoPayload=None,
               resourceLabels=None):

    class Resource(object):
      """Resources for a log entry."""

      def __init__(self, resourceType=None, labels=None):
        self.labels = labels
        self.type = resourceType

    self.timestamp = timestamp
    self.severity = severity
    self.labels = labels
    self.insertId = insertId
    self.textPayload = textPayload
    self.jsonPayload = jsonPayload
    self.protoPayload = protoPayload
    self.resource = Resource(resourceType, resourceLabels)
# pylint: enable=invalid-name

# TODO(b/36057453): Remove ml_job after transition from ml_job to
# cloudml_job is done. See b/34459608.
_LOG_OUTPUTS_V1 = [
    Log(severity=LogSeverity('INFO'),
        timestamp='2017-01-20T10:28:23Z',
        textPayload='message1',
        resourceType='ml_job',
        labels={
            'ml.googleapis.com/task_name': 'task1',
            'ml.googleapis.com/trial_id': 'trial1'}),
    Log(severity=LogSeverity('DEBUG'),
        timestamp='2017-02-20T10:28:23Z',
        textPayload='message1\nmessage2',
        resourceType='ml_job',
        labels={
            'ml.googleapis.com/task_name': 'task2',
            'ml.googleapis.com/trial_id': 'trial2'}),
    Log(severity=LogSeverity('INFO'),
        timestamp='2017-03-20T10:28:23Z',
        textPayload='message3',
        resourceType='ml_job',
        labels={
            'ml.googleapis.com/task_name': 'task3',
            'ml.googleapis.com/trial_id': 'trial3'}),
    Log(severity=LogSeverity('DEBUG'),
        timestamp='2017-04-20T10:28:23Z',
        textPayload='message4\nmessage4',
        resourceType='ml_job',
        labels={
            'ml.googleapis.com/task_name': 'task4',
            'ml.googleapis.com/trial_id': 'trial4'}),
]

_LOG_OUTPUTS_V2 = [
    Log(severity=LogSeverity('INFO'),
        timestamp='2017-01-20T10:28:23Z',
        textPayload='message1',
        resourceType='ml_job',
        resourceLabels={'task_name': 'task1'},
        labels={'trial_id': 'trial1'}),
    Log(severity=LogSeverity('DEBUG'),
        timestamp='2017-02-20T10:28:23Z',
        textPayload='message1\nmessage2',
        resourceType='ml_job',
        resourceLabels={'task_name': 'task2'},
        labels={'trial_id': 'trial2'}),
    Log(severity=LogSeverity('INFO'),
        timestamp='2017-03-20T10:28:23Z',
        textPayload='message3',
        resourceType='ml_job',
        resourceLabels={'task_name': 'task3'},
        labels={'trial_id': 'trial3'}),
    Log(severity=LogSeverity('DEBUG'),
        timestamp='2017-04-20T10:28:23Z',
        textPayload='message4\nmessage4',
        resourceLabels={'task_name': 'task4'},
        resourceType='ml_job',
        labels={'trial_id': 'trial4'})
]


# For a test of log fetcher, see tests/unit/command_lib/logs/stream_test.py.
# For a test of ML Engine log utilities, see
# tests/unit/command_lib/ml_engine/log_test.py.
@parameterized.parameters('ml-engine', 'ai-platform')
class StreamLogsTestGA(base.MlGaPlatformTestBase):
  """Tests {}jobs stream-logs' command."""

  def SetUp(self):
    self.SetUpOutputs(_LOG_OUTPUTS_V1)

  def SetUpOutputs(self, outputs):
    self.log_fetcher_mock = mock.Mock()
    self.log_fetcher_constructor_mock = self.StartObjectPatch(
        stream, 'LogFetcher', return_value=self.log_fetcher_mock)
    self.log_fetcher_mock.YieldLogs.return_value = iter(outputs)
    self.StartPatch('googlecloudsdk.core.util.times.LOCAL', tz.tzutc())

  def testStreamLogs(self, module_name):
    self.Run(
        '{} jobs stream-logs myjob --allow-multiline-logs'.format(module_name))

    self.AssertOutputEquals(
        """\
          INFO\t 2017-01-20 10:28:23 +0000\t task1\t trial1\t message1
          DEBUG\t 2017-02-20 10:28:23 +0000\t task2\t trial2\t message1
          message2
          INFO\t 2017-03-20 10:28:23 +0000\t task3\t trial3\t message3
          DEBUG\t 2017-04-20 10:28:23 +0000\t task4\t trial4\t message4
          message4
        """,
        normalize_space=True)
    self.log_fetcher_constructor_mock.assert_called_once_with(
        continue_func=mock.ANY,
        filters=['(resource.type="ml_job" OR resource.type="cloudml_job")',
                 'resource.labels.job_id="myjob"'],
        polling_interval=60, continue_interval=10)

  def testStreamLogs_PollingIntervalProperty(self, module_name):
    properties.VALUES.ml_engine.polling_interval.Set(10)

    self.Run(
        '{} jobs stream-logs myjob --allow-multiline-logs'.format(module_name))
    self.log_fetcher_constructor_mock.assert_called_once_with(
        continue_func=mock.ANY,
        filters=['(resource.type="ml_job" OR resource.type="cloudml_job")',
                 'resource.labels.job_id="myjob"'],
        polling_interval=10, continue_interval=10)

  def testStreamLogs_PollingIntervalFlag(self, module_name):
    self.Run('{} jobs stream-logs myjob --allow-multiline-logs '
             '--polling-interval 20'.format(module_name))
    self.log_fetcher_constructor_mock.assert_called_once_with(
        continue_func=mock.ANY,
        filters=['(resource.type="ml_job" OR resource.type="cloudml_job")',
                 'resource.labels.job_id="myjob"'],
        polling_interval=20, continue_interval=10)

  def testStreamLogsSingleLine(self, module_name):
    self.Run('{} jobs stream-logs myjob'.format(module_name))

    self.AssertOutputEquals(
        """\
          INFO\t 2017-01-20 10:28:23 +0000\t task1\t trial1\t message1
          DEBUG\t 2017-02-20 10:28:23 +0000\t task2\t trial2\t message1
          DEBUG\t 2017-02-20 10:28:23 +0000\t task2\t trial2\t message2
          INFO\t 2017-03-20 10:28:23 +0000\t task3\t trial3\t message3
          DEBUG\t 2017-04-20 10:28:23 +0000\t task4\t trial4\t message4
          DEBUG\t 2017-04-20 10:28:23 +0000\t task4\t trial4\t message4
        """,
        normalize_space=True)
    self.log_fetcher_constructor_mock.assert_called_once_with(
        continue_func=mock.ANY,
        filters=['(resource.type="ml_job" OR resource.type="cloudml_job")',
                 'resource.labels.job_id="myjob"'],
        polling_interval=60, continue_interval=10)


class StreamLogsV2TestGA(StreamLogsTestGA):

  def SetUp(self):
    StreamLogsTestGA.SetUpOutputs(self, _LOG_OUTPUTS_V2)


class StreamLogsTestBeta(base.MlBetaPlatformTestBase, StreamLogsTestGA):

  def SetUp(self):
    StreamLogsTestGA.SetUpOutputs(self, _LOG_OUTPUTS_V1)


class StreamLogsTestAlpha(base.MlAlphaPlatformTestBase, StreamLogsTestBeta):

  def SetUp(self):
    StreamLogsTestGA.SetUpOutputs(self, _LOG_OUTPUTS_V1)


if __name__ == '__main__':
  test_case.main()
