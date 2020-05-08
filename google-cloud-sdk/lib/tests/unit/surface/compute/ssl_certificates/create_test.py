# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the SSL certificates create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


CERTIFICATE = textwrap.dedent("""\
    -----BEGIN CERTIFICATE-----
    MIICZzCCAdACCQChX1chr91razANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV
    UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE
    CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj
    bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMzExNVoXDTE1MTAxMzIwMzExNVoweDEL
    MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0
    bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw
    FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC
    gYEAq3S7ZDKHHwdro6f9Zxk8kNZ39a2ejqls4LMropt+RpkHqpaQK17Q2rUykw+f
    P+mXojUB1ZUKkrCE+xcEHeafUgG1lBof56v2bSzIQVeeS1chvDNYGqweEHIkbFHv
    8e8RY9XPkk4hMcW+uxrzaKv1yddBucyETLa3/dYmaEzHcOsCAwEAATANBgkqhkiG
    9w0BAQsFAAOBgQAxBD6GUsgGYfeHkjo3CK/X5cbaPTdUncD13uaI4Q31GWZGhGJX
    t9hMvJdXQ6vzKXBuX6ZLUxvL9SFT+pMLTWGStUFNcDFv/Fqdcre0jPoYEJv/tOHT
    n82GtW9nMhZfVj2PrRiuZwOV8qB6+uEadbcPcET3TcH1WJacbBlHufk1wQ==
    -----END CERTIFICATE-----
    """)

PRIVATE_KEY = textwrap.dedent("""\
    -----BEGIN RSA PRIVATE KEY-----
    Proc-Type: 4,ENCRYPTED
    DEK-Info: DES-EDE3-CBC,6777341B13232A03

    mfzbKgnJFQUBSVrOId386jSKxlzKAavsYotDhT+GwJeQUAiaDkTYQd2iGK2sFvv5
    rjQprtEyGZVWceL5e05u/j0N50hJ6YGPjcZ2OxUeVdR2ALbVc6va8LQ5q/rkmSyj
    DMrrDoniCtnqQRu63sYd/fapftyi3JO3Iahy8LaCm4L1KLmS0WuHulQbtChhYI/p
    pOZ5KEH6EdCCdBug/Q9I7iKQ+NzneS2M/eu5gIlTJ5VR/47ZDnZUZWEoR2ULcZ/4
    14SsYO+n6J+QNsOu/T5xpv+Qdpi6bi3B2J65HNoSnWwxZie/C3znoouj9EH3XrMu
    ccPPFdF7ZGZtZ9ohAoA3fEue0xc1X51uIRhiDX+4oQcvIFf0bwQeCfIeCnzL4tsf
    9Px6xit3hggp9pdFR33tF6UHKKPS8mclx1I7pdCaTaLwEPHeBuyLKaAXURo02k2w
    gQQJxKqY6rafHSlwE2JGcFOnnvUq/IGExDYC3gbHLmKobHG3IOnFj7pTKh8MB5Nr
    ia54VMMpUcQBUX/jSza3+Je4VaHY9uaWfZpEN3khKArW165b5v6GeDnyYXx/RxLh
    BI2mpyxXLfVXuyqZgFxw2qX43jfmA5kA3hNseexzaQW3CXuvyBs1OmqO4ZW7V//x
    GsZQiRF2A5mw3eCPVA3XcitBL7dB+/Ff2zzmFC/X4wbB7BdRpim8tpx0hZkuQwTZ
    G85IWr8uPZVmmva4HL6sJq11KFqkt9nmZmGCa99ZxeeBP6mNBGp5YiPLU982jMqO
    PZllIfthbvSCkCt+N7uats73RFioYtvvAt6oQf0xdvw=
    -----END RSA PRIVATE KEY-----
    """)


