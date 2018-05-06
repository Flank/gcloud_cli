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
"""Integration tests for target tcp proxies."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class TcpProxyTest(e2e_test_base.BaseTest):

  def UniqueName(self, name):
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='compute-tcp-proxy-test-' + name))

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(False)
    self.backend_service_names = []
    self.health_check_names = []
    self.target_tcp_proxy_names = []
    self.forwarding_rule_names = []

  def CreateHealthCheck(self):
    name = self.UniqueName('tcp-hc')
    result = self.Run('compute health-checks create tcp {0}'.format(name))
    result_list = list(result)
    self.assertEqual(1, len(result_list))
    self.assertEqual(name, result_list[0].name)
    self.health_check_names.append(name)
    return name

  def CreateTcpBackendService(self, health_check_name):
    name = self.UniqueName('tcp-bs')
    result = self.Run('compute backend-services create {0} '
                      '--global '
                      '--protocol TCP '
                      '--health-checks {1}'.format(name, health_check_name))
    self.assertEqual(1, len(result))
    self.assertEqual(name, result[0].name)
    self.backend_service_names.append(name)
    return name

  def testTcpProxy(self):
    hc_name = self.CreateHealthCheck()
    bs_name = self.CreateTcpBackendService(hc_name)

    # Create target tcp proxy.
    target_name = self.UniqueName('tcp-proxy')
    result = self.Run('compute target-tcp-proxies create {0} '
                      '--backend-service {1}'.format(target_name, bs_name))
    result_list = list(result)
    self.assertEqual(1, len(result_list))
    self.assertEqual(target_name, result_list[0].name)
    self.target_tcp_proxy_names.append(target_name)

    # Create forwarding rule for the target tcp proxy.
    fr_name = self.UniqueName('forwarding-rule')
    result = self.Run('compute forwarding-rules create {0} --global '
                      '--target-tcp-proxy {1} --ports 443 '.format(
                          fr_name, target_name))
    self.assertEqual(1, len(result))
    self.assertEqual(fr_name, result[0].name)
    self.forwarding_rule_names.append(fr_name)

    # Update the target tcp proxy.
    bs2_name = self.CreateTcpBackendService(hc_name)
    self.Run('compute target-tcp-proxies update {0} '
             '--backend-service {1}'.format(target_name, bs2_name))
    result = self.Run('compute target-tcp-proxies describe {0}'.format(
        target_name))
    self.assertTrue(result.service.endswith(bs2_name))

    result = self.Run('compute target-tcp-proxies update {0} '
                      '--proxy-header PROXY_V1'.format(target_name))
    result = self.Run('compute target-tcp-proxies describe {0}'.format(
        target_name))
    self.assertEqual('PROXY_V1', str(result.proxyHeader))

  def TearDown(self):
    for name in self.forwarding_rule_names:
      self.CleanUpResource(name,
                           'forwarding-rules',
                           scope=e2e_test_base.EXPLICIT_GLOBAL)
    for name in self.target_tcp_proxy_names:
      self.CleanUpResource(name,
                           'target-tcp-proxies',
                           scope=e2e_test_base.GLOBAL)
    for name in self.backend_service_names:
      self.CleanUpResource(name, 'backend-services',
                           scope=e2e_test_base.EXPLICIT_GLOBAL)
    for name in self.health_check_names:
      self.CleanUpResource(name, 'health-checks', scope=e2e_test_base.GLOBAL)


if __name__ == '__main__':
  e2e_test_base.main()
