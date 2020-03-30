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
"""Tests for `gcloud service-directory services update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class ServicesUpdateTestBeta(base.ServiceDirectoryUnitTestBase):

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
    self.metadata = self._Metadata(additional_properties=[
        self._AdditionalProperty(key='a', value='b'),
        self._AdditionalProperty(key='c', value='d'),
    ])
    self.my_service = self._Service(
        name=self.service_name, metadata=self.metadata)

  def _Service(self, name=None, endpoints=None, metadata=None):
    if not endpoints:
      endpoints = []
    return self.msgs.Service(name=name, endpoints=endpoints, metadata=metadata)

  def _Metadata(self, additional_properties=None):
    if not additional_properties:
      additional_properties = []
    return self.msgs.Service.MetadataValue(
        additionalProperties=additional_properties)

  def _AdditionalProperty(self, key, value=None):
    return self.msgs.Service.MetadataValue.AdditionalProperty(
        key=key, value=value)

  def _ExpectUpdateServiceRequest(self,
                                  service=None,
                                  name=None,
                                  update_mask=None,
                                  response=None):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesPatchRequest(
        service=service, name=name, updateMask=update_mask)
    self.client.projects_locations_namespaces_services.Patch.Expect(
        request=req, response=response)

  def testUpdate_UpdateMetadata(self):
    metadata = self._Metadata([self._AdditionalProperty('a', 'b')])
    service = self._Service(metadata=metadata)
    expected = self._Service(name=self.service_name, metadata=metadata)

    self._ExpectUpdateServiceRequest(
        service=service,
        name=self.service_name,
        update_mask='metadata',
        response=expected)

    actual = self.Run('service-directory services update my-service '
                      '--namespace my-namespace '
                      '--location my-location '
                      '--metadata a=b')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Updated service [my-service].')


class ServicesUpdateTestAlpha(ServicesUpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
