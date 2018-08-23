# -*- coding: utf-8 -*- #
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
"""Tests for the target-tcp-proxies list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class TargetTcpProxiesListTest(sdk_test_base.WithFakeAuth,
                               cli_test_base.CliTestBase):

  def SetUp(self):
    self.client = mock.Client(core_apis.GetClientClass('compute', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

  def _MakeTargetTcpProxy(self, name, description=None,
                          backend_service=None,
                          proxy_header=None):
    target_tcp_proxy = resources.REGISTRY.Parse(
        name,
        params={'project': self.Project()},
        collection='compute.targetTcpProxies')
    if backend_service is not None:
      backend_service = resources.REGISTRY.Parse(
          backend_service,
          params={'project': self.Project()},
          collection='compute.backendServices').SelfLink()
    if proxy_header is not None:
      proxy_header = (self.messages.TargetTcpProxy
                      .ProxyHeaderValueValuesEnum(proxy_header))
    return self.messages.TargetTcpProxy(
        name=name,
        description=description,
        proxyHeader=proxy_header,
        service=backend_service,
        selfLink=target_tcp_proxy.SelfLink(),
    )

  def _MakeSampleTargetProxies(self):
    return [
        self._MakeTargetTcpProxy(
            'target-tcp-proxy-1',
            proxy_header='PROXY_V1',
            backend_service='my-service'),
        self._MakeTargetTcpProxy(
            'target-tcp-proxy-2',
            proxy_header='NONE',
            backend_service='my-service'),
        self._MakeTargetTcpProxy(
            'target-tcp-proxy-3',
            backend_service='my-service')]

  def _MakeSampleTargetProxies2(self):
    return [
        self._MakeTargetTcpProxy(
            'target-tcp-proxy-2',
            proxy_header='NONE',
            backend_service='my-service')]

  def testSimpleCase(self):
    self.client.targetTcpProxies.List.Expect(
        self.messages.ComputeTargetTcpProxiesListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self.messages.TargetTcpProxyList(
            items=self._MakeSampleTargetProxies(),
        )
    )

    self.Run("""
        compute target-tcp-proxies list
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME               PROXY_HEADER SERVICE
        target-tcp-proxy-1 PROXY_V1     my-service
        target-tcp-proxy-2 NONE         my-service
        target-tcp-proxy-3              my-service
        """), normalize_space=True)
    self.AssertErrEquals('')

  def testWithFilter(self):
    self.client.targetTcpProxies.List.Expect(
        self.messages.ComputeTargetTcpProxiesListRequest(
            pageToken=None,
            filter='name eq ".*\\b\\*2\\b.*"',
            project=self.Project(),
        ),
        response=self.messages.TargetTcpProxyList(
            items=self._MakeSampleTargetProxies2(),
        )
    )

    self.Run("""
        compute target-tcp-proxies list --filter name:*2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME               PROXY_HEADER SERVICE
          target-tcp-proxy-2 NONE         my-service
          """), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
