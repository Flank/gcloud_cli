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

from __future__ import absolute_import
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.app import domain_mappings_base


class DomainMappingsCommandTest(domain_mappings_base.DomainMappingsBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def ExpectGetDomainMapping(self, domain, certificate_id):
    """Adds expected domain-mappings describe request and response.

    Args:
      domain: str, the custom domain string.
      certificate_id: str, a certificate id for the new domain.
    """
    request = self.messages.AppengineAppsDomainMappingsGetRequest(
        name=self._FormatDomainMappings(domain))
    response = self.MakeDomainMapping(domain, certificate_id)
    self.mock_client.AppsDomainMappingsService.Get.Expect(
        request, response=response)

  def testDescribeDomainMapping(self):
    self.ExpectGetDomainMapping('*.example.com', '1234')
    result = self.Run('app domain-mappings describe *.example.com')
    self.assertEqual('*.example.com', result.id)
    self.assertEqual('1234', result.sslSettings.certificateId)


class DomainMappingsCommandBetaTest(
    domain_mappings_base.DomainMappingsBetaBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def ExpectGetDomainMapping(self, domain, certificate_id, management_type):
    """Adds expected domain-mappings describe request and response.

    Args:
      domain: str, the custom domain string.
      certificate_id: str, a certificate id for the new domain.
      management_type: SslSettings.SslManagementTypeValueValuesEnum,
                       AUTOMATIC or MANUAL certificate provisioning.
    """
    request = self.messages.AppengineAppsDomainMappingsGetRequest(
        name=self._FormatDomainMappings(domain))
    ssl_management = self._ManagementTypeFromString(management_type)
    response = self.MakeDomainMapping(domain, certificate_id, ssl_management)
    self.mock_client.AppsDomainMappingsService.Get.Expect(
        request, response=response)

  def testDescribeDomainMapping(self):
    self.ExpectGetDomainMapping('*.example.com', '1234', 'MANUAL')
    result = self.Run('app domain-mappings describe *.example.com')
    self.assertEqual('*.example.com', result.id)
    self.assertEqual('1234', result.sslSettings.certificateId)
