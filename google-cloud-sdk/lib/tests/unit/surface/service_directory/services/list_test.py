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
"""Tests for `gcloud service-directory services list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class ServicesListTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    # By default, the command output resources are formatted and displayed on
    # log.out. Disabling the output allows the output resources to be returned
    # by the Run() method. This disables all user interactions/output.
    properties.VALUES.core.user_output_enabled.Set(False)

    self.namespace_name = resources.REGISTRY.Parse(
        'my-namespace',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location',
        },
        collection='servicedirectory.projects.locations.namespaces'
    ).RelativeName()
    self.my_service = self._Service(
        name=self.namespace_name + '/services/my-service', metadata=None)
    self.a_service = self._Service(
        name=self.namespace_name + '/services/a-service', metadata=None)
    self.services = [
        self.my_service,
        self.a_service,
    ]

  def _Service(self, name=None, endpoints=None, metadata=None):
    if not endpoints:
      endpoints = []
    return self.msgs.Service(name=name, endpoints=endpoints, metadata=metadata)

  def _ListServicesResponse(self, services, next_page_token=None):
    return self.msgs.ListServicesResponse(
        services=services, nextPageToken=next_page_token)

  def _ExpectListServiceRequest(self,
                                parent,
                                service_filter=None,
                                order_by=None,
                                page_size=None,
                                page_token=None,
                                response_services=None,
                                response_page_token=None):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesListRequest(
        parent=parent,
        filter=service_filter,
        orderBy=order_by,
        pageSize=page_size,
        pageToken=page_token)
    self.client.projects_locations_namespaces_services.List.Expect(
        request=req,
        response=self._ListServicesResponse(response_services,
                                            response_page_token))

  def testList_NoFlags_YieldsDefaultList(self):
    expected = self.services
    self._ExpectListServiceRequest(
        parent=self.namespace_name, response_services=expected)

    actual = self.Run('service-directory services list '
                      '--namespace my-namespace '
                      '--location my-location')

    self.assertEqual(actual, expected)

  def testList_FilterByName_YieldsMyService(self):
    expected = [self.my_service]
    self._ExpectListServiceRequest(
        parent=self.namespace_name,
        service_filter='name:my-service',
        response_services=expected)

    actual = self.Run('service-directory services list '
                      '--namespace my-namespace '
                      '--location my-location '
                      '--filter name:my-service')

    self.assertEqual(actual, expected)

  def testList_OrderbyName_YieldsNameAsc(self):
    expected = [self.a_service, self.my_service]
    self._ExpectListServiceRequest(
        parent=self.namespace_name,
        order_by='name desc,name asc',
        response_services=expected)

    actual = self.Run(
        'service-directory services list --namespace my-namespace '
        '--location my-location '
        '--sort-by ~name,name')

    self.assertEqual(actual, expected)

  def testList_MultiplePages_YieldsMultiplePages(self):
    expected = self.services
    self._ExpectListServiceRequest(
        parent=self.namespace_name,
        page_size=1,
        response_services=expected[:1],
        response_page_token='nextPageToken')
    self._ExpectListServiceRequest(
        parent=self.namespace_name,
        page_size=1,
        page_token='nextPageToken',
        response_services=expected[1:])

    actual = self.Run(
        'service-directory services list --namespace my-namespace '
        '--location my-location '
        '--page-size 1')

    self.assertEqual(actual, expected)


class ServicesListTestAlpha(ServicesListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
