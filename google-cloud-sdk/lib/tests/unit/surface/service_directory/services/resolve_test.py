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
"""Tests for `gcloud service-directory services resolve`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class ServicesResolveTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.service_name = resources.REGISTRY.Parse(
        'my-service',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location',
            'namespacesId': 'my-namespace',
        },
        collection='servicedirectory.projects.locations.namespaces.services'
    ).RelativeName()

  def _Service(self, name=None, endpoints=None, metadata=None):
    if not endpoints:
      endpoints = []
    return self.msgs.Service(name=name, endpoints=endpoints, metadata=metadata)

  def _ResolveServiceResponse(self, service=None):
    return self.msgs.ResolveServiceResponse(service=service)

  def _ExpectResolveServiceRequest(self,
                                   service_name,
                                   response=None,
                                   max_endpoints=None,
                                   endpoint_filter=None):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesResolveRequest(
        name=service_name,
        resolveServiceRequest=self.msgs.ResolveServiceRequest(
            maxEndpoints=max_endpoints,
            endpointFilter=endpoint_filter))
    self.client.projects_locations_namespaces_services.Resolve.Expect(
        request=req, response=response)

  def testResolve(self):
    expected = self._ResolveServiceResponse(
        self._Service(name=self.service_name))
    self._ExpectResolveServiceRequest(self.service_name, expected)

    actual = self.Run('service-directory services resolve my-service '
                      '--location my-location --namespace my-namespace')

    self.assertEqual(actual, expected)

  def testResolve_RelativeName(self):
    expected = self._ResolveServiceResponse(
        self._Service(name=self.service_name))
    self._ExpectResolveServiceRequest(self.service_name, expected)

    actual = self.Run('service-directory services resolve {}'.format(
        self.service_name))

    self.assertEqual(actual, expected)

  def testResolve_WithMaxEndpoints(self):
    expected = self._ResolveServiceResponse(
        self._Service(name=self.service_name))
    self._ExpectResolveServiceRequest(self.service_name, expected, 5)

    actual = self.Run(
        'service-directory services resolve --max-endpoints 5 {}'.format(
            self.service_name))

    self.assertEqual(actual, expected)

  def testResolve_WithEndpointFilter(self):
    expected = self._ResolveServiceResponse(
        self._Service(name=self.service_name))
    self._ExpectResolveServiceRequest(
        self.service_name, expected, endpoint_filter='metadata.status=healthy')

    actual = self.Run('service-directory services resolve --endpoint-filter '
                      '"metadata.status=healthy" {}'.format(self.service_name))

    self.assertEqual(actual, expected)

  def testResolve_WithServiceFields(self):
    expected = self._ResolveServiceResponse(
        self._Service(
            name=self.service_name,
            metadata=self.msgs.Service.MetadataValue(additionalProperties=[
                self.msgs.Service.MetadataValue.AdditionalProperty(
                    key='a', value='b')
            ])))
    self._ExpectResolveServiceRequest(self.service_name, expected)

    actual = self.Run('service-directory services resolve my-service '
                      '--location my-location --namespace my-namespace')

    self.assertEqual(actual, expected)


class ServicesResolveTestAlpha(ServicesResolveTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
