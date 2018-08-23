# -*- coding: utf-8 -*- #
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
"""Unit tests for the client_adapter module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
from apitools.base.py import batch

from googlecloudsdk.api_lib.compute import client_adapter
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
import mock
from six.moves import range  # pylint: disable=redefined-builtin


Payload = collections.namedtuple(
    'Payload', ['is_error', 'exception', 'response'])


class ClientAdapterTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.adapter = client_adapter.ClientAdapter('v1', no_http=True)
    self.client = self.adapter.apitools_client
    self.messages = self.client.MESSAGES_MODULE

  def testBatch_NoRequests(self):
    errors_to_collect = []
    responses = []

    with mock.patch.object(
        batch.BatchApiRequest, 'Execute', return_value=responses):
      result = self.adapter.BatchRequests([], errors_to_collect)

    self.assertEqual([], result)
    self.assertEqual([], errors_to_collect)

  def testBatch_SingleRequest(self):
    requests = [
        (self.client.instances,
         'Get',
         self.messages.ComputeInstancesGetRequest(instance='instance=X',
                                                  zone='zone-X',
                                                  project='project-X'))
    ]
    errors_to_collect = []
    responses = [
        Payload(response='Some response', is_error=False, exception=None)
    ]

    with mock.patch.object(
        batch.BatchApiRequest, 'Execute', return_value=responses):
      result = self.adapter.BatchRequests(requests, errors_to_collect)

    self.assertEqual(len(requests), len(responses))
    self.assertEqual(['Some response'], result)
    self.assertEqual([], errors_to_collect)

  def testBatch_MultipleRequest(self):
    requests = [(self.client.instances, 'Get',
                 self.messages.ComputeInstancesGetRequest(
                     instance='instance=X', zone='zone-X', project='project-X'))
                for i in range(3)]
    errors_to_collect = []
    responses = [
        Payload(
            response='Some response {}'.format(i),
            is_error=False,
            exception=None) for i in range(3)
    ]

    with mock.patch.object(
        batch.BatchApiRequest, 'Execute', return_value=responses):
      result = self.adapter.BatchRequests(requests, errors_to_collect)

    self.assertEqual(['Some response 0', 'Some response 1', 'Some response 2'],
                     result)
    self.assertEqual(len(requests), len(responses))
    self.assertEqual([], errors_to_collect)

  def testBatch_SingleError(self):
    requests = [
        (self.client.instances,
         'Get',
         self.messages.ComputeInstancesGetRequest(instance='instance=X',
                                                  zone='zone-X',
                                                  project='project-X'))
    ]
    instance_ref = resources.REGISTRY.Create(
        'compute.instances',
        project='mickey', zone='disney', instance='Super-Cheese')
    http_err = http_error.MakeHttpError(code=404, url=instance_ref.SelfLink())

    errors_to_collect = []
    responses = [
        Payload(response='Some response',
                is_error=True, exception=http_err)
    ]

    with mock.patch.object(
        batch.BatchApiRequest, 'Execute', return_value=responses):
      result = self.adapter.BatchRequests(requests, errors_to_collect)

    self.assertEqual(['Some response'], result)
    self.assertEqual(len(requests), len(responses))
    self.assertEqual([api_exceptions.HttpException(http_err)],
                     errors_to_collect)


if __name__ == '__main__':
  test_case.main()
