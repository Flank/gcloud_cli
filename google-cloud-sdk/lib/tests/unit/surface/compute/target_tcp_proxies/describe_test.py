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
"""Tests for the url-maps describe subcommand."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class TargetTcpProxiesDescribeTest(test_base.BaseTest,
                                   test_case.WithOutputCapture):

  def testSimpleCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_TCP_PROXIES_V1[0]],
    ])

    self.Run("""
        compute target-tcp-proxies describe target-tcp-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.targetTcpProxies,
          'Get',
          messages.ComputeTargetTcpProxiesGetRequest(
              project='my-project',
              targetTcpProxy='target-tcp-proxy-1'))]
    )

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: My first proxy
            name: target-tcp-proxy-1
            proxyHeader: PROXY_V1
            service: {uri}/projects/my-project/global/backendServices/my-service
            """.format(uri=self.compute_uri)))


if __name__ == '__main__':
  test_case.main()
