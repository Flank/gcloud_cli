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
"""Tests for `gcloud service-directory endpoints delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.service_directory import base


class EndpointsDeleteTestBeta(base.ServiceDirectoryUnitTestBase):

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

  def _ExpectDeleteEndpointRequest(self, endpoint_name):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsDeleteRequest(
        name=endpoint_name)
    self.client.projects_locations_namespaces_services_endpoints.Delete.Expect(
        request=req, response=self.msgs.Empty())

  def testDelete(self):
    expected = self.msgs.Empty()
    self._ExpectDeleteEndpointRequest(self.endpoint_name)

    actual = self.Run('service-directory endpoints delete my-endpoint '
                      '--service my-service '
                      '--location my-location --namespace my-namespace')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Deleted endpoint [my-endpoint]')

  def testDelete_RelativeName(self):
    expected = self.msgs.Empty()
    self._ExpectDeleteEndpointRequest(self.endpoint_name)

    actual = self.Run('service-directory endpoints delete {}'.format(
        self.endpoint_name))

    self.assertEqual(actual, expected)
    self.AssertErrContains('Deleted endpoint [my-endpoint]')

  def testDelete_InvliadRequest_Fails(self):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsDeleteRequest(
        name=self.endpoint_name)
    exception = http_error.MakeHttpError(code=400)
    self.client.projects_locations_namespaces_services_endpoints.Delete.Expect(
        request=req, exception=exception, response=None)
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Invalid request API reason: Invalid request.'):
      self.Run('service-directory endpoints delete my-endpoint '
               '--service my-service '
               '--location my-location --namespace my-namespace')
    self.AssertErrNotContains('Deleted endpoint')


class EndpointsDeleteTestAlpha(EndpointsDeleteTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
