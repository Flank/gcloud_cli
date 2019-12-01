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
"""Tests for the health-checks create http subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HealthChecksCreateHttpTest(test_base.BaseTest, parameterized.TestCase):

  def RunCreate(self, command):
    self.Run('compute health-checks create http ' + command)

  def testDefaultOptions(self):
    self.RunCreate('my-health-check')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUriSupport(self):
    self.RunCreate("""
          https://compute.googleapis.com/compute/v1/projects/my-project/global/healthChecks/my-health-check
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testHostOption(self):
    self.RunCreate('my-health-check --host www.example.com')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortOption(self):
    self.RunCreate('my-health-check --port 8888')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=8888,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortNameOption(self):
    self.RunCreate('my-health-check --port-name magic-port')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      portName='magic-port',
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testPortAndPortNameOption(self):
    self.RunCreate('my-health-check --port 8888 --port-name magic-port')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=8888,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testRequestPathOption(self):
    self.RunCreate('my-health-check --request-path /testpath')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/testpath',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testCheckIntervalOption(self):
    self.RunCreate('my-health-check --check-interval 34s')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testTimeoutSecOption(self):
    self.RunCreate('my-health-check --timeout 2m')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testHealthyThresholdOption(self):
    self.RunCreate('my-health-check --healthy-threshold 7')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUnhealthyThresholdOption(self):
    self.RunCreate('my-health-check --unhealthy-threshold 8')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  description='Circulation, Airway, Breathing',
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testProxyHeaderOption(self):
    self.RunCreate('my-health-check --proxy-header PROXY_V1')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.PROXY_V1)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testResponseOption(self):
    self.RunCreate('my-health-check --response new-response')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      response='new-response',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUseServingPortOption(self):
    self.RunCreate("""
        my-health-check --use-serving-port
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      portSpecification=self.messages.HTTPHealthCheck
                      .PortSpecificationValueValuesEnum.USE_SERVING_PORT,
                      requestPath='/',
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
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


class HealthChecksCreateHttpBetaTest(HealthChecksCreateHttpTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def RunCreate(self, command):
    self.Run('compute health-checks create http --global ' + command)


class HealthChecksCreateHttpAlphaTest(HealthChecksCreateHttpBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  @parameterized.named_parameters(
      ('DisableLogging', '--no-enable-logging', False),
      ('EnableLogging', '--enable-logging', True))
  def testLogConfig(self, enable_logs_flag, enable_logs):

    self.RunCreate("""my-health-check {0}""".format(enable_logs_flag))

    expected_log_config = self.messages.HealthCheckLogConfig(enable=enable_logs)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2,
                  logConfig=expected_log_config),
              project='my-project'))],)


class RegionHealthChecksCreateHttpBetaTest(test_base.BaseTest,
                                           parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def RunCreate(self, command):
    self.Run('compute health-checks create http --region us-west-1 ' + command)

  def testGlobalHealthCheckCreate(self):
    self.Run("""
        compute health-checks create http my-health-check --global
    """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testDefaultOptions(self):
    self.RunCreate('my-health-check')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testUriSupport(self):
    self.RunCreate("""
          https://compute.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/healthChecks/my-health-check
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testHostOption(self):
    self.RunCreate('my-health-check --host www.example.com')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=8888,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      portName='magic-port',
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.NONE)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testRequestPathOption(self):
    self.RunCreate('my-health-check --request-path /testpath')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/testpath',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  description='Circulation, Airway, Breathing',
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
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
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
                  httpHealthCheck=self.messages.HTTPHealthCheck(
                      port=80,
                      requestPath='/',
                      portSpecification=(
                          self.messages.HTTPHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      proxyHeader=(self.messages.HTTPHealthCheck
                                   .ProxyHeaderValueValuesEnum.PROXY_V1)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)


class RegionHealthChecksCreateHttpAlphaTest(RegionHealthChecksCreateHttpBetaTest
                                           ):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)


if __name__ == '__main__':
  test_case.main()
