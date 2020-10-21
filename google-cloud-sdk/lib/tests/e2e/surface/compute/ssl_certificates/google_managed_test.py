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
"""Integration tests for google managed ssl certificates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import ssl_certificates_base


class GoogleManagedSslCertificateTest(
    ssl_certificates_base.SslCertificatesTestBase):

  def testCreation(self):
    name = self.UniqueName()
    description = 'CertDescription'
    domains = 'example.com'

    def CheckCert(cert):
      self.assertEqual(name, cert.name)
      self.assertEqual(
          self.messages.SslCertificate.TypeValueValuesEnum.MANAGED,
          cert.type)
      self.assertEqual(description, cert.description)

      self.assertEqual([domains], result_list[0].managed.domains)

    # test create
    result = self.Run('compute ssl-certificates create {0} --domains {1} '
                      '--description {2}'.format(name, domains, description))
    result_list = list(result)

    self.ssl_cert_names.append(name)
    self.assertEqual(1, len(result_list))
    CheckCert(result_list[0])

    # test describe
    result = self.Run('compute ssl-certificates describe {0}'.format(name))
    CheckCert(result)

    # test list
    result = self.Run('compute ssl-certificates list')
    result_list = [self.DictToCert(cert)
                   for cert in result if cert['name'] == name]
    self.assertEqual(1, len(result_list))
    CheckCert(result_list[0])

  def test100Domains(self):
    name = self.UniqueName()
    domains = ['%d.example.com' % i for i in range(100)]

    def CheckCert(cert):
      self.assertEqual(name, cert.name)
      self.assertEqual(
          self.messages.SslCertificate.TypeValueValuesEnum.MANAGED,
          cert.type)

      self.assertEqual(domains, cert.managed.domains)
      self.assertIn(
          cert.managed.status,
          [self.managed.StatusValueValuesEnum.PROVISIONING,
           self.managed.StatusValueValuesEnum.PROVISIONING_FAILED])

    # test create
    result = self.Run('compute ssl-certificates create {0} --domains {1}'
                      .format(name, ','.join(domains)))
    result_list = list(result)

    self.ssl_cert_names.append(name)
    self.assertEqual(1, len(result_list))
    CheckCert(result_list[0])

    # test describe
    result = self.Run('compute ssl-certificates describe {0}'.format(name))
    CheckCert(result)

    # test list
    result = self.Run('compute ssl-certificates list')
    result_list = [self.DictToCert(cert)
                   for cert in result if cert['name'] == name]
    self.assertEqual(1, len(result_list))
    CheckCert(result_list[0])

  def test101DomainsShouldFail(self):
    name = self.UniqueName()
    domains = ['%d.example.com' % i for i in range(101)]
    with self.AssertRaisesExceptionRegexp(
        Exception,
        r'.*Value for field .* is too large: maximum size 100 element\(s\); '
        'actual size 101.'):
      self.Run('compute ssl-certificates create {0} --domains {1}'
               .format(name, ','.join(domains)))
    self.AssertErrContains('is too large')


if __name__ == '__main__':
  e2e_test_base.main()
