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
"""Tests for the https-health-checks update subcommand."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HttpsHealthChecksUpdateTest(test_base.BaseTest,
                                  test_case.WithOutputCapture):

  def testNoArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run("""
          compute https-health-checks update my-health-check
          """)
    self.CheckRequests()

  def testUriSupport(self):
    messages = self.messages
    # This is the same as testHostOption, but uses a full URI.
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update
          {uri}/projects/my-project/global/httpsHealthChecks/my-health-check
          --host www.google.com
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update', messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.google.com',
                  port=443,
                  requestPath='/testpath'),
              project='my-project'))],
    )

  def testHostOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.google.com',
                                   port=443,
                                   requestPath='/testpath')],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --host www.google.com
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update', messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.google.com',
                  port=443,
                  requestPath='/testpath'),
              project='my-project'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testNoChanges(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
    ]

    self.Run("""
        compute https-health-checks update my-health-check
          --host www.example.com
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
    )

    self.AssertErrEquals(
        'No change requested; skipping update for [my-health-check].\n',
        normalize_space=True)

  def testJsonOutput(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.google.com',
                                   port=443,
                                   requestPath='/testpath')],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --host www.google.com
          --format json
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            [
              {
                "host": "www.google.com",
                "name": "my-health-check",
                "port": 443,
                "requestPath": "/testpath"
              }
            ]
            """))

  def testTextOutput(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.google.com',
                                   port=443,
                                   requestPath='/testpath')],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --host www.google.com
          --format text
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            host:        www.google.com
            name:        my-health-check
            port:        443
            requestPath: /testpath
            """))

  def testYamlOutput(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.google.com',
                                   port=443,
                                   requestPath='/testpath')],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --host www.google.com
          --format yaml
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            host: www.google.com
            name: my-health-check
            port: 443
            requestPath: /testpath
            """))

  def testUnsetHostOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --host ''
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  port=443,
                  requestPath='/testpath'),
              project='my-project'))],
    )

  def testPortOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --port 8888
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=8888,
                  requestPath='/testpath'),
              project='my-project'))],
    )

  def testRequestPathOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --request-path /newpath
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=443,
                  requestPath='/newpath'),
              project='my-project'))],
    )

  def testCheckIntervalOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --check-interval 30s
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=443,
                  requestPath='/testpath',
                  checkIntervalSec=30),
              project='my-project'))],
    )

  def testCheckIntervalBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute https-health-checks update my-health-check
            --check-interval 0
          """)
    self.CheckRequests()

  def testTimeoutSecOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --timeout 2m
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=443,
                  requestPath='/testpath',
                  timeoutSec=120),
              project='my-project'))],
    )

  def testTimeoutBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute https-health-checks update my-health-check
            --timeout 0
          """)
    self.CheckRequests()

  def testHealthyThresholdOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --healthy-threshold 7
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=443,
                  requestPath='/testpath',
                  healthyThreshold=7),
              project='my-project'))],
    )

  def testHealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp('must be an integer between 1 '
                                              'and 10'):
      self.Run("""
          compute https-health-checks update my-health-check
            --healthy-threshold 0
          """)
    self.CheckRequests()

  def testUnhealthyThresholdOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --unhealthy-threshold 8
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=443,
                  requestPath='/testpath',
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testUnhealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--unhealthy-threshold\] must be an integer between 1 and 10, '
        r'inclusive; received \[0\].'):
      self.Run("""
          compute https-health-checks update my-health-check
            --unhealthy-threshold 0
          """)
    self.CheckRequests()

  def testDescriptionOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --description 'Circulation, Airway, Breathing'
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=443,
                  requestPath='/testpath',
                  description='Circulation, Airway, Breathing'),
              project='my-project'))],
    )

  def testUnsetDescriptionOption(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.HttpsHealthCheck(name='my-health-check',
                                   host='www.example.com',
                                   port=443,
                                   requestPath='/testpath',
                                   description='Short Description',)],
        [],
    ])

    self.Run("""
        compute https-health-checks update my-health-check
          --description ''
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute.httpsHealthChecks,
          'Update',
          messages.ComputeHttpsHealthChecksUpdateRequest(
              httpsHealthCheck='my-health-check',
              httpsHealthCheckResource=messages.HttpsHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=443,
                  requestPath='/testpath'),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
