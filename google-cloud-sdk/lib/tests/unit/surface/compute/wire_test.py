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
"""Tests that ensure deserialization of server responses work properly."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import test_case
from six.moves import range


class WireTest(e2e_base.WithMockHttp, test_case.WithOutputCapture):

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')

  def testUnknownEnumHandling(self):
    self.AddHTTPResponse(
        'https://www.googleapis.com/batch/compute/v1',
        headers={'Content-type': 'multipart/mixed; boundary=BATCH_BOUNDARY'},
        expected_body=e2e_base.IGNORE,
        body=textwrap.dedent("""\
            --BATCH_BOUNDARY
            Content-Type: application/http
            Content-ID: <response-34573baf-914d-42df-bada-02a1d76cf771+0>

            HTTP/1.1 200 OK
            Content-Type: application/json; charset=UTF-8
            Date: Thu, 26 Jun 2014 17:43:17 GMT
            Expires: Thu, 26 Jun 2014 17:43:17 GMT
            Cache-Control: private, max-age=0
            Content-Length: 3077

            {
             "kind": "compute#project",
             "name": "my-project",
             "quotas": [
              {
               "metric": "SNAPSHOTS",
               "limit": 1000.0,
               "usage": 10.0
              },
              {
               "metric": "UNKNOWN_ENUM",
               "limit": 1000.0,
               "usage": 0.0
              }
             ]
            }

            --BATCH_BOUNDARY--
            """))

    self.Run("""\
      compute project-info describe
      """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            kind: compute#project
            name: my-project
            quotas:
            - limit: 1000.0
              metric: SNAPSHOTS
              usage: 10.0
            - limit: 1000.0
              metric: UNKNOWN_ENUM
              usage: 0.0
            """))

  def testUnknownStringFieldHandling(self):
    self.AddHTTPResponse(
        'https://www.googleapis.com/batch/compute/v1',
        headers={'Content-type': 'multipart/mixed; boundary=BATCH_BOUNDARY'},
        expected_body=e2e_base.IGNORE,
        body=textwrap.dedent("""\
            --BATCH_BOUNDARY
            Content-Type: application/http
            Content-ID: <response-34573baf-914d-42df-bada-02a1d76cf771+0>

            HTTP/1.1 200 OK
            Content-Type: application/json; charset=UTF-8
            Date: Thu, 26 Jun 2014 17:43:17 GMT
            Expires: Thu, 26 Jun 2014 17:43:17 GMT
            Cache-Control: private, max-age=0
            Content-Length: 3077

            {
             "kind": "compute#project",
             "name": "my-project",
             "unknownField": "Hello, world!"
            }

            --BATCH_BOUNDARY--
            """))

    self.Run("""\
      compute project-info describe
      """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            kind: compute#project
            name: my-project
            unknownField: Hello, world!
            """))

  def testUnknownNestedStructureFieldHandling(self):
    self.AddHTTPResponse(
        'https://www.googleapis.com/batch/compute/v1',
        headers={'Content-type': 'multipart/mixed; boundary=BATCH_BOUNDARY'},
        expected_body=e2e_base.IGNORE,
        body=textwrap.dedent("""\
            --BATCH_BOUNDARY
            Content-Type: application/http
            Content-ID: <response-34573baf-914d-42df-bada-02a1d76cf771+0>

            HTTP/1.1 200 OK
            Content-Type: application/json; charset=UTF-8
            Date: Thu, 26 Jun 2014 17:43:17 GMT
            Expires: Thu, 26 Jun 2014 17:43:17 GMT
            Cache-Control: private, max-age=0
            Content-Length: 3077

            {
             "kind": "compute#project",
             "name": "my-project",
             "unknownStructure": {
              "fieldOne": "Hello, world!",
              "fieldTwo": [1, 2, 3]
             }
            }

            --BATCH_BOUNDARY--
            """))

    self.Run("""\
      compute project-info describe
      """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            kind: compute#project
            name: my-project
            unknownStructure:
              fieldOne: Hello, world!
              fieldTwo:
              - 1
              - 2
              - 3
            """))

  def testWarningHandling(self):
    # gcloud repeatedly gets the operaiton until it has state "DONE". But it
    # doesn't check the state for the first response, since in an un-mocked
    # response it will never be DONE until at least the second. So we add this
    # twice to let the polling logic work.
    for _ in range(2):
      self.AddHTTPResponse(
          'https://www.googleapis.com/batch/compute/v1',
          headers={'Content-type': 'multipart/mixed; boundary=BATCH_BOUNDARY'},
          expected_body=e2e_base.IGNORE,
          body=textwrap.dedent("""\
              --BATCH_BOUNDARY
              Content-Type: application/http
              Content-ID: <response-34573baf-914d-42df-bada-02a1d76cf771+0>

              HTTP/1.1 200 OK
              Content-Type: application/json; charset=UTF-8
              Date: Thu, 26 Jun 2014 17:43:17 GMT
              Expires: Thu, 26 Jun 2014 17:43:17 GMT
              Cache-Control: private, max-age=0
              Content-Length: 3077

              {
               "kind": "compute#operation",
               "name": "my-operation",
               "status": "DONE",
               "operationType": "insert",
               "targetLink": "endpoint/project/1/global/networks/network-1",
               "warnings": {
                 "message": "scary-warning-message"
               }
              }

              --BATCH_BOUNDARY--
              """))

    self.Run("""\
      compute networks create network-1
      """)

    self.AssertErrContains('WARNING:')
    self.AssertErrContains('scary-warning-message')


if __name__ == '__main__':
  test_case.main()
