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
"""Tests for the health-checks update gRPC subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as core_exceptions

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HealthChecksUpdateGrpcAlphaTest(test_base.BaseTest,
                                      test_case.WithOutputCapture,
                                      parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testNoArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run('compute health-checks update grpc my-health-check')
    self.CheckRequests()

  def testUriSupport(self):
    # This is the same as testHostOption, but uses a full URI.
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    port=80,
                    grpcServiceName='old'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc
          https://compute.googleapis.com/compute/v1/projects/my-project/global/healthChecks/my-health-check
          --grpc-service-name "new"
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80, grpcServiceName='new')),
              project='my-project'))],
    )

  def testNoChange(self):
    self.make_requests.side_effect = [
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
            grpcHealthCheck=self.messages.GRPCHealthCheck(
                port=80,
                grpcServiceName='my-service'))],
    ]

    self.Run("""
        compute health-checks update grpc my-health-check
          --grpc-service-name "my-service"
        """)

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
    )

    self.AssertErrEquals(
        'No change requested; skipping update for [my-health-check].\n',
        normalize_space=True)

  def testJsonOutput(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --port 80
          --format json
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            [
              {
                "grpcHealthCheck": {
                  "port": 80
                },
                "name": "my-health-check",
                "type": "GRPC"
              }
            ]
            """))

  def testTextOutput(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=77))
        ],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --port 77
          --format text
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            grpcHealthCheck.port: 77
            name:                 my-health-check
            type:                 GRPC
            """))

  def testYamlOutput(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --port 80
          --format yaml
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            grpcHealthCheck:
              port: 80
            name: my-health-check
            type: GRPC
            """))

  def testPortOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run('compute health-checks update grpc my-health-check --port 8888')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=8888,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT))),
              project='my-project'))],
    )

  def testPortNameOptionWithPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portName='old-port'))
        ],
        [],
    ])

    self.Run('compute health-checks update grpc my-health-check '
             '--port-name new-port')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      portName='new-port')),
              project='my-project'))],
    )

  def testPortNameOptionWithoutPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portSpecification=(
                        self.messages.GRPCHealthCheck
                        .PortSpecificationValueValuesEnum.USE_SERVING_PORT)))
        ],
        [],
    ])

    self.Run('compute health-checks update grpc my-health-check '
             '--port-name new-port')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      portName='new-port')),
              project='my-project'))],
    )

  def testUnsetPortNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portName='happy-port'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check --port-name ''
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT))),
              project='my-project'))],
    )

  def testPortAndPortNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    port=80))
        ],
        [],
    ])

    self.Run('compute health-checks update grpc my-health-check '
             '--port 8888 --port-name new-port')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      port=8888)),
              project='my-project'))],
    )

  def testUseServingPortOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck())
        ],
        [],
    ])

    self.Run('compute health-checks update grpc my-health-check '
             '--use-serving-port')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_SERVING_PORT))),
              project='my-project'))],
    )

  def testUseServingPortOptionWithPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portName='old-port'))
        ],
        [],
    ])

    self.Run('compute health-checks update grpc my-health-check '
             '--use-serving-port')

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_SERVING_PORT))),
              project='my-project'))],
    )

  @parameterized.parameters(('--port', 80), ('--port-name', 'my-port'))
  def testUseServingPortOptionErrors(self, flag, flag_value):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck())
        ],
        [],
    ])

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--use-serving-port]: {0} cannot '
        'be specified when using: --use-serving-port'.format(flag)):
      self.Run("""
          compute health-checks update grpc my-health-check
          --use-serving-port {0} {1}
      """.format(flag, flag_value))

  def testCheckIntervalOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --check-interval 30s
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  checkIntervalSec=30),
              project='my-project'))],
    )

  def testCheckIntervalBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute health-checks update grpc my-health-check
            --check-interval 0
          """)
    self.CheckRequests()

  def testTimeoutSecOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --timeout 2m
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  timeoutSec=120),
              project='my-project'))],
    )

  def testTimeoutBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute health-checks update grpc my-health-check
             --timeout 0
          """)
    self.CheckRequests()

  def testHealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --healthy-threshold 7
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  healthyThreshold=7),
              project='my-project'))],
    )

  def testHealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must be an integer between 1 and 10'):
      self.Run("""
          compute health-checks update grpc my-health-check
            --healthy-threshold 0
          """)
    self.CheckRequests()

  def testUnhealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --unhealthy-threshold 8
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testUnhealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--unhealthy-threshold\] must be an integer between 1 and 10, '
        r'inclusive; received \[0\].'):
      self.Run("""
          compute health-checks update grpc my-health-check
            --unhealthy-threshold 0
          """)
    self.CheckRequests()

  def testDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --description 'Circulation, Airway, Breathing'
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  description='Circulation, Airway, Breathing'),
              project='my-project'))],
    )

  def testUnsetDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                description='Short Description')
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --description ''
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80)),
              project='my-project'))],
    )

  def testUpdatingDifferentProtocol(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
            tcpHealthCheck=self.messages.TCPHealthCheck(
                port=80))],
        [],
    ])

    with self.assertRaisesRegex(
        core_exceptions.Error,
        'update grpc subcommand applied to health check with protocol TCP'):
      self.Run('compute health-checks update grpc my-health-check --port 8888')

  def testGrpcServiceNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    port=80, grpcServiceName='my-gRPC-service'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --grpc-service-name my-new-gRPC-service
        """)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80, grpcServiceName='my-new-gRPC-service')),
              project='my-project'))],
    )

  def testUnsetGrpcServiceNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portName='happy-port',
                    grpcServiceName='my-new-gRPC-service'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check --grpc-service-name ''
        """)
    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portName='happy-port')),
              project='my-project'))],
    )

  @parameterized.named_parameters(
      ('DisableLogging', '--no-enable-logging', False),
      ('EnableLogging', '--enable-logging', True))
  def testLogConfig(self, enable_logs_flag, enable_logs):

    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""compute health-checks update grpc my-health-check {0}""".format(
        enable_logs_flag))

    expected_log_config = self.messages.HealthCheckLogConfig(enable=enable_logs)

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  logConfig=expected_log_config),
              project='my-project'))],
    )

  def testEnableToDisableLogConfig(self):
    log_config = self.messages.HealthCheckLogConfig(enable=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                logConfig=log_config)
        ],
        [],
    ])

    self.Run(
        """compute health-checks update grpc my-health-check --no-enable-logging"""
    )

    expected_log_config = self.messages.HealthCheckLogConfig(enable=False)
    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  logConfig=expected_log_config),
              project='my-project'))],
    )


class RegionHealthChecksUpdateGrpcAlphaTest(test_base.BaseTest,
                                            parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testNoArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run("""
          compute health-checks update grpc my-health-check --region us-west-1
      """)
    self.CheckRequests()

  def testUriSupport(self):
    # This is the same as testHostOption, but uses a full URI.
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    port=80,
                    grpcServiceName='old'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc
          https://compute.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/healthChecks/my-health-check
          --grpc-service-name "new"
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80,
                      grpcServiceName='new')),
              project='my-project',
              region='us-west-1'))],
    )

  def testNoChange(self):
    self.make_requests.side_effect = [
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    port=80,
                    grpcServiceName='my-service'))
        ],
    ]

    self.Run("""
        compute health-checks update grpc my-health-check
          --grpc-service-name "my-service" --region us-west-1
        """)

    self.CheckRequests([(self.compute.regionHealthChecks, 'Get',
                         self.messages.ComputeRegionHealthChecksGetRequest(
                             healthCheck='my-health-check',
                             project='my-project',
                             region='us-west-1'))],)

    self.AssertErrEquals(
        'No change requested; skipping update for [my-health-check].\n',
        normalize_space=True)

  def testJsonOutput(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --port 80
          --format json --region us-west-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            [
              {
                "grpcHealthCheck": {
                  "port": 80
                },
                "name": "my-health-check",
                "type": "GRPC"
              }
            ]
            """))

  def testTextOutput(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=66))
        ],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --port 66
          --format text --region us-west-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            grpcHealthCheck.port: 66
            name:                 my-health-check
            type:                 GRPC
            """))

  def testYamlOutput(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --port 80
          --format yaml --region us-west-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            grpcHealthCheck:
              port: 80
            name: my-health-check
            type: GRPC
            """))

  def testPortOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --port 8888 --region us-west-1
    """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=8888,
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT))),
              project='my-project',
              region='us-west-1'))],
    )

  def testPortNameOptionWithPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portName='old-port'))
        ],
        [],
    ])

    self.Run('compute health-checks update grpc my-health-check '
             '--port-name new-port --region us-west-1')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      portName='new-port')),
              project='my-project',
              region='us-west-1'))],
    )

  def testPortNameOptionWithoutPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portSpecification=(
                        self.messages.GRPCHealthCheck
                        .PortSpecificationValueValuesEnum.USE_SERVING_PORT)))
        ],
        [],
    ])

    self.Run('compute health-checks update grpc my-health-check '
             '--port-name new-port --region us-west-1')

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      portName='new-port')),
              project='my-project',
              region='us-west-1'))],
    )

  def testUnsetPortNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portName='happy-port'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check --port-name ''
        --region us-west-1
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portSpecification=(
                          self.messages.GRPCHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT))),
              project='my-project',
              region='us-west-1'))],
    )

  def testCheckIntervalOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --check-interval 30s --region us-west-1
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  checkIntervalSec=30),
              project='my-project',
              region='us-west-1'))],
    )

  def testCheckIntervalBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute health-checks update grpc my-health-check
            --check-interval 0 --region us-west-1
          """)
    self.CheckRequests()

  def testTimeoutSecOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --timeout 2m --region us-west-1
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  timeoutSec=120),
              project='my-project',
              region='us-west-1'))],
    )

  def testTimeoutBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute health-checks update grpc my-health-check
             --timeout 0 --region us-west-1
          """)
    self.CheckRequests()

  def testHealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --healthy-threshold 7 --region us-west-1
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  healthyThreshold=7),
              project='my-project',
              region='us-west-1'))],
    )

  def testHealthyThresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must be an integer between 1 and 10'):
      self.Run("""
          compute health-checks update grpc my-health-check
            --healthy-threshold 0 --region us-west-1
          """)
    self.CheckRequests()

  def testUnhealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --unhealthy-threshold 8 --region us-west-1
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  unhealthyThreshold=8),
              project='my-project',
              region='us-west-1'))],
    )

  def testUnhealthyThresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--unhealthy-threshold\] must be an integer between 1 and 10, '
        r'inclusive; received \[0\].'):
      self.Run("""
          compute health-checks update grpc my-health-check
            --unhealthy-threshold 0 --region us-west-1
          """)
    self.CheckRequests()

  def testDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --description 'Circulation, Airway, Breathing' --region us-west-1
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  description='Circulation, Airway, Breathing'),
              project='my-project',
              region='us-west-1'))],
    )

  def testUnsetDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                description='Short Description')
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --description '' --region us-west-1
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80)),
              project='my-project',
              region='us-west-1'))],
    )

  def testUpdatingDifferentProtocol(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.TCP,
                tcpHealthCheck=self.messages.TCPHealthCheck(port=80))
        ],
        [],
    ])

    with self.assertRaisesRegex(
        core_exceptions.Error,
        'update grpc subcommand applied to health check with protocol TCP'):
      self.Run("""
          compute health-checks update grpc my-health-check
            --port 8888 --region us-west-1""")

  def testGrpcServiceNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    port=80, grpcServiceName='my-gRPC-service'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --grpc-service-name my-new-gRPC-service --region us-west-1
        """)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      port=80, grpcServiceName='my-new-gRPC-service')),
              project='my-project',
              region='us-west-1'))],
    )

  def testUnsetGrpcServiceNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(
                    portName='happy-port', grpcServiceName='my-gRPC-service'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update grpc my-health-check
          --grpc-service-name '' --region us-west-1
        """)
    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(
                      portName='happy-port')),
              project='my-project',
              region='us-west-1'))],
    )

  @parameterized.named_parameters(
      ('DisableLogging', '--no-enable-logging', False),
      ('EnableLogging', '--enable-logging', True))
  def testLogConfig(self, enable_logs_flag, enable_logs):

    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80))
        ],
        [],
    ])

    self.Run("""compute health-checks update grpc my-health-check
     --region us-west-1 {0}""".format(
         enable_logs_flag))

    expected_log_config = self.messages.HealthCheckLogConfig(enable=enable_logs)

    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  logConfig=expected_log_config),
              project='my-project',
              region='us-west-1'))],
    )

  def testEnableToDisableLogConfig(self):
    log_config = self.messages.HealthCheckLogConfig(enable=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                logConfig=log_config)
        ],
        [],
    ])

    self.Run(
        """compute health-checks update grpc my-health-check
         --region us-west-1 --no-enable-logging"""
    )

    expected_log_config = self.messages.HealthCheckLogConfig(enable=False)
    self.CheckRequests(
        [(self.compute.regionHealthChecks, 'Get',
          self.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project',
              region='us-west-1'))],
        [(self.compute.regionHealthChecks, 'Update',
          self.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.GRPC,
                  grpcHealthCheck=self.messages.GRPCHealthCheck(port=80),
                  logConfig=expected_log_config),
              project='my-project',
              region='us-west-1'))],
    )


if __name__ == '__main__':
  test_case.main()
