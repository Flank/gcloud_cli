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
"""Tests for the health-checks update https subcommand."""

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


class HealthChecksUpdateHttpsTest(
    test_base.BaseTest, test_case.WithOutputCapture, parameterized.TestCase):

  def global_flag(self):
    return ''

  def testNoArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run('compute health-checks update https my-health-check' +
               self.global_flag())
    self.CheckRequests()

  def testUriSupport(self):
    # This is the same as testHostOption, but uses a full URI.
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https
          https://compute.googleapis.com/compute/v1/projects/my-project/global/healthChecks/my-health-check
          --host www.google.com
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update', self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.google.com',
                      port=80,
                      requestPath='/testpath')),
              project='my-project'))],
    )

  def testNoChange(self):
    self.make_requests.side_effect = [
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
    ]

    self.Run("""
        compute health-checks update https my-health-check
          --host www.example.com
        """ + self.global_flag())

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

  def testHostOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.google.com',
                port=80,
                requestPath='/testpath'))],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --host www.google.com
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update', self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.google.com',
                      port=80,
                      requestPath='/testpath')),
              project='my-project'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testJsonOutput(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.google.com',
                port=80,
                requestPath='/testpath'))],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --host www.google.com
          --format json
        """ + self.global_flag())

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            [
              {
                "httpsHealthCheck": {
                  "host": "www.google.com",
                  "port": 80,
                  "requestPath": "/testpath"
                },
                "name": "my-health-check",
                "type": "HTTPS"
              }
            ]
            """))

  def testTextOutput(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.google.com',
                port=80,
                requestPath='/testpath'))],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --host www.google.com
          --format text
        """ + self.global_flag())

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            httpsHealthCheck.host:        www.google.com
            httpsHealthCheck.port:        80
            httpsHealthCheck.requestPath: /testpath
            name:                         my-health-check
            type:                         HTTPS
            """))

  def testYamlOutput(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.google.com',
                port=80,
                requestPath='/testpath'))],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --host www.google.com
          --format yaml
        """ + self.global_flag())

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            httpsHealthCheck:
              host: www.google.com
              port: 80
              requestPath: /testpath
            name: my-health-check
            type: HTTPS
            """))

  def testUnsetHostOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check --host ''
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      port=80,
                      requestPath='/testpath')),
              project='my-project'))],
    )

  def testPortOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    host='www.example.com', port=80, requestPath='/testpath'))
        ],
        [],
    ])

    self.Run('compute health-checks update https my-health-check --port 8888' +
             self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=8888,
                      portSpecification=(
                          self.messages.HTTPSHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      requestPath='/testpath')),
              project='my-project'))],
    )

  def testPortNameOptionWithPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    host='www.example.com',
                    portSpecification=(
                        self.messages.HTTPSHealthCheck
                        .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                    portName='old-port'))
        ],
        [],
    ])

    self.Run('compute health-checks update https my-health-check '
             '--port-name new-port' + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      portSpecification=(
                          self.messages.HTTPSHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      portName='new-port')),
              project='my-project'))],
    )

  def testPortNameOptionWithoutPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    host='www.example.com'))
        ],
        [],
    ])

    self.Run('compute health-checks update https my-health-check '
             '--port-name new-port' + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      portSpecification=(
                          self.messages.HTTPSHealthCheck
                          .PortSpecificationValueValuesEnum.USE_NAMED_PORT),
                      portName='new-port')),
              project='my-project'))],
    )

  def testUnsetPortNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    portName='happy-port', requestPath='/testpath'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check --port-name ''
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      portSpecification=(
                          self.messages.HTTPSHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      requestPath='/testpath')),
              project='my-project'))],
    )

  def testPortAndPortNameOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    host='www.example.com'))
        ],
        [],
    ])

    self.Run('compute health-checks update https my-health-check '
             '--port 8888 --port-name new-port' + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      portSpecification=(
                          self.messages.HTTPSHealthCheck
                          .PortSpecificationValueValuesEnum.USE_FIXED_PORT),
                      port=8888)),
              project='my-project'))],
    )

  def testUseServingPortOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck())
        ],
        [],
    ])

    self.Run('compute health-checks update https my-health-check '
             '--use-serving-port' + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      portSpecification=(
                          self.messages.HTTPSHealthCheck
                          .PortSpecificationValueValuesEnum.USE_SERVING_PORT))),
              project='my-project'))],
    )

  def testUseServingPortOptionWithPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    portName='old-port'))
        ],
        [],
    ])

    self.Run('compute health-checks update https my-health-check '
             '--use-serving-port' + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks, 'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check', project='my-project'))],
        [(self.compute.healthChecks, 'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      portSpecification=(
                          self.messages.HTTPSHealthCheck
                          .PortSpecificationValueValuesEnum.USE_SERVING_PORT))),
              project='my-project'))],
    )

  @parameterized.parameters(('--port', 80), ('--port-name', 'my-port'))
  def testUseServingPortOptionErrors(self, flag, flag_value):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck())
        ],
        [],
    ])

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--use-serving-port]: {0} cannot '
        'be specified when using: --use-serving-port'.format(flag)):
      self.Run("""
          compute health-checks update https my-health-check
          --use-serving-port {0} {1} {2}
      """.format(flag, flag_value, self.global_flag()))

  def testRequestPathOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --request-path /newpath
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/newpath')),
              project='my-project'))],
    )

  def testCheckIntervalOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --check-interval 30s
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath'),
                  checkIntervalSec=30),
              project='my-project'))],
    )

  def testCheckIntervalBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute health-checks update https my-health-check
            --check-interval 0
          """ + self.global_flag())
    self.CheckRequests()

  def testTimeoutSecOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --timeout 2m
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath'),
                  timeoutSec=120),
              project='my-project'))],
    )

  def testTimeoutBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute health-checks update https my-health-check
             --timeout 0
          """ + self.global_flag())
    self.CheckRequests()

  def testHealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --healthy-threshold 7
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath'),
                  healthyThreshold=7),
              project='my-project'))],
    )

  def testHealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must be an integer between 1 and 10'):
      self.Run("""
          compute health-checks update https my-health-check
            --healthy-threshold 0
          """ + self.global_flag())
    self.CheckRequests()

  def testUnhealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --unhealthy-threshold 8
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath'),
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testUnhealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--unhealthy-threshold\] must be an integer between 1 and 10, '
        r'inclusive; received \[0\].'):
      self.Run("""
          compute health-checks update https my-health-check
            --unhealthy-threshold 0
          """ + self.global_flag())
    self.CheckRequests()

  def testDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --description 'Circulation, Airway, Breathing'
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath'),
                  description='Circulation, Airway, Breathing'),
              project='my-project'))],
    )

  def testUnsetDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'),
            description='Short Description')],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --description ''
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath')),
              project='my-project'))],
    )

  def testUpdatingDifferentProtocol(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP,
            httpHealthCheck=self.messages.HTTPHealthCheck(
                port=80))],
        [],
    ])

    with self.assertRaisesRegex(
        core_exceptions.Error,
        'update https subcommand applied to health check with protocol HTTP'):
      self.Run('compute health-checks update https my-health-check --port 8888'
               + self.global_flag())

  def testProxyHeaderOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --proxy-header PROXY_V1
          """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath',
                      proxyHeader=(self.messages.HTTPSHealthCheck
                                   .ProxyHeaderValueValuesEnum.PROXY_V1))),
              project='my-project'))],
    )

  def testProxyHeaderBadValue(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    with self.AssertRaisesArgumentErrorRegexp(
        'argument --proxy-header: Invalid choice: \'bad_value\''):
      self.Run("""
          compute health-checks update https my-health-check
            --proxy-header bad_value
          """ + self.global_flag())

  def testResponseOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --response new-response
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath',
                      response='new-response')),
              project='my-project'))],
    )

  def testUnsetResponseOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
            httpsHealthCheck=self.messages.HTTPSHealthCheck(
                host='www.example.com',
                port=80,
                requestPath='/testpath',
                response='Hello'))],
        [],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --response ''
        """ + self.global_flag())

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Get',
          self.messages.ComputeHealthChecksGetRequest(
              healthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.healthChecks,
          'Update',
          self.messages.ComputeHealthChecksUpdateRequest(
              healthCheck='my-health-check',
              healthCheckResource=self.messages.HealthCheck(
                  name='my-health-check',
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.example.com',
                      port=80,
                      requestPath='/testpath')),
              project='my-project'))],
    )


