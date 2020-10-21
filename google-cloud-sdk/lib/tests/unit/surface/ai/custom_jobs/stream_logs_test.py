# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.ai.custom_jobs.stream_logs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.py import extra_types
from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.logs import stream
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock

_LogSeverity = collections.namedtuple('LogSeverity', ['name'])


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
    self.resource = Resource(resourceType, resourceLabels)


_LOG_OUTPUTS_WITH_RESOURCE_LABEL = [
    Log(severity=_LogSeverity('INFO'),
        timestamp='2017-01-20T10:28:23',
        textPayload='message1',
        resourceType='ml_job',
        resourceLabels={'task_name': 'task1'}),
    Log(severity=_LogSeverity('DEBUG'),
        timestamp='2017-02-20T10:28:23',
        textPayload='message1\nmessage2',
        resourceType='ml_job',
        resourceLabels={'task_name': 'task2'}),
    Log(severity=_LogSeverity('INFO'),
        timestamp='2017-03-20T10:28:23',
        textPayload='message3',
        resourceType='ml_job',
        resourceLabels={'task_name': 'task3'}),
    Log(severity=_LogSeverity('DEBUG'),
        timestamp='2017-04-20T10:28:23',
        textPayload='message4\nmessage4',
        resourceType='ml_job',
        resourceLabels={'task_name': 'task4'})
]


