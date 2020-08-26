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
"""Tests that exercise 'gcloud kms keys versions get-certificate-chain'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base

CAVIUM_PARTITION_CERT = """-----BEGIN CERTIFICATE-----
  MIIDgjCCAmqgAwIBAgIBATANBgkqhkiG9w0BAQsFADB6MUQwCQYDVQQGEwJVUzAJ
  BgNVBAgMAkNBMA0GA1UECgwGQ2F2aXVtMA0GA1UECwwGTjNGSVBTMA4GA1UEBwwH
  U2FuSm9zZTEyMDAGA1UEAwwpSFNNOjUuMkcxNzQ3LUlDTTAwMDA0OSwgZm9yIG5v
  bi1GSVBTIG1vZGUwHhcNMTgwNjI2MTYxMDE3WhcNMjgwNjIzMTYxMDE3WjCBjjFE
  MAkGA1UEBhMCVVMwCQYDVQQIDAJDQTANBgNVBAoMBkNhdml1bTANBgNVBAsMBk4z
  RklQUzAOBgNVBAcMB1Nhbkpvc2UxRjBEBgNVBAMMPUhTTTpGMzUxRTlBRjlBN0FB
  RDFBODJBRjhERDkwQjZCM0Y6UEFSVE46MSwgZm9yIG5vbi1GSVBTIG1vZGUwggEi
  MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDId3Np+4aCvID2/3BdyKAfatv8
  dhve5oaWb3D5u83FtmahpJ8qiHJCmC/MffcdnXKc4YNY6Rwd/pUDW+hA22SK0EsU
  ZHYrgO3Tiqe367JYAmxOo8+YIv/JtTdM5Mh7bRos+wkSkLgerb3uDPnru6XxiRU4
  wRAYPu6VzctNDaOrQAgdOT3MM2A9fMIY9sJL24QCGVAhtRWj76xZUGyUFJY09O9e
  jS2jtG41Jm22LPYHUC6I7AlqLmdZ6C78ATS4/n+RM5W/hTY4/aEc+8yu5xZgG7mB
  Q14VvO6ehUKQBqzFSRS7zZqFfyb7053kzQASQMN9sCz7YRK0K6LO+w2IGnlxAgMB
  AAEwDQYJKoZIhvcNAQELBQADggEBAGHtSytgLxg+9EWB5TA+yU7bNEfQjyorBPjK
  x7mvCz0Hqh1g1Ss/ImMZXxi5Fv47UwafCe8SWwODD7TWwVAIpxTm5tfPqHshZmBO
  MzUTpfBjwjluxfOdPl2Npd+hPHiQbtvxp14Ok7qodEDWULLUX+g/i10WcUdE0qbN
  6EAJyqMh/UYmVR5BDBm97tJn5rO4jD5I5aODtb9d3bo5x2BRjWwPi9C+O20o0VPq
  XpoM0GL1Fn92tf4vKbs2O+NZf+KjIqAj5P9eBmEmx18JlvQgZyjYb187fYqp6GR8
  KLjb7xR0pKihc4nOMdzLiPizHWtKfr/myLHUumScwEt2bAqUTL8=
  -----END CERTIFICATE-----
  """

CAVIUM_CARD_CERT = """-----BEGIN CERTIFICATE-----
  MIIDiDCCAnACCQDdP5IaPS2UljANBgkqhkiG9w0BAQsFADCBkTELMAkGA1UEBhMC
  VVMxEzARBgNVBAgMCkNhbGlmb3JuaWExETAPBgNVBAcMCFNhbiBKb3NlMRUwEwYD
  VQQKDAxDYXZpdW0sIEluYy4xFzAVBgNVBAsMDkxpcXVpZFNlY3VyaXR5MSowKAYD
  VQQDDCFsb2NhbGNhLmxpcXVpZHNlY3VyaXR5LmNhdml1bS5jb20wHhcNMTcxMjIw
  MDI1NTE4WhcNMjcxMjE4MDI1NTE4WjB6MUQwCQYDVQQGEwJVUzAJBgNVBAgMAkNB
  MA0GA1UECgwGQ2F2aXVtMA0GA1UECwwGTjNGSVBTMA4GA1UEBwwHU2FuSm9zZTEy
  MDAGA1UEAwwpSFNNOjUuMkcxNzQ3LUlDTTAwMDA0OSwgZm9yIG5vbi1GSVBTIG1v
  ZGUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCO2C+lizBSgOlcHhDC
  lEXMLYytKwVKWw6q8w3DBq3cydKHYNZ2AYZ7qmsf8tZubeb6lHaT505JTF5pK+T6
  K424m5SR8vQRg/TSo+f55wgORLvAYa7bMrVBvuXWTQniANGd+wufRPMMjYcaueOn
  DEag5GG5e860j+XrryIUqpGwH9VRc7E98XqlQ9HS2qHhqv4lb2EBRRqTYqy+qYA0
  4awGal8VvjCM1R3bqorL85g+50AFYxb3ms/6DHu5Yo7+b4BIGcx4HZrnr541j0dO
  9NWUIq5AnAK/8T92L4FNfVPyO2biKddF99B7IjvJAS0KLQHv5jCSpciZSrfxilsa
  JAFLAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAKwvejdRnfVbUg77VX/ECpZOqj6r
  Y5VQ3SZ7050RaH4Z335D+TWzImzTq9lhUMYmzPfaLQfhfMlWHG/aMYgfSFG1hlE/
  aoiuM8dVbPxlV1hDGgf6AZT34e5IZ6225XulvYjad+qX72YM5S2z8vKTCmgMxeKD
  s0yd6YNL2FAtGb0UG6p1Lj3OkMPJr177efhHX3qu9vwHxmGBuLaraGnoRY+4lYNm
  cB2+iPhNM15GR9vB+NaIwQjlpjkklMwfwj/CGJpcx0xw5iZHxLg6WMstcUvbCNYP
  Kpr2wPJJqa9MK+YP+tdPvq9dxU7TN4GkPRMpJJhKlSOeVXun0BUYJ+NwuAI=
  -----END CERTIFICATE-----
  """

GOOGLE_CARD_CERT = """-----BEGIN CERTIFICATE-----
  MIIDzDCCArSgAwIBAgIUd2NJS/pbBKKm3Fd3CsquTht7GXgwDQYJKoZIhvcNAQEL
  BQAwZzELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRYwFAYDVQQHDA1Nb3VudGFp
  biBWaWV3MRMwEQYDVQQKDApHb29nbGUgSW5jMR4wHAYDVQQDDBVIYXdrc2JpbGwg
  Um9vdCB2MSBkZXYwHhcNMTgwNjI2MTYxMDI4WhcNMzAwMTAxMDAwMDAwWjB6MUQw
  CQYDVQQGEwJVUzAJBgNVBAgMAkNBMA0GA1UECgwGQ2F2aXVtMA0GA1UECwwGTjNG
  SVBTMA4GA1UEBwwHU2FuSm9zZTEyMDAGA1UEAwwpSFNNOjUuMkcxNzQ3LUlDTTAw
  MDA0OSwgZm9yIG5vbi1GSVBTIG1vZGUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw
  ggEKAoIBAQCO2C+lizBSgOlcHhDClEXMLYytKwVKWw6q8w3DBq3cydKHYNZ2AYZ7
  qmsf8tZubeb6lHaT505JTF5pK+T6K424m5SR8vQRg/TSo+f55wgORLvAYa7bMrVB
  vuXWTQniANGd+wufRPMMjYcaueOnDEag5GG5e860j+XrryIUqpGwH9VRc7E98Xql
  Q9HS2qHhqv4lb2EBRRqTYqy+qYA04awGal8VvjCM1R3bqorL85g+50AFYxb3ms/6
  DHu5Yo7+b4BIGcx4HZrnr541j0dO9NWUIq5AnAK/8T92L4FNfVPyO2biKddF99B7
  IjvJAS0KLQHv5jCSpciZSrfxilsaJAFLAgMBAAGjXTBbMAkGA1UdEwQCMAAwDgYD
  VR0PAQH/BAQDAgWgMB0GA1UdDgQWBBS9TmqbWGuYz5me2wdwgdNomvgbejAfBgNV
  HSMEGDAWgBQspfpXar4CvPl3DmTV65+dSqtr4jANBgkqhkiG9w0BAQsFAAOCAQEA
  JqhALitN61JhVO/zUjgY2Fup+WWkcMU8Z2aD/WwrfGdAKPTHa6Q4hmJXw+Gcnc+U
  0BrBDX5VHLER5nqa37l0fz/NFc6E8C7EwwNYvhI5Q04TrExYJBB+whFvFNxAmjlq
  CLSctScWuQVthlrQOysm/+7I0I80Qlinj77NTJQlhqMLNEUUOEx/H6XwGVlM6Vkf
  PqVb+2WbT2LEJRLm97SS4WIVvdMO5cEbdCIEr42i0/iQvLK3dRzz1sEyhOG3R2m/
  xKCRXwZjkW5LZBSZiqjT0RfnCCD2pY0euiHvVbbCbaFcYGUyWO/8tLpbaR3JVVCt
  xAdn2+KQr8oGCMEyIOfdIw==
  -----END CERTIFICATE-----
  """

GOOGLE_PARTITION_CERT = """-----BEGIN CERTIFICATE-----
  MIID4TCCAsmgAwIBAgIUUchoeWveoYnUVOgTU09iTrGmEpUwDQYJKoZIhvcNAQEL
  BQAwZzELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRYwFAYDVQQHDA1Nb3VudGFp
  biBWaWV3MRMwEQYDVQQKDApHb29nbGUgSW5jMR4wHAYDVQQDDBVIYXdrc2JpbGwg
  Um9vdCB2MSBkZXYwHhcNMTgwNjI2MTYxMDMxWhcNMzAwMTAxMDAwMDAwWjCBjjFE
  MAkGA1UEBhMCVVMwCQYDVQQIDAJDQTANBgNVBAoMBkNhdml1bTANBgNVBAsMBk4z
  RklQUzAOBgNVBAcMB1Nhbkpvc2UxRjBEBgNVBAMMPUhTTTpGMzUxRTlBRjlBN0FB
  RDFBODJBRjhERDkwQjZCM0Y6UEFSVE46MSwgZm9yIG5vbi1GSVBTIG1vZGUwggEi
  MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDId3Np+4aCvID2/3BdyKAfatv8
  dhve5oaWb3D5u83FtmahpJ8qiHJCmC/MffcdnXKc4YNY6Rwd/pUDW+hA22SK0EsU
  ZHYrgO3Tiqe367JYAmxOo8+YIv/JtTdM5Mh7bRos+wkSkLgerb3uDPnru6XxiRU4
  wRAYPu6VzctNDaOrQAgdOT3MM2A9fMIY9sJL24QCGVAhtRWj76xZUGyUFJY09O9e
  jS2jtG41Jm22LPYHUC6I7AlqLmdZ6C78ATS4/n+RM5W/hTY4/aEc+8yu5xZgG7mB
  Q14VvO6ehUKQBqzFSRS7zZqFfyb7053kzQASQMN9sCz7YRK0K6LO+w2IGnlxAgMB
  AAGjXTBbMAkGA1UdEwQCMAAwDgYDVR0PAQH/BAQDAgWgMB0GA1UdDgQWBBSiXHtJ
  8aOj4zmMLpgX3PT5bECoCzAfBgNVHSMEGDAWgBQspfpXar4CvPl3DmTV65+dSqtr
  4jANBgkqhkiG9w0BAQsFAAOCAQEAQnneoohBZMweTVyvKS8zVUL8ICxwtgX+QyBd
  RUCTmlOYOrp2QtYfM3RKnWDAnM0Ru64WH4W2qQegYqFCbpsL76MJ47vOO4J/Bn7l
  2D16/ayG43jsWFc6hhyRm/hAWLezgqNUBbG533+3TaoCBStLek7iB68hbWwwW0cL
  U8i35wXGkH2saUal3vpLQz3tcQd3IsIJ6ceA2CqUFZsKTtrlwmqtqkRhyMcM6FhT
  7Il6kchDUecAMCJl+vv3zyjQo4g6EV8m2K9XznMJu+JPX84xvNdRc7FYxAWVF+mS
  VBf8Z5dIHiBmF7tvUR6xLIUiEbtPuLfEFeKBleNylgw7egZlhg==
  -----END CERTIFICATE-----
  """


class CryptokeysVersionsDescribeTestBeta(base.KmsMockTest,
                                         parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.key_name = self.project_name.CryptoKey('global/my_kr/my_key/')
    self.version_name = self.key_name.Version('3')
    self.attestation = self.messages.KeyOperationAttestation(
        certChains=self.messages.CertificateChains(
            caviumCerts=(CAVIUM_PARTITION_CERT, CAVIUM_CARD_CERT),
            googleCardCerts=(GOOGLE_CARD_CERT,),
            googlePartitionCerts=(GOOGLE_PARTITION_CERT,)))

  def GetTestCryptoKeyVersion(self):
    return self.messages.CryptoKeyVersion(
        name=self.version_name.RelativeName(),
        attestation=self.attestation,
        protectionLevel=self.messages.CryptoKeyVersion
        .ProtectionLevelValueValuesEnum.HSM)

  def ExpectGetCryptoKeyVersion(self, crypto_key_version):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions

    ckv.Get.Expect(
        self.messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=self.version_name.RelativeName()), crypto_key_version)

  def RunWithChainAndOutputFile(self, chain, output_file):
    command = ('kms keys versions get-certificate-chain {version} '
               '--location={location} --keyring={keyring} --key={key} '
               '--certificate-chain-type={chain}').format(
                   version=self.version_name.version_id,
                   location=self.version_name.location_id,
                   keyring=self.version_name.key_ring_id,
                   key=self.version_name.crypto_key_id,
                   chain=chain)
    if output_file:
      command += ' --output-file={output}'.format(output=output_file)
    self.Run(command)

  @parameterized.named_parameters(
      {
          'testcase_name': 'Cavium',
          'chain': 'cavium',
          'expected_pem': CAVIUM_PARTITION_CERT + CAVIUM_CARD_CERT
      }, {
          'testcase_name': 'GoogleCard',
          'chain': 'google-card',
          'expected_pem': GOOGLE_CARD_CERT
      }, {
          'testcase_name': 'GooglePartition',
          'chain': 'google-partition',
          'expected_pem': GOOGLE_PARTITION_CERT
      }, {
          'testcase_name':
              'AllOrUnspecifiedChain',
          'chain':
              'all',
          'expected_pem':
              ''.join((CAVIUM_PARTITION_CERT, CAVIUM_CARD_CERT,
                       GOOGLE_PARTITION_CERT, GOOGLE_CARD_CERT))
      })
  def testGetCertificateChainStdioSuccess(self, chain, expected_pem):
    self.ExpectGetCryptoKeyVersion(self.GetTestCryptoKeyVersion())

    self.RunWithChainAndOutputFile(chain, None)

    self.AssertOutputContains(expected_pem, normalize_space=True)

  @parameterized.named_parameters(
      {
          'testcase_name': 'Cavium',
          'chain': 'cavium',
          'expected_pem': CAVIUM_PARTITION_CERT + CAVIUM_CARD_CERT
      }, {
          'testcase_name': 'GoogleCard',
          'chain': 'google-card',
          'expected_pem': GOOGLE_CARD_CERT
      }, {
          'testcase_name': 'GooglePartition',
          'chain': 'google-partition',
          'expected_pem': GOOGLE_PARTITION_CERT
      }, {
          'testcase_name':
              'AllOrUnspecifiedChain',
          'chain':
              'all',
          'expected_pem':
              ''.join((CAVIUM_PARTITION_CERT, CAVIUM_CARD_CERT,
                       GOOGLE_PARTITION_CERT, GOOGLE_CARD_CERT))
      })
  def testGetCertificateChainSuccess(self, chain, expected_pem):
    self.ExpectGetCryptoKeyVersion(self.GetTestCryptoKeyVersion())
    output_file = self.Touch(self.temp_path)

    self.RunWithChainAndOutputFile(chain, output_file)

    self.AssertFileEquals(expected_pem, output_file)

  def testMissingId(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [version]: version id must be non-empty.'):
      self.Run('kms keys versions get-certificate-chain {0}/cryptoKeyVersions/ '
               '--certificate-chain-type=cavium'.format(
                   self.key_name.RelativeName()))

  def testGetCertificateChainSoftwareKeyVersionThrowsException(self):
    key_version = self.GetTestCryptoKeyVersion()
    key_version.protectionLevel = (
        self.messages.CryptoKeyVersion.ProtectionLevelValueValuesEnum.SOFTWARE)
    self.ExpectGetCryptoKeyVersion(key_version)

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'Certificate chains are only available for HSM key versions.'):
      self.RunWithChainAndOutputFile('cavium', None)

  def testGetCertificateChainPendingKeyVersionThrowsException(self):
    key_version = self.GetTestCryptoKeyVersion()
    key_version.state = (
        self.messages.CryptoKeyVersion.StateValueValuesEnum.PENDING_GENERATION)
    self.ExpectGetCryptoKeyVersion(key_version)

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException,
        'Certificate chains are unavailable until the version is generated.'):
      self.RunWithChainAndOutputFile('cavium', None)

  def testGetCertificateChainInvalidFile(self):
    self.ExpectGetCryptoKeyVersion(self.GetTestCryptoKeyVersion())

    with self.AssertRaisesExceptionMatches(exceptions.BadFileException,
                                           self.temp_path):
      self.RunWithChainAndOutputFile('cavium', self.temp_path)


class CryptokeysVersionsDescribeTestAlpha(CryptokeysVersionsDescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
