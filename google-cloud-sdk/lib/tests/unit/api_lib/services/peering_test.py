# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests of the peering module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.services import peering
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class PeeringTest(unit_test_base.SNUnitTestBase):
  """Unit tests for peering module."""

  OPERATION_NAME = 'operations/abc.0000000000'
  NETWORK = 'hello'
  RANGES = ['10.0.1.0/30', '10.0.3.0/30']
  DNS_ZONE_NAME = 'googleapis-com'
  DNS_SUFFIX = 'googleapis.com.'

  def testCreateConnection_Success(self):
    """Test CreateConnection returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectCreateConnection(self.NETWORK, self.RANGES, self.OPERATION_NAME)

    got = peering.CreateConnection(self.PROJECT_NUMBER, self.service,
                                   self.NETWORK, self.RANGES)

    self.assertEqual(got, want)

  def testCreateConnection_PermissionDenied(self):
    """Test CreateConnection raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectCreateConnection(
        self.NETWORK, self.RANGES, None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.CreateConnectionsPermissionDeniedException, r'Error!'):
      peering.CreateConnection(self.PROJECT_NUMBER, self.service, self.NETWORK,
                               self.RANGES)

  def testUpdateConnection_Success(self):
    """Test UpdateConnection returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectUpdateConnection(self.NETWORK, self.RANGES, self.OPERATION_NAME,
                                True)

    got = peering.UpdateConnection(self.PROJECT_NUMBER, self.service,
                                   self.NETWORK, self.RANGES, True)

    self.assertEqual(got, want)

  def testUpdateConnection_PermissionDenied(self):
    """Test UpdateConnection raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectUpdateConnection(
        self.NETWORK, self.RANGES, None, True, error=server_error)

    with self.assertRaisesRegex(
        exceptions.CreateConnectionsPermissionDeniedException, r'Error!'):
      peering.UpdateConnection(self.PROJECT_NUMBER, self.service, self.NETWORK,
                               self.RANGES, True)

  def testGetOperation_Success(self):
    """Test GetOperation returns operation when successful."""
    want = self.services_messages.Operation(name=self.OPERATION_NAME, done=True)
    self.ExpectOperation(self.OPERATION_NAME, 0)

    got = peering.GetOperation(self.OPERATION_NAME)

    self.assertEqual(got, want)

  def testGetOperation_PermissionDenied(self):
    """Test GetOperation returns operation when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectOperation(self.OPERATION_NAME, 0, error=server_error)

    with self.assertRaisesRegex(exceptions.OperationErrorException, r'Error!'):
      peering.GetOperation(self.OPERATION_NAME)

  def testListConnections_Success(self):
    """Test ListConnection returns connections when successful."""
    want = [
        self.services_messages.Connection(
            network='projects/%s/global/networks/%s' % (self.PROJECT_NUMBER,
                                                        self.NETWORK),
            peering='servicenetworking-googleapis-com',
            reservedPeeringRanges=['google1', 'google2'])
    ]
    self.ExpectListConnections(self.NETWORK, want)

    got = peering.ListConnections(self.PROJECT_NUMBER, self.service,
                                  self.NETWORK)

    self.assertEqual(got, want)

  def testListConnections_PermissionDenied(self):
    """Test ListConnection raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectListConnections(self.NETWORK, None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.ListConnectionsPermissionDeniedException, r'Error!'):
      peering.ListConnections(self.PROJECT_NUMBER, self.service, self.NETWORK)

  def testEnableVpcServiceControls_Success(self):
    """Test EnableVpcServiceControls returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectEnableVpcServiceControls(self.NETWORK, self.OPERATION_NAME)

    got = peering.EnableVpcServiceControls(self.PROJECT_NUMBER, self.service,
                                           self.NETWORK)

    self.assertEqual(got, want)

  def testEnableVpcServiceControls_PermissionDenied(self):
    """Test EnableVpcServiceControls raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectEnableVpcServiceControls(self.NETWORK, None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.EnableVpcServiceControlsPermissionDeniedException,
        r'Error!'):
      peering.EnableVpcServiceControls(self.PROJECT_NUMBER, self.service,
                                       self.NETWORK)

  def testDisableVpcServiceControls_Success(self):
    """Test DisableVpcServiceControls returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectDisableVpcServiceControls(self.NETWORK, self.OPERATION_NAME)

    got = peering.DisableVpcServiceControls(self.PROJECT_NUMBER, self.service,
                                            self.NETWORK)

    self.assertEqual(got, want)

  def testDisableVpcServiceControls_PermissionDenied(self):
    """Test DisableVpcServiceControls raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectDisableVpcServiceControls(self.NETWORK, None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.DisableVpcServiceControlsPermissionDeniedException,
        r'Error!'):
      peering.DisableVpcServiceControls(self.PROJECT_NUMBER, self.service,
                                        self.NETWORK)

  def testCreatePeeredDnsDomain_Success(self):
    """Test CreatePeeredDnsDomain returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME,
        done=False,
    )
    self.ExpectCreatePeeredDnsDomain(
        self.NETWORK,
        self.DNS_ZONE_NAME,
        self.DNS_SUFFIX,
        self.OPERATION_NAME,
    )

    got = peering.CreatePeeredDnsDomain(
        self.PROJECT_NUMBER,
        self.service,
        self.NETWORK,
        self.DNS_ZONE_NAME,
        self.DNS_SUFFIX,
    )

    self.assertEqual(got, want)

  def testCreatePeeredDnsDomain_PermissionDenied(self):
    """Test CreatePeeredDnsDomain raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectCreatePeeredDnsDomain(
        self.NETWORK,
        self.DNS_ZONE_NAME,
        self.DNS_SUFFIX,
        self.OPERATION_NAME,
        error=server_error,
    )

    with self.assertRaisesRegex(
        exceptions.CreatePeeredDnsDomainPermissionDeniedException,
        r'Error!',
    ):
      peering.CreatePeeredDnsDomain(
          self.PROJECT_NUMBER,
          self.service,
          self.NETWORK,
          self.DNS_ZONE_NAME,
          self.DNS_SUFFIX,
      )

  def testDeletePeeredDnsDomain_Success(self):
    """Test DeletePeeredDnsDomain returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME,
        done=False,
    )
    self.ExpectDeletePeeredDnsDomain(
        self.NETWORK,
        self.DNS_ZONE_NAME,
        self.OPERATION_NAME,
    )

    got = peering.DeletePeeredDnsDomain(
        self.PROJECT_NUMBER,
        self.service,
        self.NETWORK,
        self.DNS_ZONE_NAME,
    )

    self.assertEqual(got, want)

  def testDeletePeeredDnsDomain_PermissionDenied(self):
    """Test DeletePeeredDnsDomain raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectDeletePeeredDnsDomain(
        self.NETWORK,
        self.DNS_ZONE_NAME,
        self.OPERATION_NAME,
        error=server_error,
    )

    with self.assertRaisesRegex(
        exceptions.DeletePeeredDnsDomainPermissionDeniedException,
        r'Error!',
    ):
      peering.DeletePeeredDnsDomain(
          self.PROJECT_NUMBER,
          self.service,
          self.NETWORK,
          self.DNS_ZONE_NAME,
      )

  def testListPeeredDnsDomains_Success(self):
    """Test ListPeeredDnsDomains returns domains when successful."""
    want = [
        self.services_messages.PeeredDnsDomain(
            name=self.DNS_ZONE_NAME,
            dnsSuffix=self.DNS_SUFFIX,
        ),
    ]
    self.ExpectListPeeredDnsDomains(self.NETWORK, want)

    got = peering.ListPeeredDnsDomains(
        self.PROJECT_NUMBER,
        self.service,
        self.NETWORK,
    )

    self.assertEqual(got, want)

  def testListPeeredDnsDomains_PermissionDenied(self):
    """Test ListPeeredDnsDomains raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error!')
    self.ExpectListPeeredDnsDomains(self.NETWORK, None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.ListPeeredDnsDomainsPermissionDeniedException,
        r'Error!',
    ):
      peering.ListPeeredDnsDomains(
          self.PROJECT_NUMBER,
          self.service,
          self.NETWORK,
      )
