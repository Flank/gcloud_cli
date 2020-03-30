# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud service-directory endpoints list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class EndpointsListTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    # By default, the command output resources are formatted and displayed on
    # log.out. Disabling the output allows the output resources to be returned
    # by the Run() method. This disables all user interactions/output.
    properties.VALUES.core.user_output_enabled.Set(False)

    self.service_name = resources.REGISTRY.Parse(
        'my-service',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location',
            'namespacesId': 'my-namespace',
        },
        collection='servicedirectory.projects.locations.namespaces.services'
    ).RelativeName()
    self.my_endpoint = self._Endpoint(
        name=self.service_name + '/endpoints/my-endpoint',
        address='10.01.0.1',
        port=2)
    self.an_endpoint = self._Endpoint(
        name=self.service_name + '/endpoints/an-endpoint',
        address='20.02.0.2',
        port=1)
    self.endpoints = [
        self.my_endpoint,
        self.an_endpoint,
    ]

  def _Endpoint(self, name=None, address=None, port=None, metadata=None):
    return self.msgs.Endpoint(
        name=name, address=address, port=port, metadata=metadata)

  def _ListEndpointsResponse(self, endpoints, next_page_token=None):
    return self.msgs.ListEndpointsResponse(
        endpoints=endpoints, nextPageToken=next_page_token)

  def _ExpectListEndpointRequest(self,
                                 parent,
                                 endpoint_filter=None,
                                 order_by=None,
                                 page_size=None,
                                 page_token=None,
                                 response_endpoints=None,
                                 response_page_token=None):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsListRequest(
        parent=parent,
        filter=endpoint_filter,
        orderBy=order_by,
        pageSize=page_size,
        pageToken=page_token)
    self.client.projects_locations_namespaces_services_endpoints.List.Expect(
        request=req,
        response=self._ListEndpointsResponse(response_endpoints,
                                             response_page_token))

  def testList_NoFlags_YieldsDefaultList(self):
    expected = self.endpoints
    self._ExpectListEndpointRequest(
        parent=self.service_name, response_endpoints=expected)

    actual = self.Run('service-directory endpoints list --service my-service '
                      '--namespace my-namespace --location my-location')

    self.assertEqual(actual, expected)

  def testList_FilterByName_YieldsMyEndpoint(self):
    expected = [self.my_endpoint]
    self._ExpectListEndpointRequest(
        parent=self.service_name,
        endpoint_filter='name:my-endpoint',
        response_endpoints=expected)

    actual = self.Run('service-directory endpoints list --service my-service '
                      '--namespace my-namespace --location my-location '
                      '--filter name:my-endpoint')

    self.assertEqual(actual, expected)

  def testList_OrderByName_YieldsNameAsc(self):
    expected = [self.an_endpoint, self.my_endpoint]
    self._ExpectListEndpointRequest(
        parent=self.service_name,
        order_by='name desc,name asc',
        response_endpoints=expected)

    actual = self.Run('service-directory endpoints list --service my-service '
                      '--namespace my-namespace --location my-location '
                      '--sort-by ~name,name')

    self.assertEqual(actual, expected)

  def testList_MultiplePages_YieldsMultiplePages(self):
    expected = self.endpoints
    self._ExpectListEndpointRequest(
        parent=self.service_name,
        page_size=1,
        response_endpoints=expected[:1],
        response_page_token='nextPageToken')
    self._ExpectListEndpointRequest(
        parent=self.service_name,
        page_size=1,
        page_token='nextPageToken',
        response_endpoints=expected[1:])

    actual = self.Run('service-directory endpoints list --service my-service '
                      '--namespace my-namespace --location my-location '
                      '--page-size 1')

    self.assertEqual(actual, expected)


class EndpointsListTestAlpha(EndpointsListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
