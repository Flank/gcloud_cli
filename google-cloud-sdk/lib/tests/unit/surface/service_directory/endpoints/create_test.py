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
"""Tests for `gcloud service-directory endpoints create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.service_directory import base


class EndpointsCreateTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.address = '10.01.0.1'
    self.port = 2
    self.metadata = self._Metadata(
        additional_properties=[self._AdditionalProperty(key='a', value='b')])
    self.service_name = resources.REGISTRY.Parse(
        'my-service',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location',
            'namespacesId': 'my-namespace',
        },
        collection='servicedirectory.projects.locations.namespaces.services'
    ).RelativeName()

  def _Endpoint(self, name=None, address=None, port=None, metadata=None):
    return self.msgs.Endpoint(
        name=name, address=address, port=port, metadata=metadata)

  def _Metadata(self, additional_properties=None):
    return self.msgs.Endpoint.MetadataValue(
        additionalProperties=additional_properties)

  def _AdditionalProperty(self, key, value=None):
    return self.msgs.Endpoint.MetadataValue.AdditionalProperty(
        key=key, value=value)

  def _ExpectCreateEndpointRequest(self, endpoint_id, endpoint):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsCreateRequest(
        parent=self.service_name, endpointId=endpoint_id, endpoint=endpoint)
    self.client.projects_locations_namespaces_services_endpoints.Create.Expect(
        request=req,
        response=self._Endpoint(
            name=self.service_name + '/endpoints/' + endpoint_id,
            address=endpoint.address,
            port=endpoint.port,
            metadata=endpoint.metadata))

  def testCreate(self):
    expected = self._Endpoint(self.service_name + '/endpoints/my-endpoint')
    self._ExpectCreateEndpointRequest('my-endpoint', self._Endpoint())

    actual = self.Run('service-directory endpoints create my-endpoint '
                      '--service my-service '
                      '--namespace=my-namespace '
                      '--location my-location')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created endpoint [my-endpoint].')

  def testCreate_RelativeName(self):
    expected = self._Endpoint(self.service_name + '/endpoints/my-endpoint')
    self._ExpectCreateEndpointRequest('my-endpoint', self._Endpoint())

    actual = self.Run(
        'service-directory endpoints create {}/endpoints/my-endpoint'.format(
            self.service_name))

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created endpoint [my-endpoint].')

  def testCreate_WithAddressAndPort(self):
    expected = self._Endpoint(self.service_name + '/endpoints/my-endpoint',
                              self.address, self.port)
    self._ExpectCreateEndpointRequest(
        'my-endpoint', self._Endpoint(address=self.address, port=self.port))

    actual = self.Run('service-directory endpoints create my-endpoint '
                      '--service my-service '
                      '--namespace=my-namespace '
                      '--location my-location '
                      '--address 10.01.0.1 '
                      '--port 2')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created endpoint [my-endpoint].')

  def testCreate_WithMetadata(self):
    expected = self._Endpoint(self.service_name + '/endpoints/my-endpoint',
                              self.address, None, self.metadata)
    self._ExpectCreateEndpointRequest(
        'my-endpoint',
        self._Endpoint(address=self.address, port=None, metadata=self.metadata))

    actual = self.Run(
        'service-directory endpoints create my-endpoint --metadata a=b '
        '--service my-service '
        '--namespace=my-namespace '
        '--location my-location '
        '--address 10.01.0.1')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created endpoint [my-endpoint].')

  def testCreate_WithoutEndpointId_Fails(self):
    with self.AssertRaisesArgumentErrorMatches('ENDPOINT must be specified.'):
      self.Run('service-directory endpoints create '
               '--service my-service '
               '--namespace=my-namespace '
               '--location my-location '
               '--address 10.01.0.1')

  def testCreate_InvalidRequest_Fails(self):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsCreateRequest(
        parent=self.service_name,
        endpointId='my-endpoint',
        endpoint=self._Endpoint())
    exception = http_error.MakeHttpError(code=400)
    self.client.projects_locations_namespaces_services_endpoints.Create.Expect(
        request=req, exception=exception, response=None)
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Invalid request API reason: Invalid request.'):
      self.Run('service-directory endpoints create my-endpoint '
               '--service my-service '
               '--namespace=my-namespace '
               '--location my-location')
    self.AssertErrNotContains('Created endpoint')


class EndpointsCreateTestAlpha(EndpointsCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
