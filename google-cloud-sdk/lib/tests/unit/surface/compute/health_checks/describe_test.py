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
"""Tests for the health-checks describe subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class HealthChecksDescribeTest(test_base.BaseTest,
                               completer_test_base.CompleterBase,
                               test_case.WithOutputCapture):

  def testSimpleCaseHttp(self):
    self.make_requests.side_effect = iter([
        [test_resources.HEALTH_CHECKS[0]],
    ])

    self.Run("""
        compute health-checks describe my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
    )
    self.assertMultiLineEqual(self.GetOutput(), textwrap.dedent("""\
            httpHealthCheck:
              host: www.example.com
              port: 8080
              portName: happy-http-port
              proxyHeader: PROXY_V1
              requestPath: /testpath
            name: health-check-http-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/healthChecks/health-check-http-1
            type: HTTP
            """))

  def testSimpleCaseHttps(self):
    self.make_requests.side_effect = iter([
        [test_resources.HEALTH_CHECKS[2]],
    ])

    self.Run("""
        compute health-checks describe my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
    )
    self.assertMultiLineEqual(self.GetOutput(), textwrap.dedent("""\
            httpsHealthCheck:
              host: www.example.com
              port: 443
              portName: happy-https-port
              proxyHeader: PROXY_V1
              requestPath: /
            name: health-check-https
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/healthChecks/health-check-https
            type: HTTPS
            """))

  def testSimpleCaseHttp2(self):
    self.make_requests.side_effect = iter([
        [test_resources.HEALTH_CHECKS_ALPHA[0]],
    ])

    self.Run("""
        compute health-checks describe my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
    )
    self.assertMultiLineEqual(self.GetOutput(), textwrap.dedent("""\
            http2HealthCheck:
              host: www.example.com
              port: 80
              portName: happy-http2-port
              proxyHeader: NONE
              requestPath: /
            name: health-check-http2
            selfLink: https://www.googleapis.com/compute/alpha/projects/my-project/global/healthChecks/health-check-http2
            type: HTTP2
            """))

  def testSimpleCaseTcp(self):
    self.make_requests.side_effect = iter([[test_resources.HEALTH_CHECKS[3]],])

    self.Run("""
        compute health-checks describe my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
    )
    self.assertMultiLineEqual(self.GetOutput(), textwrap.dedent("""\
            name: health-check-tcp
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/healthChecks/health-check-tcp
            tcpHealthCheck:
              port: 80
              portName: happy-tcp-port
              proxyHeader: NONE
              request: req
              response: ack
            type: TCP
            """))

  def testSimpleCaseSsl(self):
    self.make_requests.side_effect = iter([[test_resources.HEALTH_CHECKS[4]],])

    self.Run("""
        compute health-checks describe my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
    )
    self.assertMultiLineEqual(self.GetOutput(), textwrap.dedent("""\
            name: health-check-ssl
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/healthChecks/health-check-ssl
            sslHealthCheck:
              port: 443
              portName: happy-ssl-port
              proxyHeader: PROXY_V1
              request: req
              response: ack
            type: SSL
            """))

  def testDescribeCompletion(self):
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        return_value=resource_projector.MakeSerializable(
            test_resources.HEALTH_CHECKS),
        autospec=True)
    self.RunCompletion(
        'compute health-checks describe h',
        [
            'health-check-https',
            'health-check-http-1',
            'health-check-http-2',
            'health-check-tcp',
            'health-check-ssl',
        ])


if __name__ == '__main__':
  test_case.main()
