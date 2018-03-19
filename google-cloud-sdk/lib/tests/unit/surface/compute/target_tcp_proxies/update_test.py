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
"""Tests for the target-tcp-proxies update subcommand."""

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetTCPProxiesUpdateTest(test_base.BaseTest):

  def testSimpleCase(self):
    messages = self.messages
    self.Run("""
        compute target-tcp-proxies update target-tcp-proxy-1
          --backend-service my-service
          --proxy-header PROXY_V1
        """)

    self.CheckRequests([
        (self.compute.targetTcpProxies,
         'SetBackendService',
         messages.ComputeTargetTcpProxiesSetBackendServiceRequest(
             project='my-project',
             targetTcpProxy='target-tcp-proxy-1',
             targetTcpProxiesSetBackendServiceRequest=(
                 messages.TargetTcpProxiesSetBackendServiceRequest(
                     service=(self.compute_uri + '/projects/my-project/'
                              'global/backendServices/my-service'))))),
        (self.compute.targetTcpProxies,
         'SetProxyHeader',
         messages.ComputeTargetTcpProxiesSetProxyHeaderRequest(
             project='my-project',
             targetTcpProxy='target-tcp-proxy-1',
             targetTcpProxiesSetProxyHeaderRequest=(
                 self.messages.TargetTcpProxiesSetProxyHeaderRequest(
                     proxyHeader=(
                         messages.TargetTcpProxiesSetProxyHeaderRequest.
                         ProxyHeaderValueValuesEnum.PROXY_V1)))))
    ])

  def testSimpleCaseBackendService(self):
    messages = self.messages
    self.Run("""
        compute target-tcp-proxies update target-tcp-proxy-1
          --backend-service my-service
        """)

    self.CheckRequests([
        (self.compute.targetTcpProxies,
         'SetBackendService',
         messages.ComputeTargetTcpProxiesSetBackendServiceRequest(
             project='my-project',
             targetTcpProxy='target-tcp-proxy-1',
             targetTcpProxiesSetBackendServiceRequest=(
                 messages.TargetTcpProxiesSetBackendServiceRequest(
                     service=(self.compute_uri + '/projects/my-project/'
                              'global/backendServices/my-service')))))
    ])

  def testUriSupportBackendService(self):
    messages = self.messages
    self.Run("""
        compute target-tcp-proxies update
          {uri}/projects/my-project/global/targetTcpProxies/target-tcp-proxy-1
          --backend-service
          {uri}/projects/my-project/global/backendServices/my-service
        """.format(uri=self.compute_uri))

    self.CheckRequests([
        (self.compute.targetTcpProxies,
         'SetBackendService',
         messages.ComputeTargetTcpProxiesSetBackendServiceRequest(
             project='my-project',
             targetTcpProxy='target-tcp-proxy-1',
             targetTcpProxiesSetBackendServiceRequest=(
                 messages.TargetTcpProxiesSetBackendServiceRequest(
                     service=(self.compute_uri + '/projects/my-project/'
                              'global/backendServices/my-service')))))
    ])

  def testSimpleCaseProxyHeaderV1(self):
    messages = self.messages

    self.Run("""
        compute target-tcp-proxies update target-tcp-proxy-1
          --proxy-header PROXY_V1
        """)

    self.CheckRequests([
        (self.compute.targetTcpProxies,
         'SetProxyHeader',
         messages.ComputeTargetTcpProxiesSetProxyHeaderRequest(
             project='my-project',
             targetTcpProxy='target-tcp-proxy-1',
             targetTcpProxiesSetProxyHeaderRequest=(
                 self.messages.TargetTcpProxiesSetProxyHeaderRequest(
                     proxyHeader=messages.TargetTcpProxiesSetProxyHeaderRequest.
                     ProxyHeaderValueValuesEnum.PROXY_V1))))
    ])

  def testSimpleCaseProxyHeaderNone(self):
    messages = self.messages

    self.Run("""
        compute target-tcp-proxies update target-tcp-proxy-1
          --proxy-header NONE
        """)

    self.CheckRequests([
        (self.compute.targetTcpProxies,
         'SetProxyHeader',
         messages.ComputeTargetTcpProxiesSetProxyHeaderRequest(
             project='my-project',
             targetTcpProxy='target-tcp-proxy-1',
             targetTcpProxiesSetProxyHeaderRequest=(
                 self.messages.TargetTcpProxiesSetProxyHeaderRequest(
                     proxyHeader=messages.TargetTcpProxiesSetProxyHeaderRequest.
                     ProxyHeaderValueValuesEnum.NONE))))
    ])

  def testUriSupportProxyHeader(self):
    messages = self.messages
    self.Run("""
        compute target-tcp-proxies update
          {uri}/projects/my-project/global/targetTcpProxies/target-tcp-proxy-1
          --proxy-header PROXY_V1
        """.format(uri=self.compute_uri))

    self.CheckRequests([
        (self.compute.targetTcpProxies,
         'SetProxyHeader',
         messages.ComputeTargetTcpProxiesSetProxyHeaderRequest(
             project='my-project',
             targetTcpProxy='target-tcp-proxy-1',
             targetTcpProxiesSetProxyHeaderRequest=(
                 self.messages.TargetTcpProxiesSetProxyHeaderRequest(
                     proxyHeader=messages.TargetTcpProxiesSetProxyHeaderRequest.
                     ProxyHeaderValueValuesEnum.PROXY_V1))))
    ])

  def testWithoutArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'You must specify at least one of '
        r'\[--backend-service\] or \[--proxy-header\].'):
      self.Run("""
          compute target-tcp-proxies update my-proxy
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
