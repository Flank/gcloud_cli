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
"""Base class for ssl_certificates tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class SslCertificatesBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):
  """Base class for all SslCertificates tests."""

  APPENGINE_API = 'appengine'
  APPENGINE_API_VERSION = 'v1'

  def _FormatApp(self):
    return 'apps/{0}'.format(self.Project())

  def _FormatSslCertificates(self, cert_id):
    uri = self._FormatApp() + '/authorizedCertificates'
    if cert_id:
      uri += '/' + cert_id
    return uri

  def MakeSslCertificate(self,
                         cert_id,
                         display_name,
                         certificate_data,
                         private_key_data,
                         domain_names=None,
                         expire_time=None,
                         visible_domain_mappings=None):
    cert = self.messages.CertificateRawData(
        privateKey=private_key_data, publicCertificate=certificate_data)

    if domain_names is None:
      domain_names = []
    if visible_domain_mappings is None:
      visible_domain_mappings = []

    name = None
    if cert_id:
      name = self._FormatSslCertificates(cert_id)

    return self.messages.AuthorizedCertificate(
        id=cert_id,
        name=name,
        displayName=display_name,
        certificateRawData=cert,
        domainNames=domain_names,
        expireTime=expire_time,
        visibleDomainMappings=visible_domain_mappings)

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

  def ExpectListSslCertificates(self, certificates):
    """Adds expected ssl-certificates list request and response.

    Args:
      certificates: messages.SslCertificate[], list of certificates to expect.
    """
    request = self.messages.AppengineAppsAuthorizedCertificatesListRequest(
        parent=self._FormatApp())
    response = self.messages.ListAuthorizedCertificatesResponse(
        certificates=certificates)
    self.mock_client.AppsAuthorizedCertificatesService.List.Expect(
        request, response=response)

  def ExpectDeleteSslCertificate(self, cert_id):
    """Adds expected ssl-certificates delete request and response.

    Args:
     cert_id: str, the id of the certificate to delete.
    """
    request = self.messages.AppengineAppsAuthorizedCertificatesDeleteRequest(
        name=self._FormatSslCertificates(cert_id))
    response = self.messages.Empty()
    self.mock_client.AppsAuthorizedCertificatesService.Delete.Expect(
        request, response=response)

  def ExpectGetSslCertificate(self, cert_id, display_name, certificate_data,
                              private_key_data):
    """Adds expected ssl-certificates describe request and response.

    Args:
      cert_id: str, the id of the certificate.
      display_name: str, the display name for the new certificate.
      certificate_data: str, string data of a certificate file.
      private_key_data: str, string data of private key file.
    """
    request = self.messages.AppengineAppsAuthorizedCertificatesGetRequest(
        name=self._FormatSslCertificates(cert_id))
    request.view = (self.messages.AppengineAppsAuthorizedCertificatesGetRequest.
                    ViewValueValuesEnum.FULL_CERTIFICATE)
    response = self.MakeSslCertificate(cert_id, display_name, certificate_data,
                                       private_key_data)
    self.mock_client.AppsAuthorizedCertificatesService.Get.Expect(
        request, response=response)

  def ExpectCreateSslCertificate(self, cert_id, display_name, certificate_data,
                                 private_key_data):
    """Adds expected ssl-certificates create request and response.

    Args:
      cert_id: str, the id of the certificate.
      display_name: str, the display name for the new certificate.
      certificate_data: str, string data of a certificate file.
      private_key_data: str, string data of private key file.
    """
    request_cert = self.MakeSslCertificate(None, display_name, certificate_data,
                                           private_key_data)
    request_cert.name = None
    response_cert = self.MakeSslCertificate('1234', display_name,
                                            certificate_data, private_key_data)
    request = self.messages.AppengineAppsAuthorizedCertificatesCreateRequest(
        parent=self._FormatApp(), authorizedCertificate=request_cert)
    self.mock_client.AppsAuthorizedCertificatesService.Create.Expect(
        request, response=response_cert)

  def ExpectUpdateSslCertificate(self, cert_id, display_name, certificate_data,
                                 private_key_data, mask):
    """Adds expected ssl-certificates create request and response.

    Args:
      cert_id: str, the id of the certificate.
      display_name: str, the display name for the new certificate.
      certificate_data: str, string data of a certificate file.
      private_key_data: str, string data of private key file.
      mask: str, a comma separated list of included fields to expect.
    """
    request_cert = self.MakeSslCertificate(None, display_name, certificate_data,
                                           private_key_data)
    response_cert = self.MakeSslCertificate(cert_id, display_name,
                                            certificate_data, private_key_data)
    request = self.messages.AppengineAppsAuthorizedCertificatesPatchRequest(
        name=self._FormatSslCertificates(cert_id),
        authorizedCertificate=request_cert,
        updateMask=mask)
    self.mock_client.AppsAuthorizedCertificatesService.Patch.Expect(
        request, response=response_cert)


class SslCertificatesBetaBase(SslCertificatesBase):
  """Base class for all SslCertificates Beta tests."""

  APPENGINE_API_VERSION = 'v1beta'

  def MakeSslCertificate(self,
                         cert_id,
                         display_name,
                         certificate_data,
                         private_key_data,
                         managed_cert_status=None,
                         domain_names=None,
                         expire_time=None,
                         visible_domain_mappings=None):
    """Makes an SSL certificate including managed_cert_status."""
    cert = super(SslCertificatesBetaBase, self).MakeSslCertificate(
        cert_id, display_name, certificate_data, private_key_data, domain_names,
        expire_time, visible_domain_mappings)
    if managed_cert_status is not None:
      cert.managedCertificate = self.messages.ManagedCertificate(
          status=managed_cert_status)
    return cert
