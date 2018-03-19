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

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib.surface.app import domain_mappings_base


class DomainMappingsCommandTest(domain_mappings_base.DomainMappingsBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _ExpectCreateDomainMapping(self, domain, certificate_id):
    """Adds expected domain-mappings create request and response.

    Args:
      domain: str, the custom domain string.
      certificate_id: str, a certificate id for the new domain.
    """
    domain_mapping = self.MakeDomainMapping(domain, certificate_id)
    request = self.messages.AppengineAppsDomainMappingsCreateRequest(
        parent=self._FormatApp(), domainMapping=domain_mapping)
    self.mock_client.AppsDomainMappingsService.Create.Expect(
        request,
        response=self.messages.Operation(
            done=True,
            response=encoding.JsonToMessage(
                self.messages.Operation.ResponseValue,
                encoding.MessageToJson(domain_mapping))))

  def testCreateDomainMapping(self):
    self._ExpectCreateDomainMapping('*.example.com', '1')
    self.Run("""app domain-mappings create
                *.example.com --certificate-id=1""")
    self.AssertErrContains('Created [*.example.com].')


class DomainMappingsCommandAlphaTest(
    domain_mappings_base.DomainMappingsBetaBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectCreateDomainMapping(self, domain, certificate_id, management_type):
    """Adds expected domain-mappings create request and response.

    Args:
      domain: str, the custom domain string.
      certificate_id: str, a certificate id for the new domain.
      management_type: SslSettings.SslManagementTypeValueValuesEnum,
                       AUTOMATIC or MANUAL certificate provisioning.
    """
    ssl_management = self._ManagementTypeFromString(management_type)
    domain_mapping = self.MakeDomainMapping(domain, certificate_id,
                                            ssl_management)
    request = self.messages.AppengineAppsDomainMappingsCreateRequest(
        parent=self._FormatApp(), domainMapping=domain_mapping)
    self.mock_client.AppsDomainMappingsService.Create.Expect(
        request,
        response=self.messages.Operation(
            done=True,
            response=encoding.JsonToMessage(
                self.messages.Operation.ResponseValue,
                encoding.MessageToJson(domain_mapping))))

  def testCreateDomainMapping(self):
    self._ExpectCreateDomainMapping('*.example.com', '1', 'MANUAL')
    self.Run("""app domain-mappings create
                *.example.com --certificate-id=1""")
    self.AssertErrContains('Created [*.example.com].')

  def testCreateDomainMapping_manualManagement(self):
    self._ExpectCreateDomainMapping('*.example.com', '1', 'MANUAL')
    self.Run("""app domain-mappings create
                *.example.com --certificate-id=1
                --certificate-management=MANUAL""")
    self.AssertErrContains('Created [*.example.com].')

  def testCreateDomainMapping_autoManagement(self):
    self._ExpectCreateDomainMapping('example.com', None, 'AUTOMATIC')
    self.Run("""app domain-mappings create
                example.com --certificate-management=AUTOMATIC""")
    self.AssertErrContains('Created [example.com].')

  def testCreateDomainMappingNoManagementSpecified_autoManagement(self):
    self._ExpectCreateDomainMapping('example.com', None, 'AUTOMATIC')
    self.Run("""app domain-mappings create example.com""")
    self.AssertErrContains('Created [example.com].')

  def testCreateDomainMapping_autoManagementFailsWithCert(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app domain-mappings create
                  *.example.com --certificate-id=1
                  --certificate-management=AUTOMATIC""")
    self.AssertErrContains('Invalid value for [certificate-id]')
