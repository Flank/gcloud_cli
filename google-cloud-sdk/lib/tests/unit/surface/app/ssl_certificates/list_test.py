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
"""Tests for gcloud app ssl-certificates."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.app import ssl_certificates_base

CERTIFICATE = 'cert_data'
PRIVATE_KEY = 'key_data'


class SslCertificatesListTest(ssl_certificates_base.SslCertificatesBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.certificate_file = self.Touch(
        self.temp_path, 'cert.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private.key', contents=PRIVATE_KEY)

  def _MakeExampleCert(self, cert_id):
    return self.MakeSslCertificate(
        cert_id=cert_id,
        display_name='example{}.com'.format(cert_id),
        certificate_data='cert_data{}'.format(cert_id),
        private_key_data='key_data{}'.format(cert_id),
        domain_names=['example{}.com'.format(cert_id)])

  def testListSslCertificates(self):
    certificates = [self._MakeExampleCert('123'), self._MakeExampleCert('456')]

    self.ExpectListSslCertificates(certificates)
    self.Run('app ssl-certificates list')
    self.AssertOutputEquals(
        """\
        ID    DISPLAY_NAME    DOMAIN_NAMES
        123   example123.com  example123.com
        456   example456.com  example456.com
        """,
        normalize_space=True)


class SslCertificatesListBetaTest(
    ssl_certificates_base.SslCertificatesBetaBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.certificate_file = self.Touch(
        self.temp_path, 'cert.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private.key', contents=PRIVATE_KEY)

  def _MakeExampleCert(self, cert_id, cert_status):
    return self.MakeSslCertificate(
        cert_id=cert_id,
        display_name='example{}.com'.format(cert_id),
        certificate_data='cert_data{}'.format(cert_id),
        private_key_data='key_data{}'.format(cert_id),
        domain_names=['example{}.com'.format(cert_id)],
        managed_cert_status=(
            self.messages.ManagedCertificate.StatusValueValuesEnum.
            MANAGEMENT_STATUS_UNSPECIFIED))

  def testListSslCertificates(self):
    certificates = [
        self._MakeExampleCert('123', None),
        self._MakeExampleCert(
            '456', self.messages.ManagedCertificate.StatusValueValuesEnum.OK)
    ]

    self.ExpectListSslCertificates(certificates)
    self.Run('app ssl-certificates list')
    self.AssertOutputEquals(
        """\
        ID   DISPLAY_NAME    DOMAIN_NAMES    MANAGED_CERTIFICATE_STATUS
        123  example123.com  example123.com  MANAGEMENT_STATUS_UNSPECIFIED
        456  example456.com  example456.com  MANAGEMENT_STATUS_UNSPECIFIED
        """,
        normalize_space=True)
