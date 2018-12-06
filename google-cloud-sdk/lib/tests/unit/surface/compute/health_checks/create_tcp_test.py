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
"""Tests for the health-checks create tcp subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HealthChecksCreateTcpTest(test_base.BaseTest):

  def SetUp(self):
    self._api = 'v1'
    self._health_check_api = self.compute.healthChecks

  def RunCreate(self, command):
    self.Run('compute health-checks create tcp ' + command)

  def testDefaultOptions(self):
    self.RunCreate('my-health-check')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUriSupport(self):
    self.Run("""
        compute health-checks create tcp
          https://www.googleapis.com/compute/{0}/projects/my-project/global/healthChecks/my-health-check
          """.format(self._api))

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testRequestOptionUnicode(self):
    self.RunCreate('my-health-check --request Ṳᾔḯ¢◎ⅾℯ')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      request='Ṳᾔḯ¢◎ⅾℯ',
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testResponseOptionUnicode(self):
    self.RunCreate('my-health-check --response Ṳᾔḯ¢◎ⅾℯ')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      response='Ṳᾔḯ¢◎ⅾℯ',
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortOption(self):
    self.RunCreate('my-health-check --port 8888')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=8888,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortNameOption(self):
    self.RunCreate('my-health-check --port-name magic-port')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      portName='magic-port',
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testCheckIntervalOption(self):
    self.RunCreate('my-health-check --check-interval 34s')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testTimeoutSecOption(self):
    self.RunCreate('my-health-check --timeout 2m')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testHealthyThresholdOption(self):
    self.RunCreate('my-health-check --healthy-threshold 7')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUnhealthyThresholdOption(self):
    self.RunCreate('my-health-check --unhealthy-threshold 8')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project'))],)

  def testDescriptionOption(self):
    self.RunCreate("""
      my-health-check --description "Circulation, Airway, Breathing"
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  description='Circulation, Airway, Breathing',
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testProxyHeaderOption(self):
    self.RunCreate('my-health-check --proxy-header PROXY_V1')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.PROXY_V1)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)


class HealthChecksCreateTcpTestBetaTest(HealthChecksCreateTcpTest,
                                        parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self._health_check_api = self.compute_beta.healthChecks
    self._api = 'beta'

  def RunCreate(self, command):
    self.Run('compute health-checks create tcp ' + command)

  def testUseServingPortOption(self):
    self.RunCreate('my-health-check --use-serving-port')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      portSpecification=self.messages.TCPHealthCheck.
                      PortSpecificationValueValuesEnum.USE_SERVING_PORT,
                      proxyHeader=(self.messages.TCPHealthCheck.
                                   ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  @parameterized.parameters(('--port', 80), ('--port-name', 'my-port'))
  def testUseServingPortOptionErrors(self, flag, flag_value):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--use-serving-port]: {0} cannot '
        'be specified when using: --use-serving-port'.format(flag)):
      self.RunCreate('my-health-check --use-serving-port {0} {1}'.format(
          flag, flag_value))

  def testDefaultOptions(self):
    self.RunCreate('my-health-check')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUriSupport(self):
    self.Run("""
        compute health-checks create tcp
          https://www.googleapis.com/compute/{0}/projects/my-project/global/healthChecks/my-health-check
          """.format(self._api))

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testRequestOptionUnicode(self):
    self.RunCreate('my-health-check --request Ṳᾔḯ¢◎ⅾℯ')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      request='Ṳᾔḯ¢◎ⅾℯ',
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testResponseOptionUnicode(self):
    self.RunCreate('my-health-check --response Ṳᾔḯ¢◎ⅾℯ')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      response='Ṳᾔḯ¢◎ⅾℯ',
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortOption(self):
    self.RunCreate('my-health-check --port 8888')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=8888,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortNameOption(self):
    self.RunCreate('my-health-check --port-name magic-port')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      portName='magic-port',
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortAndPortNameOption(self):
    self.RunCreate('my-health-check --port 8888 --port-name magic-port')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=8888,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testCheckIntervalOption(self):
    self.RunCreate('my-health-check --check-interval 34s')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testTimeoutSecOption(self):
    self.RunCreate('my-health-check --timeout 2m')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testHealthyThresholdOption(self):
    self.RunCreate('my-health-check --healthy-threshold 7')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUnhealthyThresholdOption(self):
    self.RunCreate('my-health-check --unhealthy-threshold 8')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project'))],)

  def testDescriptionOption(self):
    self.RunCreate("""
      my-health-check --description "Circulation, Airway, Breathing"
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  description='Circulation, Airway, Breathing',
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testProxyHeaderOption(self):
    self.RunCreate('my-health-check --proxy-header PROXY_V1')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.PROXY_V1)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)


class HealthChecksCreateTcpTestAlphaTest(HealthChecksCreateTcpTestBetaTest,
                                         parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self._api = 'alpha'
    self._health_check_api = self.compute_alpha.healthChecks

  def RunCreate(self, command):
    self.Run('compute health-checks create tcp --global ' + command)


class RegionHealthChecksCreateTcpTest(test_base.BaseTest,
                                      parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self._api = 'alpha'
    self._health_check_api = self.compute_alpha.regionHealthChecks

  def RunCreate(self, command):
    self.Run('compute health-checks create tcp --region us-west-1 ' + command)

  def testDefaultOptions(self):
    self.RunCreate('my-health-check')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testUriSupport(self):
    self.Run("""
        compute health-checks create tcp
          https://www.googleapis.com/compute/{0}/projects/my-project/regions/us-west-1/healthChecks/my-health-check
        """.format(self._api))

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testRequestOptionUnicode(self):
    self.RunCreate('my-health-check --request Ṳᾔḯ¢◎ⅾℯ')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      request='Ṳᾔḯ¢◎ⅾℯ',
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testResponseOptionUnicode(self):
    self.RunCreate('my-health-check --response Ṳᾔḯ¢◎ⅾℯ')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      response='Ṳᾔḯ¢◎ⅾℯ',
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testPortOption(self):
    self.RunCreate('my-health-check --port 8888')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=8888,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testPortNameOption(self):
    self.RunCreate('my-health-check --port-name magic-port')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      portName='magic-port',
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testCheckIntervalOption(self):
    self.RunCreate('my-health-check --check-interval 34s')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testTimeoutSecOption(self):
    self.RunCreate('my-health-check --timeout 2m')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testHealthyThresholdOption(self):
    self.RunCreate('my-health-check --healthy-threshold 7')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testUnhealthyThresholdOption(self):
    self.RunCreate('my-health-check --unhealthy-threshold 8')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project',
              region='us-west-1'))],)

  def testDescriptionOption(self):
    self.RunCreate("""
      my-health-check --description "Circulation, Airway, Breathing"
    """)

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  description='Circulation, Airway, Breathing',
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testProxyHeaderOption(self):
    self.RunCreate('my-health-check --proxy-header PROXY_V1')

    self.CheckRequests(
        [(self._health_check_api, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                  tcpHealthCheck=self.messages.TCPHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.TCPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.TCPHealthCheck
                                   .ProxyHeaderValueValuesEnum.PROXY_V1)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)


if __name__ == '__main__':
  test_case.main()
