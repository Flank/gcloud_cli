# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for target ssl proxies."""

import os
import subprocess

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


SSL_CONFIG_FILE_CONTENTS = """
#
# SSLeay example configuration file.
#

[ req ]
distinguished_name      = req_distinguished_name
prompt                  = no

[ req_distinguished_name ]
commonName                      = @HostName@

[ v3_req ]
basicConstraints        = CA:FALSE
"""


class SslProxyTest(e2e_test_base.BaseTest):

  def UniqueName(self, name):
    return e2e_utils.GetResourceNameGenerator(
        prefix='compute-ssl-proxy-test-' + name).next()

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(False)
    self.backend_service_names = []
    self.health_check_names = []
    self.ssl_cert_names = []
    self.target_ssl_proxy_names = []
    self.forwarding_rule_names = []
    self.ssl_config_fname = os.path.join(self.CreateTempDir(), 'ssl.cnf')
    self.key_fname = os.path.join(self.CreateTempDir(), 'foo.key')
    self.crt_fname = os.path.join(self.CreateTempDir(), 'foo.crt')

    ssl_config_file = open(self.ssl_config_fname, 'w')
    ssl_config_file.write(SSL_CONFIG_FILE_CONTENTS)
    ssl_config_file.close()

    self.assertEqual(
        subprocess.call(
            ['openssl', 'req', '-x509', '-nodes', '-days', '365',
             '-newkey', 'rsa:2048', '-batch',
             '-subj', '/C=US/CN=Alon',
             '-keyout', self.key_fname,
             '-out', self.crt_fname,
             '-rand', '/dev/zero',  # sounds pretty random
             '-config', self.ssl_config_fname]),
        0)

  def CreateHealthCheck(self):
    name = self.UniqueName('tcp-hc')
    result = self.Run('compute health-checks create tcp {0}'.format(name))
    result_list = list(result)
    self.assertEquals(1, len(result_list))
    self.assertEquals(name, result_list[0].name)
    self.health_check_names.append(name)
    return name

  def CreateTcpBackendService(self, health_check_name):
    name = self.UniqueName('tcp-bs')
    result = self.Run('compute backend-services create {0} '
                      '--global '
                      '--protocol TCP '
                      '--health-checks {1}'.format(name, health_check_name))
    self.assertEquals(1, len(result))
    self.assertEquals(name, result[0].name)
    self.backend_service_names.append(name)
    return name

  def CreateSslCertificate(self):
    name = self.UniqueName('ssl-cert')
    result = self.Run('compute ssl-certificates create {0} '
                      '--certificate {1} --private-key {2}'.format(
                          name, self.crt_fname, self.key_fname))
    result_list = list(result)
    self.assertEquals(1, len(result_list))
    self.assertEquals(name, result_list[0].name)
    self.ssl_cert_names.append(name)
    return name

  def testSslProxy(self):
    hc_name = self.CreateHealthCheck()
    bs_name = self.CreateTcpBackendService(hc_name)
    cert_name = self.CreateSslCertificate()

    # Create target ssl proxy.
    target_name = self.UniqueName('ssl-proxy')
    result = self.Run('compute target-ssl-proxies create {0} '
                      '--backend-service {1} '
                      '--ssl-certificates {2}'.format(target_name, bs_name,
                                                      cert_name))
    result_list = list(result)
    self.assertEquals(1, len(result_list))
    self.assertEquals(target_name, result_list[0].name)
    self.target_ssl_proxy_names.append(target_name)

    # Create forwarding rule for the target ssl proxy.
    fr_name = self.UniqueName('forwarding-rule')
    result = self.Run('compute forwarding-rules create {0} --global '
                      '--target-ssl-proxy {1} --ports 443 '.format(fr_name,
                                                                   target_name))
    self.assertEquals(1, len(result))
    self.assertEquals(fr_name, result[0].name)
    self.forwarding_rule_names.append(fr_name)

    # Update the target ssl proxy.
    bs2_name = self.CreateTcpBackendService(hc_name)
    self.Run('compute target-ssl-proxies update {0} '
             '--backend-service {1}'.format(target_name, bs2_name))
    result = self.Run('compute target-ssl-proxies describe {0}'.format(
        target_name))
    self.assertTrue(result.service.endswith(bs2_name))

    cert2_name = self.CreateSslCertificate()
    result = self.Run('compute target-ssl-proxies update {0} '
                      '--ssl-certificates {1}'.format(target_name, cert2_name))
    result = self.Run('compute target-ssl-proxies describe {0}'.format(
        target_name))
    self.assertTrue(result.sslCertificates[0].endswith(cert2_name))

    result = self.Run('compute target-ssl-proxies update {0} '
                      '--proxy-header PROXY_V1'.format(target_name))
    result = self.Run('compute target-ssl-proxies describe {0}'.format(
        target_name))
    self.assertEquals('PROXY_V1', str(result.proxyHeader))

  def TearDown(self):
    for name in self.forwarding_rule_names:
      self.CleanUpResource(name,
                           'forwarding-rules',
                           scope=e2e_test_base.EXPLICIT_GLOBAL)
    for name in self.target_ssl_proxy_names:
      self.CleanUpResource(name,
                           'target-ssl-proxies',
                           scope=e2e_test_base.GLOBAL)
    for name in self.backend_service_names:
      self.CleanUpResource(name, 'backend-services',
                           scope=e2e_test_base.EXPLICIT_GLOBAL)
    for name in self.health_check_names:
      self.CleanUpResource(name, 'health-checks', scope=e2e_test_base.GLOBAL)
    for name in self.ssl_cert_names:
      self.CleanUpResource(name, 'ssl-certificates', scope=e2e_test_base.GLOBAL)


if __name__ == '__main__':
  e2e_test_base.main()
