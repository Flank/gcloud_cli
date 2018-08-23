# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the health-checks update udp subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HealthChecksUpdateUdpTest(test_base.BaseTest,
                                test_case.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testNoArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run('compute health-checks update udp my-health-check')
    self.CheckRequests()

  def testEmptyRequestResponse(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='sync',
                port=80,
                response='ack'))],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        '"request" field for UDP can not be empty.'):
      self.Run("""
        compute health-checks update udp my-health-check
        --request ''
        --response ack
        --global
        """)
    self.CheckRequests()

    with self.AssertRaisesToolExceptionRegexp(
        '"response" field for UDP can not be empty.'):
      self.Run("""
        compute health-checks update udp my-health-check
        --request sync
        --response ''
        --global
        """)
    self.CheckRequests()

  def testNoChange(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=80))],
    ])

    self.Run("""
      compute health-checks update udp my-health-check --port 80 --global
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

  def testUriSupport(self):
    # This is the same as testRequestOption, but uses a full URI.
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='initial-req',
                port=80,
                response='ack'))],
        [],
    ])

    self.Run("""
        compute health-checks update udp
          https://www.googleapis.com/compute/v1/projects/my-project/global/healthChecks/my-health-check
          --request req
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='req',
                      port=80,
                      response='ack')),
              project='my-project'))],
    )

  def testRequestOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='req1',
                port=80,
                response='ack'))],
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='req2',
                port=80,
                response='ack'))],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --request req2 --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='req2',
                      port=80,
                      response='ack')),
              project='my-project'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testJsonOutput(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='req-1',
                port=80))],
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='req-2',
                port=80))],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --request req-2
          --format json
          --global
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            [
              {
                "name": "my-health-check",
                "type": "UDP",
                "udpHealthCheck": {
                  "port": 80,
                  "request": "req-2"
                }
              }
            ]
            """))

  def testTextOutput(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='req-1',
                port=80,
                portName='happy-port',
                response='ack-1'))],
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='req-2',
                port=80,
                portName='happy-port',
                response='ack-2'))],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --request req-2
          --format text
          --global
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            name:                    my-health-check
            type:                    UDP
            udpHealthCheck.port:     80
            udpHealthCheck.portName: happy-port
            udpHealthCheck.request:  req-2
            udpHealthCheck.response: ack-2
            """))

  def testYamlOutput(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='req_1',
                port=80,
                response='ack'))],
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                request='req_2',
                port=80,
                response='ack'))],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --request req_2
          --format yaml
          --global
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            name: my-health-check
            type: UDP
            udpHealthCheck:
              port: 80
              request: req_2
              response: ack
            """))

  def testPortOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=80))],
        [],
    ])

    self.Run("""
      compute health-checks update udp my-health-check --port 8888 --global
    """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=8888)),
              project='my-project'))],
    )

  def testPortNameOptionWithPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                portName='old-port'))],
        [],
    ])

    self.Run('compute health-checks update udp my-health-check '
             '--port-name new-port --global')

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      portName='new-port')),
              project='my-project'))],
    )

  def testPortNameOptionWithoutPreexistingPortName(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck())],
        [],
    ])

    self.Run('compute health-checks update udp my-health-check '
             '--port-name new-port --global')

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      portName='new-port')),
              project='my-project'))],
    )

  def testUnsetPortNameOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                portName='happy-port'))],
        [],
    ])

    self.Run("""
        compute health-checks update udp my-health-check --port-name '' --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck()),
              project='my-project'))],
    )

  def testResponseOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=88,
                portName='happy-port',
                request='req',
                response='old-response'))],
        [],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --response new-response --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=88,
                      portName='happy-port',
                      request='req',
                      response='new-response')),
              project='my-project'))],
    )

  def testCheckIntervalOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=80,
                response='///'))],
        [],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --check-interval 30s --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=80,
                      response='///'),
                  checkIntervalSec=30),
              project='my-project'))],
    )

  def testCheckIntervalBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute health-checks update udp my-health-check
            --check-interval 0 --global
          """)
    self.CheckRequests()

  def testTimeoutSecOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=80,
                request='/',
                response='///'))],
        [],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --timeout 2m --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=80,
                      request='/',
                      response='///'),
                  timeoutSec=120),
              project='my-project'))],
    )

  def testTimeoutBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute health-checks update udp my-health-check
             --timeout 0 --global
          """)
    self.CheckRequests()

  def testHealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=80))],
        [],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --healthy-threshold 7 --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=80),
                  healthyThreshold=7),
              project='my-project'))],
    )

  def testHealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must be an integer between 1 and 10'):
      self.Run("""
          compute health-checks update udp my-health-check
            --healthy-threshold 0 --global
          """)
    self.CheckRequests()

  def testUnhealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=80,
                portName='happy-port'))],
        [],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --unhealthy-threshold 8 --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=80,
                      portName='happy-port'),
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testUnhealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--unhealthy-threshold\] must be an integer between 1 and 10, '
        r'inclusive; received \[0\].'):
      self.Run("""
          compute health-checks update udp my-health-check
            --unhealthy-threshold 0 --global
          """)
    self.CheckRequests()

  def testDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=80))],
        [],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --description 'Circulation, Airway, Breathing' --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=80),
                  description='Circulation, Airway, Breathing'),
              project='my-project'))],
    )

  def testUnsetDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [self.messages.HealthCheck(
            name='my-health-check',
            type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=self.messages.UDPHealthCheck(
                port=80),
            description='Short Description')],
        [],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --description '' --global
        """)

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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      port=80)),
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
        'update udp subcommand applied to health check with protocol HTTP'):
      self.Run("""
        compute health-checks update udp my-health-check --port 8888 --global
      """)


class RegionHealthChecksUpdateUdpTest(test_base.BaseTest,
                                      test_case.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testUriSupport(self):
    # This is the same as testRequestOption, but uses a full URI.
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                udpHealthCheck=self.messages.UDPHealthCheck(
                    request='initial-req', port=80, response='ack'))
        ],
        [],
    ])

    self.Run("""
        compute health-checks update udp
          https://www.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/healthChecks/my-health-check
          --request req
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='req', port=80, response='ack')),
              project='my-project',
              region='us-west-1'))],
    )

  def testRequestOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                udpHealthCheck=self.messages.UDPHealthCheck(
                    request='req1', port=80, response='ack'))
        ],
        [
            self.messages.HealthCheck(
                name='my-health-check',
                type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                udpHealthCheck=self.messages.UDPHealthCheck(
                    request='req2', port=80, response='ack'))
        ],
    ])

    self.Run("""
        compute health-checks update udp my-health-check
          --request req2 --region us-west-1
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
                  type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
                  udpHealthCheck=self.messages.UDPHealthCheck(
                      request='req2', port=80, response='ack')),
              project='my-project',
              region='us-west-1'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())


if __name__ == '__main__':
  test_case.main()
