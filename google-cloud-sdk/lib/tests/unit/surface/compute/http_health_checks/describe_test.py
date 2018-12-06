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
"""Tests for the http-health-checks describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class HttpHealthChecksDescribeTest(test_base.BaseTest,
                                   completer_test_base.CompleterBase,
                                   test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.HTTP_HEALTH_CHECKS[0]],
    ])

    self.Run("""
        compute http-health-checks describe my-http-health-check
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Get',
          messages.ComputeHttpHealthChecksGetRequest(
              httpHealthCheck='my-http-health-check',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            host: www.example.com
            name: health-check-1
            port: 8080
            requestPath: /testpath
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/health-check-1
            """))

  def testDescribeCompletion(self):
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        return_value=resource_projector.MakeSerializable(
            test_resources.HTTP_HEALTH_CHECKS),
        autospec=True)
    self.RunCompletion(
        'compute http-health-checks describe h',
        [
            'health-check-1',
            'health-check-2',
        ])


if __name__ == '__main__':
  test_case.main()
