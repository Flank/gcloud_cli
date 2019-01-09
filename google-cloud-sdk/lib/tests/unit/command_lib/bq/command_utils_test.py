# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""dlp hooks tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.bq import command_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class BqPollerTest(waiter_test_base.Base):
  """BqPoller tests."""

  def SetUp(self):
    self.client_class = apis.GetClientClass('bigquery', 'v2')
    self.client = mock.Client(self.client_class,
                              real_client=apis.GetClientInstance(
                                  'bigquery', 'v2', no_http=True))
    self.messages = self.client_class.MESSAGES_MODULE
    self._done = self.messages.JobStatus(state='DONE')
    self._pending = self.messages.JobStatus(state='RUNNING')
    self.error_entry = self.messages.ErrorProto
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.job_service = self.client.jobs
    self._result_data = {
        'QUERY': (self.client.jobs,
                  {'jobId': 'myjob', 'projectId': 'fakeproject'}),
        'COPY': (self.client.tables,
                 {'tableId': 'test_table', 'datasetId': 'my_dataset',
                  'projectId': 'fakeproject'}),
        'LOAD': (self.client.tables,
                 {'tableId': 'test_table', 'datasetId': 'my_dataset',
                  'projectId': 'fakeproject'}),
        'OTHER': (self.client.jobs,
                  {'jobId': 'myjob', 'projectId': 'fakeproject'})}

  def ExpectJobResult(self, result_type):
    result_svc, result_req_params = self._result_data[result_type]
    result_request_type = result_svc.GetRequestType('Get')
    result_response_type = result_svc.GetResponseType('Get')

    if result_type == 'QUERY':
      result_request_type = result_svc.GetRequestType('GetQueryResults')
      request = result_request_type(**result_req_params)
      request.maxResults = 1000
      result_response_type = result_svc.GetResponseType('GetQueryResults')
      job_ref = self.messages.JobReference(**result_req_params)
      result = result_response_type(jobReference=job_ref)
      result_svc.GetQueryResults.Expect(
          request=request,
          response=result)
      return result

    if result_type == 'COPY' or result_type == 'LOAD':
      table_ref = self.messages.TableReference(**result_req_params)
      result = result_response_type(tableReference=table_ref)
      result_svc.Get.Expect(
          request=result_request_type(**result_req_params),
          response=result)
    else:
      job_ref = self.messages.JobReference(**result_req_params)
      result = result_response_type(jobReference=job_ref)
      arg_utils.SetFieldInMessage(result, 'configuration.jobType', 'OTHER')
      result.status = self._done

    return result

  def MakeJobReference(self):
    return resources.REGISTRY.Parse('myjob',
                                    params={'projectId': 'fakeproject'},
                                    collection='bigquery.jobs')

  def ExpectJob(self, job_ref, result_type, retries=1, error_msg=None):
    request_type = self.job_service.GetRequestType('Get')
    response_type = self.job_service.GetResponseType('Get')
    response = response_type()
    if result_type == 'COPY':
      arg_utils.SetFieldInMessage(
          response, 'configuration.copy.destinationTable.datasetId',
          'my_dataset')
      arg_utils.SetFieldInMessage(
          response, 'configuration.copy.destinationTable.projectId',
          'fakeproject')
      arg_utils.SetFieldInMessage(
          response, 'configuration.copy.destinationTable.tableId',
          'test_table')
    elif result_type == 'LOAD':
      arg_utils.SetFieldInMessage(
          response, 'configuration.load.destinationTable.datasetId',
          'my_dataset')
      arg_utils.SetFieldInMessage(
          response, 'configuration.load.destinationTable.projectId',
          'fakeproject')
      arg_utils.SetFieldInMessage(
          response, 'configuration.load.destinationTable.tableId',
          'test_table')
    elif result_type == 'QUERY':
      arg_utils.SetFieldInMessage(
          response, 'configuration.query.destinationTable.datasetId',
          'my_dataset')
      arg_utils.SetFieldInMessage(
          response, 'configuration.query.destinationTable.projectId',
          'fakeproject')
      arg_utils.SetFieldInMessage(
          response, 'configuration.query.destinationTable.tableId',
          'test_table')
    else:
      arg_utils.SetFieldInMessage(response, 'configuration.jobType', 'OTHER')

    arg_utils.SetFieldInMessage(response, 'configuration.jobType', result_type)
    arg_utils.SetFieldInMessage(response, 'jobReference.jobId', job_ref.Name())
    arg_utils.SetFieldInMessage(response, 'jobReference.projectId',
                                job_ref.Parent().Name())
    if error_msg:
      response.status = self._done
      response.status.errorResult = self.error_entry(message=error_msg,
                                                     reason='BAD')
      self.job_service.Get.Expect(
          request=request_type(jobId=job_ref.Name(),
                               projectId=job_ref.Parent().Name()),
          response=response)
    else:
      for i in range(retries):
        response.status = (self._pending if i < retries-1 else self._done)
        self.job_service.Get.Expect(
            request=request_type(jobId=job_ref.Name(),
                                 projectId=job_ref.Parent().Name()),
            response=response)
    result = None
    if not error_msg:
      result = self.ExpectJobResult(result_type)

    return result

  def testCopy(self):
    poller = command_utils.BqJobPoller(self.job_service, self.client.tables)
    job_ref = self.MakeJobReference()

    expected = self.ExpectJob(job_ref, 'COPY')
    actual = waiter.WaitFor(poller=poller,
                            operation_ref=job_ref,
                            message='COPYING TABLE')
    self.assertEqual(expected, actual)
    self.AssertOutputEquals('')
    self.AssertErrContains('COPYING TABLE')

  def testLoad(self):
    poller = command_utils.BqJobPoller(self.job_service, self.client.tables)
    job_ref = self.MakeJobReference()

    expected = self.ExpectJob(job_ref, 'LOAD')
    actual = waiter.WaitFor(poller=poller,
                            operation_ref=job_ref,
                            message='LOADING TABLE')
    self.assertEqual(expected, actual)
    self.AssertOutputEquals('')
    self.AssertErrContains('LOADING TABLE')

  def testQuery(self):
    poller = command_utils.BqJobPoller(self.job_service, self.client.jobs)
    job_ref = self.MakeJobReference()

    expected = self.ExpectJob(job_ref, 'QUERY')
    actual = waiter.WaitFor(poller=poller,
                            operation_ref=job_ref,
                            message='RUNNING QUERY')
    self.assertEqual(expected, actual)
    self.AssertOutputEquals('')
    self.AssertErrContains('RUNNING QUERY')

  def testOther(self):
    poller = command_utils.BqJobPoller(self.job_service, self.client.jobs)
    job_ref = self.MakeJobReference()

    expected = self.ExpectJob(job_ref, 'OTHER')
    actual = waiter.WaitFor(poller=poller,
                            operation_ref=job_ref,
                            message='OTHER JOB')
    self.assertEqual(expected, actual)
    self.AssertOutputEquals('')
    self.AssertErrContains('OTHER JOB')

  def testJobErrors(self):
    poller = command_utils.BqJobPoller(self.job_service, self.client.tables)
    job_ref = self.MakeJobReference()

    self.ExpectJob(job_ref, 'COPY', error_msg='FAILED COPY')
    with self.assertRaisesRegexp(waiter.OperationError, r'FAILED COPY'):
      waiter.WaitFor(poller=poller, operation_ref=job_ref,
                     message='COPYING TABLE')
      self.AssertOutputEquals('')
      self.AssertErrContains('FAILURE')

if __name__ == '__main__':
  test_case.main()
