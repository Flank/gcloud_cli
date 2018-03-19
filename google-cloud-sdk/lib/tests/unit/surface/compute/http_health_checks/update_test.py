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
"""Tests for the http-health-checks update subcommand."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class HttpHealthChecksUpdateTest(test_base.BaseTest,
                                 test_case.WithOutputCapture):

  def testNoArgs(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run(
          'compute http-health-checks update my-health-check')
    self.CheckRequests()

  def testNoChange(self):
    self.make_requests.side_effect = iter([
        [
            messages.HttpHealthCheck(
                name='my-health-check',
                host='www.example.com',
                port=80,
                requestPath='/testpath')
        ],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
        --host www.example.com
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks, 'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check', project='my-project'))],)

    self.AssertErrEquals(
        'No change requested; skipping update for [my-health-check].\n',
        normalize_space=True)

  def testUriSupport(self):
    # This is the same as testHostOption, but uses a full URI.
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute http-health-checks update
          https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/my-health-check
          --host www.google.com
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update', messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.google.com',
                  port=80,
                  requestPath='/testpath'),
              project='my-project'))],
    )

  def testHostOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.google.com',
                                  port=80,
                                  requestPath='/testpath')],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --host www.google.com
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update', messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.google.com',
                  port=80,
                  requestPath='/testpath'),
              project='my-project'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testJsonOutput(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.google.com',
                                  port=80,
                                  requestPath='/testpath')],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
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
                "port": 80,
                "requestPath": "/testpath"
              }
            ]
            """))

  def testTextOutput(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.google.com',
                                  port=80,
                                  requestPath='/testpath')],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --host www.google.com
          --format text
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            host:        www.google.com
            name:        my-health-check
            port:        80
            requestPath: /testpath
            """))

  def testYamlOutput(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.google.com',
                                  port=80,
                                  requestPath='/testpath')],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --host www.google.com
          --format yaml
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            host: www.google.com
            name: my-health-check
            port: 80
            requestPath: /testpath
            """))

  def testUnsetHostOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --host ''
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  port=80,
                  requestPath='/testpath'),
              project='my-project'))],
    )

  def testPortOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run(
        'compute http-health-checks update my-health-check --port 8888')

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=8888,
                  requestPath='/testpath'),
              project='my-project'))],
    )

  def testRequestPathOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --request-path /newpath
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=80,
                  requestPath='/newpath'),
              project='my-project'))],
    )

  def testCheckIntervalOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --check-interval 30s
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=80,
                  requestPath='/testpath',
                  checkIntervalSec=30),
              project='my-project'))],
    )

  def testCheckIntervalBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute http-health-checks update my-health-check
            --check-interval 0
          """)
    self.CheckRequests()

  def testTimeoutSecOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --timeout 2m
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=80,
                  requestPath='/testpath',
                  timeoutSec=120),
              project='my-project'))],
    )

  def testTimeoutBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must not be less than 1 second or greater than 300 seconds'):
      self.Run("""
          compute http-health-checks update my-health-check
             --timeout 0
          """)
    self.CheckRequests()

  def testHealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --healthy-threshold 7
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=80,
                  requestPath='/testpath',
                  healthyThreshold=7),
              project='my-project'))],
    )

  def testHealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        'must be an integer between 1 and 10'):
      self.Run("""
          compute http-health-checks update my-health-check
            --healthy-threshold 0
          """)
    self.CheckRequests()

  def testUnhealthyThresholdOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --unhealthy-threshold 8
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=80,
                  requestPath='/testpath',
                  unhealthyThreshold=8),
              project='my-project'))],
    )

  def testUnhealthyTresholdBadValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--unhealthy-threshold\] must be an integer between 1 and 10, '
        r'inclusive; received \[0\].'):
      self.Run("""
          compute http-health-checks update my-health-check
            --unhealthy-threshold 0
          """)
    self.CheckRequests()

  def testDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath')],
        [],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --description 'Circulation, Airway, Breathing'
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=80,
                  requestPath='/testpath',
                  description='Circulation, Airway, Breathing'),
              project='my-project'))],
    )

  def testUnsetDescriptionOption(self):
    self.make_requests.side_effect = iter([
        [messages.HttpHealthCheck(name='my-health-check',
                                  host='www.example.com',
                                  port=80,
                                  requestPath='/testpath',
                                  description='Short Description',)],
        [],
    ])

    self.Run("""
        compute http-health-checks update my-health-check
          --description ''
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-health-check',
              project='my-project'))],
        [(self.compute_v1.httpHealthChecks,
          'Update',
          messages.ComputeHttpHealthChecksUpdateRequest(
              httpHealthCheck='my-health-check',
              httpHealthCheckResource=messages.HttpHealthCheck(
                  name='my-health-check',
                  host='www.example.com',
                  port=80,
                  requestPath='/testpath'),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
