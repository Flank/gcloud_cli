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
"""Integration tests for self managed ssl certificates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import subprocess
import time

from googlecloudsdk.command_lib.util import time_util
from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import ssl_certificates_base


class SelfManagedSslCertificateTest(
    ssl_certificates_base.SslCertificatesTestBase):

  def SetUp(self):
    temp_dir = self.CreateTempDir()
    self.key_fname = os.path.join(temp_dir, 'foo.key')
    self.crt_fname = os.path.join(temp_dir, 'foo.crt')

    self.start_time = time.time()
    self.assertEqual(
        subprocess.call(
            ['openssl', 'req', '-x509', '-nodes', '-days', '365',
             '-newkey', 'rsa:2048', '-batch',
             '-subj', '/CN=example.com',
             '-keyout', self.key_fname,
             '-out', self.crt_fname]),
        0)

  def testCreation(self):
    name = self.UniqueName()
    description = 'CertDescription'

    def CheckCert(cert, after):
      self.assertEqual(name, cert.name)
      self.assertEqual(
          self.messages.SslCertificate.TypeValueValuesEnum.SELF_MANAGED,
          cert.type)
      self.assertEqual(description, cert.description)

      creation_timestamp = time_util.Strptime(cert.creationTimestamp)
      # Metastore, TrueTime and server time can be different on different
      # machines and you should compare timestamp with some accuracy.
      time_accuracy = 60
      self.assertLessEqual(self.start_time - time_accuracy, creation_timestamp)
      self.assertGreaterEqual(after + time_accuracy, creation_timestamp)

      expire_time = time_util.Strptime(cert.expireTime)
      self.assertLessEqual(self.start_time + 364*24*3600, expire_time)
      self.assertGreaterEqual(after + 366*24*3600, expire_time)

    # test create
    result = self.Run('compute ssl-certificates create {0} --certificate {1} '
                      '--private-key {2} --description {3}'.format(
                          name, self.crt_fname, self.key_fname, description))
    result_list = list(result)

    self.ssl_cert_names.append(name)
    self.assertEqual(1, len(result_list))
    after = time.time()
    CheckCert(result_list[0], after)

    # test describe
    result = self.Run('compute ssl-certificates describe {0}'.format(name))
    CheckCert(result, after)

    # test list
    result = self.Run('compute ssl-certificates list')
    result_list = [self.DictToCert(cert)
                   for cert in result if cert['name'] == name]
    self.assertEqual(1, len(result_list))
    CheckCert(result_list[0], after)

  def testDescriptionOnlyShouldFail(self):
    name = self.UniqueName()
    description = 'CertDescription'
    with self.AssertRaisesExceptionRegexp(
        Exception,
        r'Exactly one of .* must be specified.'):
      self.Run('compute ssl-certificates create {0} --description {1}'
               .format(name, description))
    self.AssertErrContains('--domains | --certificate --private-key')


if __name__ == '__main__':
  e2e_test_base.main()
