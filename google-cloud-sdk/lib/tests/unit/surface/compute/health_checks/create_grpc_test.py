# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the health-checks create grpc subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HealthChecksCreateGrpcAlphaTest(test_base.BaseTest,
                                      parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def RunCreate(self, command):
    self.Run('compute health-checks create grpc %s' % command)

  def testWithoutPortRelatedOptions(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Either --port, --port-name or --use-serving-port must be set for gRPC '
        'health check.'):
      self.RunCreate('my-health-check')
      self.CheckRequests()

  def testUriSupport(self):
    self.RunCreate("""
          https://compute.googleapis.com/compute/v1/projects/my-project/global/healthChecks/my-health-check
          --port 80
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=8888,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portName='magic-port',
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT)),
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=8888,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testCheckIntervalOption(self):
    self.RunCreate('my-health-check --port 80 --check-interval 34s')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testTimeoutSecOption(self):
    self.RunCreate('my-health-check --port 80 --timeout 2m')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testHealthyThresholdOption(self):
    self.RunCreate('my-health-check --port 80 --healthy-threshold 7')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testUnhealthyThresholdOption(self):
    self.RunCreate('my-health-check --port 80 --unhealthy-threshold 8')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project'))],)

  def testDescriptionOption(self):
    self.RunCreate("""
        my-health-check --port 80 --description "Circulation, Airway, Breathing"
    """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  description='Circulation, Airway, Breathing',
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testGrpcServiceNameOption(self):
    self.RunCreate(
        'my-health-check --port 80 --grpc-service-name my-gRPC-service')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      grpcServiceName='my-gRPC-service',
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=self.messages.GRPCHealthCheck
                      .PortSpecificationValueValuesEnum.USE_SERVING_PORT),
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

  @parameterized.named_parameters(
      ('DisableLogging', '--no-enable-logging', False),
      ('EnableLogging', '--enable-logging', True))
  def testLogConfig(self, enable_logs_flag, enable_logs):

    self.RunCreate("""my-health-check --port 80 {0}""".format(enable_logs_flag))

    expected_log_config = self.messages.HealthCheckLogConfig(enable=enable_logs)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2,
                  logConfig=expected_log_config),
              project='my-project'))],)


class RegionHealthChecksCreateGrpcAlphaTest(test_base.BaseTest,
                                            parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def RunCreate(self, command):
    self.Run(
        'compute health-checks create grpc --region us-west-1 %s' % command)

  def testGlobalHealthCheckCreate(self):
    self.Run("""
        compute health-checks create grpc my-health-check --port 80 --global
    """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Insert',
          self.messages.ComputeHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project'))],)

  def testWithoutPortRelatedOptions(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Either --port, --port-name or --use-serving-port must be set for gRPC '
        'health check.'):
      self.RunCreate('my-health-check')
      self.CheckRequests()

  def testUriSupport(self):
    self.RunCreate("""
          https://compute.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/healthChecks/my-health-check
          --port 80
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=8888,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portName='magic-port',
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testGrpcServiceNameOption(self):
    self.RunCreate(
        'my-health-check --port 80 --grpc-service-name my-gRPC-service')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      grpcServiceName='my-gRPC-service',
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testCheckIntervalOption(self):
    self.RunCreate('my-health-check --port 80 --check-interval 34s')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=34,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testTimeoutSecOption(self):
    self.RunCreate('my-health-check --port 80 --timeout 2m')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=120,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testHealthyThresholdOption(self):
    self.RunCreate('my-health-check --port 80 --healthy-threshold 7')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=7,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  def testUnhealthyThresholdOption(self):
    self.RunCreate('my-health-check --port 80 --unhealthy-threshold 8')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=8),
              project='my-project',
              region='us-west-1'))],)

  def testDescriptionOption(self):
    self.RunCreate("""
        my-health-check --port 80 --description "Circulation, Airway, Breathing"
    """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  description='Circulation, Airway, Breathing',
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2),
              project='my-project',
              region='us-west-1'))],)

  @parameterized.named_parameters(
      ('DisableLogging', '--no-enable-logging', False),
      ('EnableLogging', '--enable-logging', True))
  def testLogConfig(self, enable_logs_flag, enable_logs):

    self.RunCreate("""my-health-check --port 80 {0}""".format(enable_logs_flag))

    expected_log_config = self.messages.HealthCheckLogConfig(enable=enable_logs)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Insert',
          self.messages.ComputeRegionHealthChecksInsertRequest(
              healthCheck=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT)),
                  checkIntervalSec=5,
                  timeoutSec=5,
                  healthyThreshold=2,
                  unhealthyThreshold=2,
                  logConfig=expected_log_config),
              project='my-project',
              region='us-west-1'))],)


if __name__ == '__main__':
  test_case.main()
