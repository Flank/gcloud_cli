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
"""Tests for the health-checks describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class HealthChecksDescribeTest(test_base.BaseTest,
                               completer_test_base.CompleterBase,
                               test_case.WithOutputCapture):

  def RunDescribe(self, command):
    self.Run('compute health-checks describe ' + command)

  def testSimpleCaseHttp(self):
    self.make_requests.side_effect = iter([
        [test_resources.HEALTH_CHECKS[0]],
    ])

    self.RunDescribe('my-health-check')

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

    self.RunDescribe('my-health-check')

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

  def testSimpleCaseTcp(self):
    self.make_requests.side_effect = iter([[test_resources.HEALTH_CHECKS[3]],])

    self.RunDescribe('my-health-check')

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

    self.RunDescribe('my-health-check')

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


class HealthChecksDescribeHttp2Test(test_base.BaseTest,
                                    completer_test_base.CompleterBase,
                                    test_case.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def testSimpleCaseHttp2(self):
    self.make_requests.side_effect = iter([
        [test_resources.HEALTH_CHECKS_BETA[0]],
    ])

    self.Run("""
        compute health-checks describe my-health-check
        """)

    health_check = self.compute_beta.healthChecks
    self.CheckRequests(
        [(health_check,
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
            selfLink: https://www.googleapis.com/compute/beta/projects/my-project/global/healthChecks/health-check-http2
            type: HTTP2
            """))


class RegionHealthChecksDescribeTest(test_base.BaseTest,
                                     completer_test_base.CompleterBase,
                                     test_case.WithOutputCapture):

  URI_PREFIX = 'https://www.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    self.health_checks = [
        self.messages.HealthCheck(
            name='health-check-http-1',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
            httpHealthCheck=self.messages.HTTPHealthCheck(
                host='www.example.com',
                port=8080,
                portName='happy-http-port',
                requestPath='/testpath',
                proxyHeader=(self.messages.HTTPHealthCheck.
                             ProxyHeaderValueValuesEnum.PROXY_V1)),
            selfLink=(
                self.URI_PREFIX + 'global/healthChecks/health-check-http-1')),
        self.messages.HealthCheck(
            name='health-check-http-2',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
            httpHealthCheck=self.messages.HTTPHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/',
                proxyHeader=self.messages.HTTPHealthCheck.
                ProxyHeaderValueValuesEnum.NONE),
            selfLink=(
                self.URI_PREFIX + 'global/healthChecks/health-check-http-2')),
    ]

    self.region_health_checks = [
        self.messages.HealthCheck(
            name='health-check-tcp',
            type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
            tcpHealthCheck=self.messages.TCPHealthCheck(
                port=80,
                portName='happy-tcp-port',
                request='req',
                response='ack',
                proxyHeader=self.messages.TCPHealthCheck.
                ProxyHeaderValueValuesEnum.NONE),
            selfLink=(self.URI_PREFIX +
                      'regions/region-1/healthChecks/health-check-tcp'),
            region='region-1'),
        self.messages.HealthCheck(
            name='health-check-ssl',
            type=self.messages.HealthCheck.TypeValueValuesEnum.SSL,
            sslHealthCheck=self.messages.SSLHealthCheck(
                port=443,
                portName='happy-ssl-port',
                request='req',
                response='ack',
                proxyHeader=(self.messages.SSLHealthCheck.
                             ProxyHeaderValueValuesEnum.PROXY_V1)),
            selfLink=(self.URI_PREFIX +
                      'regions/region-1/healthChecks/health-check-ssl'),
            region='region-1')
    ]

  def RunDescribe(self, command):
    self.Run('compute health-checks describe --region us-west-1 ' + command)

  def testSimpleCaseHttp(self):
    self.make_requests.side_effect = iter([
        [test_resources.HEALTH_CHECKS[0]],
    ])

    self.RunDescribe('my-health-check')

    self.CheckRequests([(self.compute.regionHealthChecks, 'Get',
                         self.messages.ComputeRegionHealthChecksGetRequest(
                             healthCheck='my-health-check',
                             project='my-project',
                             region='us-west-1'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
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

    self.RunDescribe('my-health-check')

    self.CheckRequests([(self.compute.regionHealthChecks, 'Get',
                         self.messages.ComputeRegionHealthChecksGetRequest(
                             healthCheck='my-health-check',
                             project='my-project',
                             region='us-west-1'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
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
        [test_resources.HEALTH_CHECKS_BETA[0]],
    ])

    self.RunDescribe('my-health-check')

    self.CheckRequests([(self.compute.regionHealthChecks, 'Get',
                         self.messages.ComputeRegionHealthChecksGetRequest(
                             healthCheck='my-health-check',
                             project='my-project',
                             region='us-west-1'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            http2HealthCheck:
              host: www.example.com
              port: 80
              portName: happy-http2-port
              proxyHeader: NONE
              requestPath: /
            name: health-check-http2
            selfLink: https://www.googleapis.com/compute/beta/projects/my-project/global/healthChecks/health-check-http2
            type: HTTP2
            """))

  def testSimpleCaseTcp(self):
    self.make_requests.side_effect = iter([
        [test_resources.HEALTH_CHECKS[3]],
    ])

    self.RunDescribe('my-health-check')

    self.CheckRequests([(self.compute.regionHealthChecks, 'Get',
                         self.messages.ComputeRegionHealthChecksGetRequest(
                             healthCheck='my-health-check',
                             project='my-project',
                             region='us-west-1'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
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
    self.make_requests.side_effect = iter([
        [test_resources.HEALTH_CHECKS[4]],
    ])

    self.RunDescribe('my-health-check')

    self.CheckRequests([(self.compute.regionHealthChecks, 'Get',
                         self.messages.ComputeRegionHealthChecksGetRequest(
                             healthCheck='my-health-check',
                             project='my-project',
                             region='us-west-1'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
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
    self.RunCompletion('compute health-checks describe h', [
        'health-check-https',
        'health-check-http-1',
        'health-check-http-2',
        'health-check-tcp',
        'health-check-ssl',
    ])

  def testHealthChecksCompleterRegional(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self.health_checks),
        resource_projector.MakeSerializable(self.region_health_checks)
    ]
    self.RunCompleter(
        completers.HealthChecksCompleterAlpha,
        expected_command=[
            [
                'alpha',
                'compute',
                'health-checks',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'alpha',
                'compute',
                'health-checks',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            'health-check-http-1',
            'health-check-http-2',
            'health-check-tcp',
            'health-check-ssl',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
