# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base
import mock


class DeletePeeredDnsDomainTest(unit_test_base.SNUnitTestBase):
  """Unit tests for services peered-dns-domains delete command."""
  OPERATION_NAME = 'operations/abc.0000000000'
  NETWORK = 'hello'
  ZONE_NAME = 'googleapis-com'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  @mock.patch.object(projects_api, 'Get', autospec=True)
  def testDeletePeeredDnsDomain_Success(self, mock_get):
    mock_get.return_value.projectNumber = self.PROJECT_NUMBER
    self.ExpectDeletePeeredDnsDomain(
        self.NETWORK,
        self.ZONE_NAME,
        self.OPERATION_NAME,
    )
    self.ExpectOperation(self.OPERATION_NAME, poll_count=3)

    self.Run(('services peered-dns-domains delete {} '
              '--service={} --network={}').format(
                  self.ZONE_NAME,
                  self.service,
                  self.NETWORK,
              ))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  @mock.patch.object(projects_api, 'Get', autospec=True)
  def testDeletePeeredDnsDomain_WithDefaultService(self, mock_get):
    mock_get.return_value.projectNumber = self.PROJECT_NUMBER
    self.service = 'servicenetworking.googleapis.com'
    self.ExpectDeletePeeredDnsDomain(
        self.NETWORK,
        self.ZONE_NAME,
        self.OPERATION_NAME,
    )
    self.ExpectOperation(self.OPERATION_NAME, poll_count=3)

    self.Run(('services peered-dns-domains delete {} '
              '--network={}').format(
                  self.ZONE_NAME,
                  self.NETWORK,
              ))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  @mock.patch.object(projects_api, 'Get', autospec=True)
  def testDeletePeeredDnsDomain_Async(self, mock_get):
    mock_get.return_value.projectNumber = self.PROJECT_NUMBER
    self.ExpectDeletePeeredDnsDomain(
        self.NETWORK,
        self.ZONE_NAME,
        self.OPERATION_NAME,
    )

    self.Run(('services peered-dns-domains delete {} '
              '--service={} --network={} --async').format(
                  self.ZONE_NAME,
                  self.service,
                  self.NETWORK,
              ))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('operation is in progress')

  @mock.patch.object(projects_api, 'Get', autospec=True)
  def testDeletePeeredDnsDomain_AsyncWithDefaultService(self, mock_get):
    mock_get.return_value.projectNumber = self.PROJECT_NUMBER
    self.service = 'servicenetworking.googleapis.com'
    self.ExpectDeletePeeredDnsDomain(
        self.NETWORK,
        self.ZONE_NAME,
        self.OPERATION_NAME,
    )

    self.Run(('services peered-dns-domains delete {} '
              '--network={} --async').format(
                  self.ZONE_NAME,
                  self.NETWORK,
              ))
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('operation is in progress')

  @mock.patch.object(projects_api, 'Get', autospec=True)
  def testDeletePeeredDnsDomain_PermissionDenied(self, mock_get):
    mock_get.return_value.projectNumber = self.PROJECT_NUMBER
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectDeletePeeredDnsDomain(
        self.NETWORK,
        self.ZONE_NAME,
        self.OPERATION_NAME,
        error=server_error,
    )

    with self.assertRaisesRegex(
        exceptions.DeletePeeredDnsDomainPermissionDeniedException,
        r'Error.',
    ):
      self.Run(('services peered-dns-domains delete {} '
                '--service={} --network={}').format(
                    self.ZONE_NAME,
                    self.service,
                    self.NETWORK,
                ))


if __name__ == '__main__':
  test_case.main()
