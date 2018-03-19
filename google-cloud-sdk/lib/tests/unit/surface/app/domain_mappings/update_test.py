# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for gcloud app domain-mappings."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib.surface.app import domain_mappings_base


class DomainMappingsUpdateTest(domain_mappings_base.DomainMappingsBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _ExpectUpdateDomainMapping(self, domain, certificate_id, mask):
    """Adds expected domain-mappings create request and response.

    Args:
      domain: str, the custom domain string.
      certificate_id: str, a certificate id for the new domain.
      mask: str, a comma separated list of included fields to expect.
    """
    domain_mapping = self.MakeDomainMapping(domain, certificate_id)
    request = self.messages.AppengineAppsDomainMappingsPatchRequest(
        name=self._FormatDomainMappings(domain),
        domainMapping=domain_mapping,
        updateMask=mask)
    self.mock_client.AppsDomainMappingsService.Patch.Expect(
        request, response=self.messages.Operation(done=True))

  def testUpdateDomainMapping(self):
    self._ExpectUpdateDomainMapping('*.example.com', '1234',
                                    'sslSettings.certificateId')
    self.Run('app domain-mappings update *.example.com --certificate-id=1234')
    self.AssertErrContains('Updated [*.example.com].')

  def testUpdateDomainMapping_clearCert(self):
    self._ExpectUpdateDomainMapping('*.example.com', None,
                                    'sslSettings.certificateId')
    self.Run('app domain-mappings update *.example.com --no-certificate-id')
    self.AssertErrContains('Updated [*.example.com].')


class DomainMappingsUpdateBetaTest(domain_mappings_base.DomainMappingsBetaBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectUpdateDomainMapping(self, domain, certificate_id, management_type,
                                 mask):
    """Adds expected domain-mappings create request and response.

    Args:
      domain: str, the custom domain string.
      certificate_id: str, a certificate id for the new domain.
      management_type: SslSettings.SslManagementTypeValueValuesEnum,
                       AUTOMATIC or MANUAL certificate provisioning.
      mask: str, a comma separated list of included fields to expect.
    """
    ssl_management = self._ManagementTypeFromString(management_type)
    domain_mapping = self.MakeDomainMapping(domain, certificate_id,
                                            ssl_management)
    request = self.messages.AppengineAppsDomainMappingsPatchRequest(
        name=self._FormatDomainMappings(domain),
        domainMapping=domain_mapping,
        updateMask=mask)
    self.mock_client.AppsDomainMappingsService.Patch.Expect(
        request, response=self.messages.Operation(done=True))

  def testUpdateDomainMapping(self):
    self._ExpectUpdateDomainMapping(
        '*.example.com', '1234', 'MANUAL',
        'sslSettings.certificateId,sslSettings.sslManagementType')
    self.Run('app domain-mappings update *.example.com --certificate-id=1234')
    self.AssertErrContains('Updated [*.example.com].')

  def testUpdateDomainMapping_clearCert(self):
    self._ExpectUpdateDomainMapping(
        '*.example.com', None, 'MANUAL',
        'sslSettings.certificateId,sslSettings.sslManagementType')
    self.Run('app domain-mappings update *.example.com --no-certificate-id')
    self.AssertErrContains('Updated [*.example.com].')

  def testUpdateDomainMapping_autoManagementFailsWithCert(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app domain-mappings update
                  *.example.com --certificate-id=1
                  --certificate-management=AUTOMATIC""")
    self.AssertErrContains('Invalid value for [certificate-id]')

  def testUpdateDomainMapping_autoManagementFailsWithNoCert(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app domain-mappings update
                  *.example.com --no-certificate-id
                  --certificate-management=AUTOMATIC""")
    self.AssertErrContains('Invalid value for [no-certificate-id]')

  def testUpdateDomainMapping_manualManagementFailsWithNoCert(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app domain-mappings update *.example.com
                  --certificate-management=MANUAL""")
    self.AssertErrContains('Invalid value for [certificate-id]')
