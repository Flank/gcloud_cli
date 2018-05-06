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
"""Tests for the target-tcp-proxies create subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetTCPProxiesCreateTest(test_base.BaseTest):

  def testSimpleCaseProxyV1Header(self):
    messages = self.messages
    proxy_header_enum = messages.TargetTcpProxy.ProxyHeaderValueValuesEnum

    self.make_requests.side_effect = iter([
        [messages.TargetTcpProxy(
            name='my-proxy',
            description='My target TCP proxy',
        )],
    ])

    result = list(
        self.Run("""
        compute target-tcp-proxies create my-proxy
          --description "My target TCP proxy"
          --backend-service my-service
          --proxy-header PROXY_V1
          --format=disable
        """))

    self.assertEqual(result[0].name, 'my-proxy')
    self.AssertOutputEquals('')
    self.CheckRequests(
        [(self.compute.targetTcpProxies,
          'Insert',
          messages.ComputeTargetTcpProxiesInsertRequest(
              project='my-project',
              targetTcpProxy=messages.TargetTcpProxy(
                  description='My target TCP proxy',
                  name='my-proxy',
                  proxyHeader=proxy_header_enum.PROXY_V1,
                  service=(self.compute_uri + '/projects/my-project/global/'
                           'backendServices/my-service'))))],
    )

  def testSimpleCaseNoneHeader(self):
    messages = self.messages
    proxy_header_enum = messages.TargetTcpProxy.ProxyHeaderValueValuesEnum

    self.make_requests.side_effect = iter([
        [messages.TargetTcpProxy(
            name='my-proxy',
            description='My target TCP proxy',
        )],
    ])

    result = list(self.Run("""
        compute target-tcp-proxies create my-proxy
          --description "My target TCP proxy"
          --backend-service my-service
          --proxy-header NONE
          --format=disable
        """))

    self.assertEqual(result[0].name, 'my-proxy')

    self.CheckRequests(
        [(self.compute.targetTcpProxies,
          'Insert',
          messages.ComputeTargetTcpProxiesInsertRequest(
              project='my-project',
              targetTcpProxy=messages.TargetTcpProxy(
                  description='My target TCP proxy',
                  name='my-proxy',
                  proxyHeader=proxy_header_enum.NONE,
                  service=(self.compute_uri + '/projects/my-project/global/'
                           'backendServices/my-service'))))],
    )

  def testUriSupport(self):
    messages = self.messages
    proxy_header_enum = messages.TargetTcpProxy.ProxyHeaderValueValuesEnum

    self.make_requests.side_effect = iter([
        [messages.TargetTcpProxy(
            name='my-proxy',
            description='My target TCP proxy',
        )],
    ])

    result = list(self.Run("""
        compute target-tcp-proxies create
          {uri}/projects/my-project/global/targetTcpProxies/my-proxy
          --backend-service {uri}/projects/my-project/global/backendServices/my-service
          --format=disable
        """.format(uri=self.compute_uri)))

    self.assertEqual(result[0].name, 'my-proxy')

    self.CheckRequests(
        [(self.compute.targetTcpProxies,
          'Insert',
          messages.ComputeTargetTcpProxiesInsertRequest(
              project='my-project',
              targetTcpProxy=messages.TargetTcpProxy(
                  name='my-proxy',
                  proxyHeader=proxy_header_enum.NONE,
                  service=(self.compute_uri + '/projects/my-project/global/'
                           'backendServices/my-service'))))],
    )

  def testWithoutBackendService(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --backend-service: Must be specified.'):
      self.Run("""
          compute target-tcp-proxies create my-proxy
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