class SslCertificatesCreateTest(test_base.BaseTest, parameterized.TestCase):

  def SetUp(self):
    self.certificate_file = self.Touch(
        self.temp_path, 'certificate.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private-key.key', contents=PRIVATE_KEY)
    self.SelectApi('v1')
    self.prefix = ''

  def RunVersioned(self, command):
    return self.Run('{prefix} {command}'.format(
        prefix=self.prefix, command=command))

  def testSimpleCase(self):
    messages = self.messages

    self.RunVersioned("""
        compute ssl-certificates create my-cert
          --certificate {certificate_file}
          --private-key {key_file}
          --description 'Certificate one.'
        """.format(
            certificate_file=self.certificate_file,
            key_file=self.private_key_file))

    self.CheckRequests(
        [(self.compute.sslCertificates, 'Insert',
          messages.ComputeSslCertificatesInsertRequest(
              sslCertificate=messages.SslCertificate(
                  name='my-cert',
                  description='Certificate one.',
                  certificate=CERTIFICATE,
                  privateKey=PRIVATE_KEY,
              ),
              project='my-project'))],)

  def testSimpleCaseRegion(self):
    messages = self.messages

    self.RunVersioned("""
        compute ssl-certificates create my-cert
          --region us-west1
          --certificate {certificate_file}
          --private-key {key_file}
          --description 'Certificate one.'
        """.format(
            certificate_file=self.certificate_file,
            key_file=self.private_key_file))

    self.CheckRequests(
        [(self.compute.regionSslCertificates, 'Insert',
          messages.ComputeRegionSslCertificatesInsertRequest(
              sslCertificate=messages.SslCertificate(
                  name='my-cert',
                  description='Certificate one.',
                  certificate=CERTIFICATE,
                  privateKey=PRIVATE_KEY,
              ),
              project='my-project',
              region='us-west1'))],)

  @parameterized.parameters((['example.com'],),
                            (['one.example.com', 'two.example.com'],),
                            (['Ṳᾔḯ¢◎ⅾℯ.certsbridge.com'],),
                            (['xn--8a342m2fai5b18csni3w.certsbridge'],))
  def testManaged(self, domains):
    messages = self.messages

    self.RunVersioned("""
        compute ssl-certificates create my-cert-managed
          --domains {domains}
          --description 'Managed certificate one.'
        """.format(domains=','.join(domains)))

    self.CheckRequests(
        [(self.compute.sslCertificates, 'Insert',
          messages.ComputeSslCertificatesInsertRequest(
              sslCertificate=messages.SslCertificate(
                  name='my-cert-managed',
                  type=messages.SslCertificate.TypeValueValuesEnum.MANAGED,
                  description='Managed certificate one.',
                  managed=messages.SslCertificateManagedSslCertificate(
                      domains=domains),
              ),
              project='my-project'))],)

  @parameterized.parameters((['example.com'],),
                            (['one.example.com', 'two.example.com'],),
                            (['Ṳᾔḯ¢◎ⅾℯ.certsbridge.com'],),
                            (['xn--8a342m2fai5b18csni3w.certsbridge'],))
  def testManagedRegion(self, domains):
    messages = self.messages

    self.RunVersioned("""
        compute ssl-certificates create my-cert-managed
          --domains {domains}
          --description 'Managed certificate one.'
        """.format(domains=','.join(domains)))

    self.CheckRequests(
        [(self.compute.sslCertificates, 'Insert',
          messages.ComputeSslCertificatesInsertRequest(
              sslCertificate=messages.SslCertificate(
                  name='my-cert-managed',
                  type=messages.SslCertificate.TypeValueValuesEnum.MANAGED,
                  description='Managed certificate one.',
                  managed=messages.SslCertificateManagedSslCertificate(
                      domains=domains),
              ),
              project='my-project'))],)

  def testUriSupport(self):
    messages = self.messages

    self.RunVersioned("""
        compute ssl-certificates create
            {base_uri}/projects/my-project/global/sslCertificates/my-cert
          --certificate {certificate_file}
          --private-key {key_file}
        """.format(
            base_uri=self.compute_uri,
            certificate_file=self.certificate_file,
            key_file=self.private_key_file))

    self.CheckRequests(
        [(self.compute.sslCertificates, 'Insert',
          messages.ComputeSslCertificatesInsertRequest(
              sslCertificate=messages.SslCertificate(
                  name='my-cert',
                  certificate=CERTIFICATE,
                  privateKey=PRIVATE_KEY,
              ),
              project='my-project'))],)

  def testUriSupportRegion(self):
    messages = self.messages

    self.RunVersioned("""
        compute ssl-certificates create
            {base_uri}/projects/my-project/regions/us-west-1/sslCertificates/my-cert
          --certificate {certificate_file}
          --private-key {key_file}
        """.format(
            base_uri=self.compute_uri,
            certificate_file=self.certificate_file,
            key_file=self.private_key_file))

    self.CheckRequests(
        [(self.compute.regionSslCertificates, 'Insert',
          messages.ComputeRegionSslCertificatesInsertRequest(
              sslCertificate=messages.SslCertificate(
                  name='my-cert',
                  certificate=CERTIFICATE,
                  privateKey=PRIVATE_KEY,
              ),
              region='us-west-1',
              project='my-project'))],)

  def testNoDomain(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --domains: not enough args'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            '--domains='
                        """)

    self.CheckRequests()

  def testWithoutCertificate(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --certificate: Must be specified.'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --private-key {key_file}
          """.format(key_file=self.private_key_file))

    self.CheckRequests()

  def testWithoutCertificateRegion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --certificate: Must be specified.'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --region us-west1
            --private-key {key_file}
          """.format(key_file=self.private_key_file))

    self.CheckRequests()

  def testWithoutPrivateKey(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --private-key: Must be specified.'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --certificate {certificate_file}
          """.format(certificate_file=self.certificate_file))

    self.CheckRequests()

  def testWithoutPrivateKeyRegion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --private-key: Must be specified.'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --region us-west-1
            --certificate {certificate_file}
          """.format(certificate_file=self.certificate_file))

    self.CheckRequests()

  def testWithoutCertificateFile(self):
    with self.assertRaisesRegex(
        files.Error, r'Unable to read file \[not-certificate.crt\]: '
        r'.*No such file or directory'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --certificate not-certificate.crt
            --private-key {key_file}
          """.format(key_file=self.private_key_file))

    self.CheckRequests()

  def testWithoutCertificateFileRegion(self):
    with self.assertRaisesRegex(
        files.Error, r'Unable to read file \[not-certificate.crt\]: '
        r'.*No such file or directory'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --region us-west1
            --certificate not-certificate.crt
            --private-key {key_file}
          """.format(key_file=self.private_key_file))

    self.CheckRequests()

  def testWithoutPrivateKeyFile(self):
    with self.assertRaisesRegex(
        files.Error, r'Unable to read file \[non-existent.key\]: '
        r'.*No such file or directory'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --certificate {certificate_file}
            --private-key non-existent.key
          """.format(certificate_file=self.certificate_file))

  def testWithoutPrivateKeyFileRegion(self):
    with self.assertRaisesRegex(
        files.Error, r'Unable to read file \[non-existent.key\]: '
        r'.*No such file or directory'):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --region us-west-1
            --certificate {certificate_file}
            --private-key non-existent.key
          """.format(certificate_file=self.certificate_file))

  def testWithDomainsAndCertificate(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --certificate {certificate_file}
            --domains example.com
          """.format(certificate_file=self.certificate_file))

    self.CheckRequests()

  def testWithDomainsAndCertificateRegion(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --region us-west1
            --certificate {certificate_file}
            --domains example.com
          """.format(certificate_file=self.certificate_file))

    self.CheckRequests()

  def testWithDomainsAndPrivateKey(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --domains example.com
            --private-key {key_file}
          """.format(key_file=self.private_key_file))

    self.CheckRequests()

  def testWithDomainsAndPrivateKeyRegion(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunVersioned("""
          compute ssl-certificates create my-cert
            --region us-west-1
            --domains example.com
            --private-key {key_file}
          """.format(key_file=self.private_key_file))

    self.CheckRequests()


class SslCertificatesCreateBetaTest(SslCertificatesCreateTest,
                                    parameterized.TestCase):

  def SetUp(self):
    self.SelectApi('beta')
    self.SetEncoding('utf8')
    self.prefix = 'beta'


class SslCertificatesCreateAlphaTest(SslCertificatesCreateTest,
                                     parameterized.TestCase):

  def SetUp(self):
    self.SelectApi('alpha')
    self.SetEncoding('utf8')
    self.prefix = 'alpha'


if __name__ == '__main__':
  test_case.main()
