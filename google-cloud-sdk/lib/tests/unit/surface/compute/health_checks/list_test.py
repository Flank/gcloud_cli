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
"""Tests for the health-checks list subcommand."""

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


class HealthChecksListTest(test_base.BaseTest,
                           completer_test_base.CompleterBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS))

  def testTableOutputNoProtocol(self):
    self.Run("""
        compute health-checks list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
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
            """), normalize_space=True)

  def testTableOutputHttp(self):
    self.Run("""
        compute health-checks list --protocol http
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
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
    self.Run("""
        compute health-checks list --protocol https
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL HOST            PORT REQUEST_PATH PROXY_HEADER
            health-check-https  HTTPS    www.example.com 443  /            PROXY_V1
            """),
        normalize_space=True)

  def testTableOutputTcp(self):
    self.Run("""
        compute health-checks list --protocol tcp
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL PORT REQUEST RESPONSE PROXY_HEADER
            health-check-tcp    TCP      80   req     ack      NONE
            """),
        normalize_space=True)

  def testTableOutputSsl(self):
    self.Run("""
        compute health-checks list --protocol ssl
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
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
    self.Run("""
        compute health-checks list health-check-https
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
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
    self.Run("""
        compute health-checks list health-check-https --protocol https
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
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
    self.Run("""
        compute health-checks list health-check-tcp --protocol https
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertErrContains('Listed 0 items.')
    self.AssertOutputEquals(
        textwrap.dedent("""\
            """), normalize_space=True)

  def testInvalidProtocol(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Invalid health check protocol totally-wacky.'):
      self.Run("""
          compute health-checks list --protocol totally-wacky
          """)
    self.CheckRequests()

  def testInvalidProtocolNamedInvalid(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Invalid health check protocol invalid.'):
      self.Run("""
          compute health-checks list --protocol invalid
          """)
    self.CheckRequests()

  def testHealthChecksCompleter(self):
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
            'health-check-http-1',
            'health-check-http-2',
            'health-check-https',
            'health-check-ssl',
            'health-check-tcp',
        ],
        cli=self.cli,
    )
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])


class HealthChecksListBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.HEALTH_CHECKS_BETA))

  def testTableOutputNoProtocol(self):
    self.Run("""
        compute health-checks list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL
            health-check-http2  HTTP2
            """),
        normalize_space=True)

  def testTableOutputHttp2(self):
    self.Run("""
        compute health-checks list --protocol http2
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL HOST            PORT REQUEST_PATH PROXY_HEADER
            health-check-http2  HTTP2    www.example.com 80   /            NONE
            """),
        normalize_space=True)

  def testTableOutputListByNameHTTP2(self):
    # List a specific health check by name.
    self.Run("""
        compute health-checks list health-check-http2
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.healthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                PROTOCOL
            health-check-http2  HTTP2
            """),
        normalize_space=True)


class HealthChecksListAlphaTest(test_base.BaseTest):

  URI_PREFIX = 'https://www.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self.SelectApi('alpha')
    self._compute_api = self.compute_alpha

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

  def testGlobalOption(self):
    command = 'alpha compute health-checks list --uri --global'
    output = ("""\
        https://www.googleapis.com/compute/alpha/projects/my-project/global/healthChecks/health-check-http-1
        https://www.googleapis.com/compute/alpha/projects/my-project/global/healthChecks/health-check-http-2
    """)

    self.RequestOnlyGlobal(command, self.health_checks, output)

  def testOneRegion(self):
    command = 'alpha compute health-checks list --uri --regions region-1'
    output = ("""\
        https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/healthChecks/health-check-tcp
        https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/healthChecks/health-check-ssl
        """)

    self.RequestOneRegion(command, self.region_health_checks, output)

  def testTwoRegions(self):
    command = ('alpha compute health-checks list --uri --regions '
               'region-1,region-2')
    output = ("""\
        https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/healthChecks/health-check-tcp
        https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/healthChecks/health-check-ssl
        """)

    self.RequestTwoRegions(command, self.region_health_checks, output)

  def testAggregateList(self):
    command = 'alpha compute health-checks list'
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
    command = 'alpha compute health-checks list --protocol http'
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


if __name__ == '__main__':
  test_case.main()