class StreamLogsCustomJobUnitTestAlpha(cli_test_base.CliTestBase,
                                       sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.region = 'us-central1'
    self.version = 'alpha'
    self.logging_msgs = apis.GetMessagesModule('logging', 'v2')
    self.messages = apis.GetMessagesModule('aiplatform', 'v1beta1')
    self.mock_client = api_mock.Client(
        apis.GetClientClass('aiplatform', 'v1beta1'),
        real_client=apis.GetClientInstance(
            'aiplatform', 'v1beta1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.SetUpOutputs(_LOG_OUTPUTS_WITH_RESOURCE_LABEL)

  def SetUpOutputs(self, outputs):
    self.log_fetcher_mock = mock.Mock()
    self.log_fetcher_constructor_mock = self.StartObjectPatch(
        stream, 'LogFetcher', return_value=self.log_fetcher_mock)
    self.log_fetcher_mock.YieldLogs.return_value = iter(outputs)

  def RunCommand(self, *command):
    return self.Run([self.version, 'ai', 'custom-jobs'] + list(command))

  def _BuildCustomJob(
      self,
      name='projects/fake-project/locations/us-central1/customJobs/1',
      replica_count=1,
      machine_type=u'n1-highmem-2',
      container_uri=u'gcr.io/ucaip-test/ucaip-training-test',
      display_name=u'DescribeCustomJobUnitTest'):
    worker_pool_spec = self.messages.GoogleCloudAiplatformV1beta1WorkerPoolSpec(
    )
    worker_pool_spec.replicaCount = replica_count
    worker_pool_spec.machineSpec = self.messages.GoogleCloudAiplatformV1beta1MachineSpec(
        machineType=machine_type)
    worker_pool_spec.containerSpec = self.messages.GoogleCloudAiplatformV1beta1ContainerSpec(
        imageUri=container_uri)
    job_spec = self.messages.GoogleCloudAiplatformV1beta1CustomJobSpec(
        workerPoolSpecs=[worker_pool_spec])
    return self.messages.GoogleCloudAiplatformV1beta1CustomJob(
        name=name, displayName=display_name, jobSpec=job_spec)

  @test_case.Filters.SkipInRpmPackage('Wrong UTC offset', 'b/170708598')
  @test_case.Filters.SkipInDebPackage('Wrong UTC offset', 'b/170708598')
  def testStreamLogCustomJob(self):
    request = self.messages.AiplatformProjectsLocationsCustomJobsGetRequest(
        name='projects/{}/locations/{}/customJobs/{}'.format(
            'fake-project', 'us-central1', '1'))
    expected_response = self._BuildCustomJob()
    expected_response.endTime = '2020-10-07T22:49:45.431231Z'
    self.mock_client.projects_locations_customJobs.Get.Expect(
        request, response=expected_response)

    self.RunCommand('stream-logs', '1', '--region={}'.format(self.region))

    self.AssertOutputEquals(
        """\
          INFO\t 2017-01-20 10:28:23 -0800\t task1\t message1
          DEBUG\t 2017-02-20 10:28:23 -0800\t task2\t message1
          DEBUG\t 2017-02-20 10:28:23 -0800\t task2\t message2
          INFO\t 2017-03-20 10:28:23 -0700\t task3\t message3
          DEBUG\t 2017-04-20 10:28:23 -0700\t task4\t message4
          DEBUG\t 2017-04-20 10:28:23 -0700\t task4\t message4
        """,
        normalize_space=True)
    self.log_fetcher_constructor_mock.assert_called_once_with(
        filters=['resource.type="ml_job"', 'resource.labels.job_id="1"'],
        polling_interval=60,
        continue_interval=10,
        continue_func=mock.ANY)

  @test_case.Filters.SkipInRpmPackage('Wrong UTC offset', 'b/170708598')
  @test_case.Filters.SkipInDebPackage('Wrong UTC offset', 'b/170708598')
  def testStreamLogCustomJobWithTaskName(self):
    request = self.messages.AiplatformProjectsLocationsCustomJobsGetRequest(
        name='projects/{}/locations/{}/customJobs/{}'.format(
            'fake-project', 'us-central1', '1'))
    expected_response = self._BuildCustomJob()
    expected_response.endTime = '2020-10-07T22:49:45.431231Z'
    self.mock_client.projects_locations_customJobs.Get.Expect(
        request, response=expected_response)
    self.log_fetcher_mock.YieldLogs.return_value = iter([
        Log(severity=_LogSeverity('DEBUG'),
            timestamp='2017-04-20T10:28:23',
            textPayload='message4\nmessage4',
            resourceType='ml_job',
            resourceLabels={'task_name': 'task4'})
    ])

    self.RunCommand('stream-logs', '1', '--region={}'.format(self.region),
                    '--task-name=task4')

    self.AssertOutputEquals(
        """\
          DEBUG\t 2017-04-20 10:28:23 -0700\t task4\t message4
          DEBUG\t 2017-04-20 10:28:23 -0700\t task4\t message4
        """,
        normalize_space=True)
    self.log_fetcher_constructor_mock.assert_called_once_with(
        filters=[
            'resource.type="ml_job"', 'resource.labels.job_id="1"',
            'resource.labels.task_name="task4"'
        ],
        polling_interval=60,
        continue_interval=10,
        continue_func=mock.ANY)

  def testStreamLogCustomJobWithPollingInterval(self):
    request = self.messages.AiplatformProjectsLocationsCustomJobsGetRequest(
        name='projects/{}/locations/{}/customJobs/{}'.format(
            'fake-project', 'us-central1', '1'))
    expected_response = self._BuildCustomJob()
    expected_response.endTime = '2020-10-07T22:49:45.431231Z'
    self.mock_client.projects_locations_customJobs.Get.Expect(
        request, response=expected_response)

    self.RunCommand('stream-logs', '1', '--region={}'.format(self.region),
                    '--polling-interval=20')

    self.log_fetcher_constructor_mock.assert_called_once_with(
        filters=['resource.type="ml_job"', 'resource.labels.job_id="1"'],
        polling_interval=20,
        continue_interval=10,
        continue_func=mock.ANY)

  @test_case.Filters.SkipInRpmPackage('Wrong UTC offset', 'b/170708598')
  @test_case.Filters.SkipInDebPackage('Wrong UTC offset', 'b/170708598')
  def testStreamLogCustomJobWithAllowMultipleLine(self):
    request = self.messages.AiplatformProjectsLocationsCustomJobsGetRequest(
        name='projects/{}/locations/{}/customJobs/{}'.format(
            'fake-project', 'us-central1', '1'))
    expected_response = self._BuildCustomJob()
    expected_response.endTime = '2020-10-07T22:49:45.431231Z'
    self.mock_client.projects_locations_customJobs.Get.Expect(
        request, response=expected_response)

    self.RunCommand('stream-logs', '1', '--region={}'.format(self.region),
                    '--allow-multiline-logs')

    self.AssertOutputEquals(
        """\
          INFO\t 2017-01-20 10:28:23 -0800\t task1\t message1
          DEBUG\t 2017-02-20 10:28:23 -0800\t task2\t message1\nmessage2
          INFO\t 2017-03-20 10:28:23 -0700\t task3\t message3
          DEBUG\t 2017-04-20 10:28:23 -0700\t task4\t message4\nmessage4
        """,
        normalize_space=True)
    self.log_fetcher_constructor_mock.assert_called_once_with(
        filters=['resource.type="ml_job"', 'resource.labels.job_id="1"'],
        polling_interval=60,
        continue_interval=10,
        continue_func=mock.ANY)

  @test_case.Filters.SkipInRpmPackage('Wrong UTC offset', 'b/170708598')
  @test_case.Filters.SkipInDebPackage('Wrong UTC offset', 'b/170708598')
  def testStreamLogCustomJobWithJsonPayload(self):
    request = self.messages.AiplatformProjectsLocationsCustomJobsGetRequest(
        name='projects/{}/locations/{}/customJobs/{}'.format(
            'fake-project', 'us-central1', '1'))
    expected_response = self._BuildCustomJob()
    expected_response.endTime = '2020-10-07T22:49:45.431231Z'
    self.mock_client.projects_locations_customJobs.Get.Expect(
        request, response=expected_response)
    json_payload = self.logging_msgs.LogEntry.JsonPayloadValue()
    json_payload.additionalProperties = [
        self.logging_msgs.LogEntry.JsonPayloadValue.AdditionalProperty(
            key='message',
            value=extra_types.JsonValue(string_value='json_message'))
    ]
    self.log_fetcher_mock.YieldLogs.return_value = iter([
        Log(severity=_LogSeverity('DEBUG'),
            timestamp='2017-04-20T10:28:23',
            textPayload='message4\nmessage4',
            resourceType='ml_job',
            resourceLabels={'task_name': 'task4'},
            jsonPayload=json_payload)
    ])

    self.RunCommand('stream-logs', '1', '--region={}'.format(self.region))

    self.AssertOutputEquals(
        """\
          DEBUG\t 2017-04-20 10:28:23 -0700\t task4\t json_message
        """,
        normalize_space=True)
    self.log_fetcher_constructor_mock.assert_called_once_with(
        filters=['resource.type="ml_job"', 'resource.labels.job_id="1"'],
        polling_interval=60,
        continue_interval=10,
        continue_func=mock.ANY)


class StreamLogsCustomJobUnitTestBeta(StreamLogsCustomJobUnitTestAlpha):

  def SetUp(self):
    self.version = 'beta'


if __name__ == '__main__':
  test_case.main()
