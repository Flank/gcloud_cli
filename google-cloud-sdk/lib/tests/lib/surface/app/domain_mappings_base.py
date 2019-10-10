# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Base class for domain_mappings tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class DomainMappingsBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for all DomainMappings tests."""

  APPENGINE_API = 'appengine'
  APPENGINE_API_VERSION = 'v1'

  def _FormatApp(self):
    return 'apps/{0}'.format(self.Project())

  def _FormatDomainMappings(self, domain_id):
    uri = self._FormatApp() + '/domainMappings'
    if domain_id:
      uri += '/' + domain_id
    return uri

  def _ManagementTypeFromString(self, management_type):
    return self.messages.SslSettings.SslManagementTypeValueValuesEnum(
        management_type.upper()) if management_type else None

  def MakeDomainMapping(self, domain, certificate_id, management_type):
    ssl = self.messages.SslSettings(certificateId=certificate_id)
    mapping = self.messages.DomainMapping(id=domain, sslSettings=ssl)
    if management_type is not None:
      mapping.sslSettings.sslManagementType = management_type
    return mapping

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule(self.APPENGINE_API,
                                                self.APPENGINE_API_VERSION)
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass(self.APPENGINE_API,
                                 self.APPENGINE_API_VERSION),
        real_client=core_apis.GetClientInstance(
            self.APPENGINE_API, self.APPENGINE_API_VERSION, no_http=True))
    self.mock_client.Mock()
    # If any API calls were made but weren't expected, this will throw an error
    self.addCleanup(self.mock_client.Unmock)

  def ExpectCreateDomainMapping(self, domain, certificate_id, management_type):
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

  def ExpectUpdateDomainMapping(self, domain, certificate_id, management_type,
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

  def ExpectListDomainMappings(self, mappings):
    """Adds expected domain-mappings list request and response.

    Args:
      mappings: messages.DomainMapping[], list of domains to expect.
    """
    request = self.messages.AppengineAppsDomainMappingsListRequest(
        parent=self._FormatApp())
    response = self.messages.ListDomainMappingsResponse(domainMappings=mappings)
    self.mock_client.AppsDomainMappingsService.List.Expect(
        request, response=response)

  def ExpectDeleteDomainMapping(self, domain):
    """Adds expected domain-mappings delete request and response.

    Args:
     domain: str, the custom domain string.
    """
    request = self.messages.AppengineAppsDomainMappingsDeleteRequest(
        name=self._FormatDomainMappings(domain))
    self.mock_client.AppsDomainMappingsService.Delete.Expect(
        request, response=self.messages.Operation(done=True))
