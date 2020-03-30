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
"""Tests for `gcloud service-directory endpoints update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class EndpointsUpdateTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.endpoint_name = resources.REGISTRY.Parse(
        'my-endpoint',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location',
            'namespacesId': 'my-namespace',
            'servicesId': 'my-service',
        },
        collection='servicedirectory.projects.locations.namespaces.services.endpoints'
    ).RelativeName()
    self.address = '10.01.0.1'
    self.port = 2
    self.metadata = self._Metadata(additional_properties=[
        self._AdditionalProperty(key='a', value='b'),
        self._AdditionalProperty(key='c', value='d'),
    ])
    self.my_endpoint = self._Endpoint(self.endpoint_name, self.address,
                                      self.port, self.metadata)

  def _Endpoint(self, name=None, address=None, port=None, metadata=None):
    return self.msgs.Endpoint(
        name=name, address=address, port=port, metadata=metadata)

  def _Metadata(self, additional_properties=None):
    if not additional_properties:
      additional_properties = []
    return self.msgs.Endpoint.MetadataValue(
        additionalProperties=additional_properties)

  def _AdditionalProperty(self, key, value=None):
    return self.msgs.Endpoint.MetadataValue.AdditionalProperty(
        key=key, value=value)

  def _ExpectUpdateEndpointRequest(self,
                                   endpoint=None,
                                   name=None,
                                   update_mask=None,
                                   response=None):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsPatchRequest(
        endpoint=endpoint, name=name, updateMask=update_mask)
    self.client.projects_locations_namespaces_services_endpoints.Patch.Expect(
        request=req, response=response)

  def testUpdate_UpdateAddress(self):
    endpoint = self._Endpoint(address='1.2.3.4')
    expected = self._Endpoint(self.endpoint_name, '1.2.3.4', self.port,
                              self.metadata)
    self._ExpectUpdateEndpointRequest(
        endpoint=endpoint,
        name=self.endpoint_name,
        update_mask='address',
        response=expected)

    actual = self.Run('service-directory endpoints update my-endpoint '
                      '--service my-service '
                      '--namespace=my-namespace '
                      '--location my-location '
                      '--address 1.2.3.4')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Updated endpoint [my-endpoint].')

  def testUpdate_UpdatePort(self):
    endpoint = self._Endpoint(port=5)
    expected = self._Endpoint(self.endpoint_name, self.address, 5,
                              self.metadata)
    self._ExpectUpdateEndpointRequest(
        endpoint=endpoint,
        name=self.endpoint_name,
        update_mask='port',
        response=expected)

    actual = self.Run('service-directory endpoints update my-endpoint '
                      '--service my-service '
                      '--namespace my-namespace '
                      '--location my-location '
                      '--port 5')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Updated endpoint [my-endpoint].')

  def testUpdate_UpdatePortToZero(self):
    endpoint = self._Endpoint(port=0)
    expected = self._Endpoint(self.endpoint_name, self.address, 0,
                              self.metadata)

    self._ExpectUpdateEndpointRequest(
        endpoint=endpoint,
        name=self.endpoint_name,
        update_mask='port',
        response=expected)

    actual = self.Run('service-directory endpoints update my-endpoint '
                      '--service my-service '
                      '--namespace my-namespace '
                      '--location my-location '
                      '--port 0')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Updated endpoint [my-endpoint].')

  def testUpdate_UpdateMetadata(self):
    metadata = self._Metadata([self._AdditionalProperty('a', 'b')])
    endpoint = self._Endpoint(metadata=metadata)
    expected = self._Endpoint(self.endpoint_name, self.address, self.port,
                              metadata)

    self._ExpectUpdateEndpointRequest(
        endpoint=endpoint,
        name=self.endpoint_name,
        update_mask='metadata',
        response=expected)

    actual = self.Run('service-directory endpoints update my-endpoint '
                      '--service my-service '
                      '--namespace my-namespace '
                      '--location my-location '
                      '--metadata a=b')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Updated endpoint [my-endpoint].')

  def testUpdate_UpdateAllFields(self):
    metadata = self._Metadata([self._AdditionalProperty('a', 'z')])
    endpoint = self._Endpoint(address='1.2.3.4', port=5, metadata=metadata)
    expected = self._Endpoint(
        name=self.endpoint_name, address='1.2.3.4', port=5, metadata=metadata)

    self._ExpectUpdateEndpointRequest(
        endpoint=endpoint,
        name=self.endpoint_name,
        update_mask='address,port,metadata',
        response=expected)

    actual = self.Run('service-directory endpoints update my-endpoint '
                      '--service my-service '
                      '--namespace my-namespace '
                      '--location my-location '
                      '--address 1.2.3.4 '
                      '--port 5 '
                      '--metadata a=z')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Updated endpoint [my-endpoint].')


class EndpointsUpdateTestAlpha(EndpointsUpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
