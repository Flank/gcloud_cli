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
"""Tests for `gcloud service-directory services create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class ServicesCreateTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.metadata = self._Metadata(
        additional_properties=[self._AdditionalProperty(key='a', value='b')])
    self.namespace_name = resources.REGISTRY.Parse(
        'my-namespace',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location'
        },
        collection='servicedirectory.projects.locations.namespaces'
    ).RelativeName()

  def _Service(self, name=None, endpoints=None, metadata=None):
    if endpoints is None:
      endpoints = []
    return self.msgs.Service(name=name, endpoints=endpoints, metadata=metadata)

  def _Metadata(self, additional_properties=None):
    return self.msgs.Service.MetadataValue(
        additionalProperties=additional_properties)

  def _AdditionalProperty(self, key, value=None):
    return self.msgs.Service.MetadataValue.AdditionalProperty(
        key=key, value=value)

  def _ExpectCreateServiceRequest(self, service_id, service):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesCreateRequest(
        parent=self.namespace_name, serviceId=service_id, service=service)
    self.client.projects_locations_namespaces_services.Create.Expect(
        request=req,
        response=self._Service(
            name=self.namespace_name + '/services/' + service_id,
            metadata=service.metadata))

  def testCreate(self):
    expected = self._Service(self.namespace_name + '/services/my-service')
    self._ExpectCreateServiceRequest('my-service', self._Service())

    actual = self.Run('service-directory services create my-service '
                      '--namespace my-namespace '
                      '--location my-location ')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created service [my-service].')

  def testCreate_WithMetadata(self):
    expected = self._Service(
        self.namespace_name + '/services/my-service', metadata=self.metadata)
    self._ExpectCreateServiceRequest('my-service',
                                     self._Service(metadata=self.metadata))

    actual = self.Run('service-directory services create my-service '
                      '--namespace my-namespace '
                      '--location my-location '
                      '--metadata a=b')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created service [my-service].')

  def testCreate_RelativeName(self):
    expected = self._Service(self.namespace_name + '/services/my-service')
    self._ExpectCreateServiceRequest('my-service', self._Service())

    actual = self.Run(
        'service-directory services create {}/services/my-service'.format(
            self.namespace_name))

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created service [my-service].')

  def testCreate_WithoutServiceId_Fails(self):
    with self.AssertRaisesArgumentErrorMatches('SERVICE must be specified.'):
      self.Run('service-directory services create '
               '--namespace my-namespace '
               '--location my-location')


class ServicesCreateTestAlpha(ServicesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
