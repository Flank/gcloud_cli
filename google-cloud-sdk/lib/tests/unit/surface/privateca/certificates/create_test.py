# Lint as: python3
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
"""Tests for creating a certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import key_generation
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import mock


class CreateTest(cli_test_base.CliTestBase, sdk_test_base.WithTempCWD,
                 sdk_test_base.WithFakeAuth, sdk_test_base.WithLogCapture):

  def SetUp(self):
    self.mock_client = api_mock.Client(
        privateca_base.GetClientClass(),
        real_client=privateca_base.GetClientInstance())
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = privateca_base.GetMessagesModule()

    self.test_cert = files.ReadFileContents(
        self.Resource('tests', 'unit', 'surface', 'privateca', 'test_data',
                      'test_cert.pem'))
    self.parent_cert = ('----BEGIN CERTIFICATE----\ntest\n----END '
                        'CERTIFICATE----')

  def _ExpectGetCa(self, ca_name, ca_tier=None):
    ca_tier = ca_tier or self.messages.CertificateAuthority.TierValueValuesEnum.ENTERPRISE
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=self.messages
        .PrivatecaProjectsLocationsCertificateAuthoritiesGetRequest(
            name=ca_name),
        response=self.messages.CertificateAuthority(name=ca_name, tier=ca_tier))

  def _ExpectCreateCertificate(self,
                               parent_name,
                               cert_id,
                               request_id,
                               public_key,
                               lifetime='P30D',
                               reusable_config=None,
                               subject_config=None,
                               include_name=False,
                               labels=None):
    reusable_config = reusable_config or self.messages.ReusableConfigWrapper()
    subject_config = subject_config or self.messsages.SubjectConfig(
        subject=self.messages.Subject,
        subjectAltName=self.messages.SubjectAltNames())
    lifetime = times.FormatDurationForJson(times.ParseDuration(lifetime))
    response = self.messages.Certificate(
        pemCertificate=self.test_cert,
        pemCertificateChain=[self.parent_cert])
    if include_name:
      response.name = '{}/certificate/{}'.format(parent_name, cert_id)

    request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesCreateRequest(
        certificateId=cert_id,
        requestId=request_id,
        parent=parent_name,
        certificate=self.messages.Certificate(
            lifetime=lifetime,
            config=self.messages.CertificateConfig(
                reusableConfig=reusable_config,
                subjectConfig=subject_config,
                publicKey=self.messages.PublicKey(
                    type=self.messages.PublicKey.TypeValueValuesEnum
                    .PEM_RSA_KEY,
                    key=public_key)),
            labels=labels))

    self.mock_client.projects_locations_certificateAuthorities_certificates.Create.Expect(
        request=request, response=response)

  def _MakeIsCaReusableConfig(self, is_ca):
    return self.messages.ReusableConfigWrapper(
        reusableConfigValues=self.messages.ReusableConfigValues(
            keyUsage=self.messages.KeyUsage(
                baseKeyUsage=self.messages.KeyUsageOptions(),
                extendedKeyUsage=self.messages.ExtendedKeyUsageOptions()),
            caOptions=self.messages.CaOptions(isCa=is_ca)))

  @mock.patch.object(
      request_utils, 'GenerateRequestId', return_value='create_id')
  @mock.patch.object(
      certificate_utils, 'GenerateCertId', return_value='00000000-AAA-AAA')
  @mock.patch.object(
      key_generation, 'RSAKeyGen', return_value=(b'private', b'public'))
  def testCreateKeyGen(self, key_gen_mock, cert_name_mock, request_id_mock):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    self._ExpectGetCa(parent_name)
    self._ExpectCreateCertificate(
        parent_name,
        cert_name_mock.return_value,
        request_id=request_id_mock.return_value,
        public_key=key_gen_mock.return_value[1],
        reusable_config=self._MakeIsCaReusableConfig(is_ca=False),
        subject_config=self.messages.SubjectConfig(
            commonName='google.com',
            subject=self.messages.Subject(
                organizationalUnit='organizationUnit', locality='locality'),
            subjectAltName=self.messages.SubjectAltNames()))

    self.Run('beta privateca certificates create --issuer ca --issuer-location'
             ' europe --cert-output-file cert_out.pem --generate-key '
             '--key-output-file private_key.pem --no-is-ca-cert '
             '--subject "CN=google.com, OU=organizationUnit, L=locality"')

    self.AssertFileEquals('private', 'private_key.pem')
    self.AssertFileEquals(self.test_cert + '\n' + self.parent_cert,
                          'cert_out.pem')

  @mock.patch.object(
      request_utils, 'GenerateRequestId', return_value='create_id')
  @mock.patch.object(
      key_generation, 'RSAKeyGen', return_value=(b'private', b'public'))
  def testCreateKeyGenWithAltNames(self, key_gen_mock, request_id_mock):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    self._ExpectGetCa(parent_name)
    self._ExpectCreateCertificate(
        parent_name,
        'cert',
        request_id=request_id_mock.return_value,
        public_key=key_gen_mock.return_value[1],
        lifetime='P20Y',
        reusable_config=self._MakeIsCaReusableConfig(is_ca=False),
        subject_config=self.messages.SubjectConfig(
            subject=self.messages.Subject(),
            subjectAltName=self.messages.SubjectAltNames(
                emailAddresses=['email1@gmail.com', 'email2@gmail.com'],
                ipAddresses=['1.1.1.1'])))

    self.Run('beta privateca certificates create cert --issuer ca '
             '--issuer-location europe --cert-output-file cert_out.pem '
             '--generate-key --key-output-file private_key.pem '
             '--email-san email1@gmail.com,email2@gmail.com --ip-san 1.1.1.1 '
             '--validity P20Y --no-is-ca-cert')

  @mock.patch.object(
      request_utils, 'GenerateRequestId', return_value='create_id')
  @mock.patch.object(
      key_generation, 'RSAKeyGen', return_value=(b'private', b'public'))
  def testCreateKeyGenWithSubjectAndSan(self, key_gen_mock, request_id_mock):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    self._ExpectGetCa(parent_name)
    self._ExpectCreateCertificate(
        parent_name,
        'cert',
        request_id=request_id_mock.return_value,
        public_key=key_gen_mock.return_value[1],
        reusable_config=self._MakeIsCaReusableConfig(is_ca=False),
        subject_config=self.messages.SubjectConfig(
            commonName='google.com',
            subject=self.messages.Subject(organization='google'),
            subjectAltName=self.messages.SubjectAltNames(
                emailAddresses=['email1@gmail.com', 'email2@gmail.com'],
                ipAddresses=['1.1.1.1'])))

    self.Run('beta privateca certificates create cert --issuer ca '
             '--issuer-location europe --cert-output-file cert_out.pem '
             '--generate-key --key-output-file private_key.pem '
             '--email-san email1@gmail.com,email2@gmail.com --ip-san 1.1.1.1 '
             '--subject CN=google.com,O=google')

  @mock.patch.object(
      request_utils, 'GenerateRequestId', return_value='create_id')
  @mock.patch.object(
      key_generation, 'RSAKeyGen', return_value=(b'private', b'public'))
  def testReusableConfig(self, key_gen_mock, request_id_mock):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    reusable_config_name = 'projects/project/locations/loc/reusableConfigs/config'
    self._ExpectGetCa(parent_name)
    self._ExpectCreateCertificate(
        parent_name,
        'cert',
        request_id=request_id_mock.return_value,
        public_key=key_gen_mock.return_value[1],
        reusable_config=self.messages.ReusableConfigWrapper(
            reusableConfig=reusable_config_name),
        subject_config=self.messages.SubjectConfig(
            commonName='google.com',
            subject=self.messages.Subject(organization='google'),
            subjectAltName=self.messages.SubjectAltNames()))

    self.Run(('beta privateca certificates create cert --issuer ca '
              '--issuer-location europe --cert-output-file cert_out.pem '
              '--generate-key --key-output-file private_key.pem '
              '--reusable-config {} '
              '--subject CN=google.com,O=google').format(reusable_config_name))

  @mock.patch.object(
      request_utils, 'GenerateRequestId', return_value='create_id')
  @mock.patch.object(
      key_generation, 'RSAKeyGen', return_value=(b'private', b'public'))
  def testReusableConfigValues(self, key_gen_mock, request_id_mock):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    self._ExpectGetCa(parent_name)
    self._ExpectCreateCertificate(
        parent_name,
        'cert',
        request_id=request_id_mock.return_value,
        public_key=key_gen_mock.return_value[1],
        reusable_config=self.messages.ReusableConfigWrapper(
            reusableConfigValues=self.messages.ReusableConfigValues(
                keyUsage=self.messages.KeyUsage(
                    baseKeyUsage=self.messages.KeyUsageOptions(
                        digitalSignature=True, certSign=True, crlSign=True),
                    extendedKeyUsage=self.messages.ExtendedKeyUsageOptions(
                        clientAuth=True, serverAuth=True)),
                caOptions=self.messages.CaOptions(
                    isCa=True, maxIssuerPathLength=3))),
        subject_config=self.messages.SubjectConfig(
            commonName='google.com',
            subject=self.messages.Subject(organization='google'),
            subjectAltName=self.messages.SubjectAltNames()))

    self.Run(
        'beta privateca certificates create cert --issuer ca '
        '--issuer-location europe --cert-output-file cert_out.pem '
        '--generate-key --key-output-file private_key.pem '
        '--extended-key-usages client_auth,server_auth '
        '--key-usages digital_signature,cert_sign '
        '--subject CN=google.com,O=google --is-ca-cert --max-chain-length 3')

  def testDevOpsWithoutCertOutputFileFails(self):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    self._ExpectGetCa(
        parent_name,
        self.messages.CertificateAuthority.TierValueValuesEnum.DEVOPS)

    with self.AssertRaisesExceptionRegexp(exceptions.RequiredArgumentException,
                                          '--cert-output-file'):
      self.Run(
          'beta privateca certificates create cert --issuer ca '
          '--issuer-location europe '
          '--generate-key --key-output-file private_key.pem '
          '--subject CN=google.com,O=google')

  @mock.patch.object(
      request_utils, 'GenerateRequestId', return_value='create_id')
  @mock.patch.object(
      key_generation, 'RSAKeyGen', return_value=(b'private', b'public'))
  def testDevOpsWithCertIdLogsWarning(self, key_gen_mock, request_id_mock):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    self._ExpectGetCa(
        parent_name,
        self.messages.CertificateAuthority.TierValueValuesEnum.DEVOPS)
    self._ExpectCreateCertificate(
        parent_name,
        'explicit-cert-id',
        request_id=request_id_mock.return_value,
        public_key=key_gen_mock.return_value[1],
        reusable_config=self._MakeIsCaReusableConfig(is_ca=False),
        subject_config=self.messages.SubjectConfig(
            subject=self.messages.Subject(),
            subjectAltName=self.messages.SubjectAltNames(
                dnsNames=['example.com'])))

    self.Run('beta privateca certificates create explicit-cert-id --issuer ca '
             '--issuer-location europe --cert-output-file cert_out.pem '
             '--generate-key --key-output-file private_key.pem '
             '--dns-san example.com')
    self.AssertErrContains('certificate ID was specified but will not be used')

  @mock.patch.object(
      request_utils, 'GenerateRequestId', return_value='create_id')
  @mock.patch.object(
      certificate_utils, 'GenerateCertId', return_value='00000000-AAA-AAA')
  @mock.patch.object(
      key_generation, 'RSAKeyGen', return_value=(b'private', b'public'))
  def testDevOpsWithLabelsLogsWarning(self, key_gen_mock, cert_name_mock,
                                      request_id_mock):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    self._ExpectGetCa(
        parent_name,
        self.messages.CertificateAuthority.TierValueValuesEnum.DEVOPS)
    self._ExpectCreateCertificate(
        parent_name,
        cert_name_mock.return_value,
        request_id=request_id_mock.return_value,
        public_key=key_gen_mock.return_value[1],
        reusable_config=self._MakeIsCaReusableConfig(is_ca=False),
        subject_config=self.messages.SubjectConfig(
            subject=self.messages.Subject(),
            subjectAltName=self.messages.SubjectAltNames(
                dnsNames=['example.com'])),
        labels=self.messages.Certificate.LabelsValue(
            additionalProperties=[
                self.messages.Certificate.LabelsValue.AdditionalProperty(
                    key='foo', value='bar')]))

    self.Run('beta privateca certificates create --issuer ca '
             '--issuer-location europe --cert-output-file cert_out.pem '
             '--generate-key --key-output-file private_key.pem '
             '--dns-san example.com --labels "foo=bar"')
    self.AssertErrContains('labels was specified but will not be used')

  @mock.patch.object(
      request_utils, 'GenerateRequestId', return_value='create_id')
  @mock.patch.object(
      key_generation, 'RSAKeyGen', return_value=(b'private', b'public'))
  def testDevOpsWithCertIdAndLabelsLogsWarning(self, key_gen_mock,
                                               request_id_mock):
    parent_name = 'projects/fake-project/locations/europe/certificateAuthorities/ca'
    self._ExpectGetCa(
        parent_name,
        self.messages.CertificateAuthority.TierValueValuesEnum.DEVOPS)
    self._ExpectCreateCertificate(
        parent_name,
        'explicit-cert-id',
        request_id=request_id_mock.return_value,
        public_key=key_gen_mock.return_value[1],
        reusable_config=self._MakeIsCaReusableConfig(is_ca=False),
        subject_config=self.messages.SubjectConfig(
            subject=self.messages.Subject(),
            subjectAltName=self.messages.SubjectAltNames(
                dnsNames=['example.com'])),
        labels=self.messages.Certificate.LabelsValue(
            additionalProperties=[
                self.messages.Certificate.LabelsValue.AdditionalProperty(
                    key='foo', value='bar')]))

    self.Run('beta privateca certificates create explicit-cert-id --issuer ca '
             '--issuer-location europe --cert-output-file cert_out.pem '
             '--generate-key --key-output-file private_key.pem '
             '--dns-san example.com --labels "foo=bar"')
    self.AssertErrContains('certificate ID, labels were specified but will not '
                           'be used')
