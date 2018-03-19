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
"""Base class for domain_mappings tests."""

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

  def MakeDomainMapping(self, domain, certificate_id):
    ssl = self.messages.SslSettings(certificateId=certificate_id)
    return self.messages.DomainMapping(id=domain, sslSettings=ssl)

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


class DomainMappingsBetaBase(DomainMappingsBase):
  """Base class for DomainMappings tests against Beta client."""

  APPENGINE_API_VERSION = 'v1beta'

  def _ManagementTypeFromString(self, management_type):
    return self.messages.SslSettings.SslManagementTypeValueValuesEnum(
        management_type.upper()) if management_type else None

  def MakeDomainMapping(self, domain, certificate_id, management_type):
    mapping = super(DomainMappingsBetaBase, self).MakeDomainMapping(
        domain, certificate_id)
    if management_type is not None:
      mapping.sslSettings.sslManagementType = management_type
    return mapping
