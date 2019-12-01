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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
import six

MESSAGES = apis.GetMessagesModule(global_methods.SERVERLESS_API_NAME,
                                  global_methods.SERVERLESS_API_VERSION)


class ListServicesTest(sdk_test_base.WithOutputCapture):

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')
    self.client = mock.Client(
        apis.GetClientClass(global_methods.SERVERLESS_API_NAME,
                            global_methods.SERVERLESS_API_VERSION),
        # no_http since we will not make http requests in a unit test
        real_client=apis.GetClientInstance(
            global_methods.SERVERLESS_API_NAME,
            global_methods.SERVERLESS_API_VERSION,
            no_http=True))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

  def testMissingRegions(self):
    request = MESSAGES.RunProjectsLocationsServicesListRequest(
        parent='projects/my-project/locations/-')
    response = MESSAGES.ListServicesResponse(
        unreachable=['us-central1', 'asia-northeast1'])
    self.client.projects_locations_services.List.Expect(
        request=request, response=response)
    global_methods.ListServices(self.client)

    self.AssertErrEquals(
        'WARNING: The following Cloud Run regions did not respond: '
        'asia-northeast1, us-central1. List results may be incomplete.\n')

  def testReturnsServices(self):
    request = MESSAGES.RunProjectsLocationsServicesListRequest(
        parent='projects/my-project/locations/-')
    response = MESSAGES.ListServicesResponse(items=[
        MESSAGES.Service(metadata=MESSAGES.ObjectMeta(name='Service1')),
        MESSAGES.Service(metadata=MESSAGES.ObjectMeta(name='Service2'))
    ])
    self.client.projects_locations_services.List.Expect(
        request=request, response=response)
    services = global_methods.ListServices(self.client)

    six.assertCountEqual(self, [service.name for service in services],
                         ('Service1', 'Service2'))
    self.AssertErrEquals('')


if __name__ == '__main__':
  test_case.main()
