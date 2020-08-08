# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the health-checks list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.health_checks import test_resources

import mock


class HealthChecksListTest(test_base.BaseTest,
                           completer_test_base.CompleterBase):

  def SetUp(self):
    self._api = ''
    self.SelectApi('v1')
    self._compute_api = self.compute_v1
    self._uri_prefix = 'https://compute.googleapis.com/compute/v1/projects/my-project/'

    self._Setup()

    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]

  def _Setup(self):
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
                proxyHeader=(self.messages.HTTPHealthCheck
                             .ProxyHeaderValueValuesEnum.PROXY_V1)),
            selfLink=(self._uri_prefix +
                      'global/healthChecks/health-check-http-1')),
        self.messages.HealthCheck(
            name='health-check-http-2',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
            httpHealthCheck=self.messages.HTTPHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/',
                proxyHeader=self.messages.HTTPHealthCheck
                .ProxyHeaderValueValuesEnum.NONE),
            selfLink=(self._uri_prefix +
                      'global/healthChecks/health-check-http-2')),
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
                proxyHeader=self.messages.TCPHealthCheck
                .ProxyHeaderValueValuesEnum.NONE),
            selfLink=(self._uri_prefix +
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
                proxyHeader=(self.messages.SSLHealthCheck
                             .ProxyHeaderValueValuesEnum.PROXY_V1)),
            selfLink=(self._uri_prefix +
                      'regions/region-1/healthChecks/health-check-ssl'),
            region='region-1')
    ]

  def testTableOutputNoProtocol(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list --global
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL
            health-check-http-1 HTTP
            health-check-http-2 HTTP
            health-check-https  HTTPS
            health-check-tcp    TCP
            health-check-ssl    SSL
            health-check-http2  HTTP2
            health-check-grpc   GRPC
            """),
        normalize_space=True)

  def testTableOutputGrpc(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list health-check-grpc --global --protocol grpc
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                 PROTOCOL PORT    GRPC_SERVICE_NAME
            health-check-grpc    GRPC     88      gRPC-service
            """),
        normalize_space=True)

  def testTableOutputHttp(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list --global --protocol http
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL HOST            PORT REQUEST_PATH PROXY_HEADER
            health-check-http-1 HTTP     www.example.com 8080 /testpath    PROXY_V1
            health-check-http-2 HTTP     www.example.com 80   /            NONE
            """),
        normalize_space=True)

  def testTableOutputHttps(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list --global --protocol https
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL HOST            PORT REQUEST_PATH PROXY_HEADER
            health-check-https  HTTPS    www.example.com 443  /            PROXY_V1
            """),
        normalize_space=True)

  def testTableOutputHttp2(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list --global --protocol http2
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL HOST            PORT REQUEST_PATH PROXY_HEADER
            health-check-http2  HTTP2    www.example.com 443  /            PROXY_V1
            """),
        normalize_space=True)

  def testTableOutputTcp(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list --global --protocol tcp
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL PORT REQUEST RESPONSE PROXY_HEADER
            health-check-tcp    TCP      80   req     ack      NONE
            """),
        normalize_space=True)

  def testTableOutputSsl(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list --global --protocol ssl
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL PORT REQUEST RESPONSE PROXY_HEADER
            health-check-ssl    SSL      443  req     ack      PROXY_V1
            """),
        normalize_space=True)

  def testTableOutputListByName(self):
    # List a specific health check by name.
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list --global health-check-https
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL
            health-check-https  HTTPS
            """), normalize_space=True)

  def testTableOutputListByNameAndSpecifyProtocol(self):
    # List a specific health check by name and specify protocol to get
    # protocol-specific fields.
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list health-check-https --global --protocol https
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL HOST            PORT REQUEST_PATH PROXY_HEADER
            health-check-https  HTTPS    www.example.com 443  /            PROXY_V1
            """), normalize_space=True)

  def testTableOutputListByNameAndSpecifyNonMatchingProtocol(self):
    # List a specific health check by name but specify a protocol that
    # is not the protocol of the named health check.
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.Run(self._api + """
        compute health-checks list health-check-tcp --global --protocol https
        """)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertErrContains('Listed 0 items.')
    self.AssertOutputEquals(
        textwrap.dedent("""\
            """), normalize_space=True)

  def testInvalidProtocol(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    with self.AssertRaisesToolExceptionRegexp(
        'Invalid health check protocol totally-wacky.'):
      self.Run(self._api + """
          compute health-checks list --global --protocol totally-wacky
          """)
    self.CheckRequests()

  def testInvalidProtocolNamedInvalid(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    with self.AssertRaisesToolExceptionRegexp(
        'Invalid health check protocol invalid.'):
      self.Run(self._api + """
          compute health-checks list --global --protocol invalid
          """)
    self.CheckRequests()

  def testHealthChecksCompleter(self):
    # Completer always uses v1 API.
    self._api = ''
    self.SelectApi('v1')
    self._compute_api = self.compute
    self._uri_prefix = 'https://compute.googleapis.com/compute/v1/projects/my-project/'
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS)
    ]
    self.RunCompleter(
        completers.HealthChecksCompleter,
        expected_command=[
            'compute',
            'health-checks',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'health-check-grpc',
            'health-check-http-1',
            'health-check-http-2',
            'health-check-https',
            'health-check-ssl',
            'health-check-tcp',
            'health-check-http2',
        ],
        cli=self.cli,
    )
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'AggregatedList',
                   self.messages.ComputeHealthChecksAggregatedListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def testGlobalOption(self):
    command = self._api + ' compute health-checks list --uri --global'
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/global/healthChecks/health-check-http-1
        https://compute.googleapis.com/compute/{0}/projects/my-project/global/healthChecks/health-check-http-2
    """.format(self.api))

    self.RequestOnlyGlobal(command, self.health_checks, output)

  def testOneRegion(self):
    command = self._api + ' compute health-checks list --uri --regions region-1'
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/healthChecks/health-check-tcp
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/healthChecks/health-check-ssl
        """.format(self.api))

    self.RequestOneRegion(command, self.region_health_checks, output)

  def testTwoRegions(self):
    command = (
        self._api + ' compute health-checks list --uri --regions '
        'region-1,region-2')
    output = ("""\
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/healthChecks/health-check-tcp
        https://compute.googleapis.com/compute/{0}/projects/my-project/regions/region-1/healthChecks/health-check-ssl
        """.format(self.api))

    self.RequestTwoRegions(command, self.region_health_checks, output)

  def testAggregateList(self):
    command = self._api + ' compute health-checks list'
    return_value = self.health_checks + self.region_health_checks
    output = ("""\
        NAME PROTOCOL
        health-check-http-1 HTTP
        health-check-http-2 HTTP
        health-check-tcp TCP
        health-check-ssl SSL
    """)

    self.RequestAggregate(command, return_value, output)

  def testAggregateListWithProtocol(self):
    command = self._api + ' compute health-checks list --protocol http'
    return_value = self.health_checks + self.region_health_checks
    output = ("""\
        NAME PROTOCOL HOST PORT REQUEST_PATH PROXY_HEADER
        health-check-http-1 HTTP www.example.com 8080 /testpath PROXY_V1
        health-check-http-2 HTTP www.example.com 80 / NONE
    """)

    self.RequestAggregate(command, return_value, output)

  def RequestOnlyGlobal(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'List',
                   self.messages.ComputeHealthChecksListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestAggregate(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)

    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.healthChecks, 'AggregatedList',
                   self.messages.ComputeHealthChecksAggregatedListRequest(
                       project='my-project', maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestOneRegion(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.regionHealthChecks, 'List',
                   self.messages.ComputeRegionHealthChecksListRequest(
                       project='my-project', region='region-1',
                       maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestTwoRegions(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self._compute_api.regionHealthChecks, 'List',
                   self.messages.ComputeRegionHealthChecksListRequest(
                       project='my-project', region='region-1',
                       maxResults=500)),
                  (self._compute_api.regionHealthChecks, 'List',
                   self.messages.ComputeRegionHealthChecksListRequest(
                       project='my-project', region='region-2',
                       maxResults=500))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)


class HealthChecksListBetaTest(HealthChecksListTest):

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi('beta')
    self._compute_api = self.compute_beta
    self._uri_prefix = 'https://compute.googleapis.com/compute/beta/projects/my-project/'

    self._Setup()


class HealthChecksListAlphaTest(HealthChecksListBetaTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi('alpha')
    self._compute_api = self.compute_alpha
    self._uri_prefix = 'https://compute.googleapis.com/compute/alpha/projects/my-project/'

    self._Setup()


if __name__ == '__main__':
  test_case.main()
