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
"""Tests for the https-health-checks describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.health_checks import test_resources


class HttpsHealthChecksDescribeTest(test_base.BaseTest,
                                    test_case.WithOutputCapture):

  def SetUp(self):
    self._https_health_checks = test_resources.HTTPS_HEALTH_CHECKS_V1

  def testSimpleCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._https_health_checks[0]],
    ])

    self.Run("""
        compute https-health-checks describe my-https-health-check
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Get',
          messages.ComputeHttpsHealthChecksGetRequest(
              httpsHealthCheck='my-https-health-check',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            host: www.example.com
            name: https-health-check-1
            port: 8888
            requestPath: /testpath
            selfLink: {compute_uri}/projects/my-project/global/httpsHealthChecks/https-health-check-1
            """.format(compute_uri=self.compute_uri)))


if __name__ == '__main__':
  test_case.main()