class HealthChecksUpdateHttpsBetaTest(HealthChecksUpdateHttpsTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def global_flag(self):
    return ' --global'


class HealthChecksUpdateHttpsAlphaTest(HealthChecksUpdateHttpsBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)


class RegionHealthChecksCreateHttpsBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def testUriSupport(self):
    # This is the same as testHostOption, but uses a full URI.
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    host='www.example.com', port=80, requestPath='/testpath'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update https
          https://compute.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/healthChecks/my-health-check
          --host www.google.com
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.google.com', port=80, requestPath='/testpath')),
              project='my-project',
              region='us-west-1'))],
    )

  def testHostOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    host='www.example.com', port=80, requestPath='/testpath'))
        ],
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                httpsHealthCheck=self.messages.HTTPSHealthCheck(
                    host='www.google.com', port=80, requestPath='/testpath'))
        ],
    ])

    self.Run("""
        compute health-checks update https my-health-check
          --host www.google.com --region us-west-1
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.HTTPS,
                  httpsHealthCheck=self.messages.HTTPSHealthCheck(
                      host='www.google.com', port=80, requestPath='/testpath')),
              project='my-project',
              region='us-west-1'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())


class RegionHealthChecksCreateHttpsAlphaTest(
    RegionHealthChecksCreateHttpsBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)


if __name__ == '__main__':
  test_case.main()
