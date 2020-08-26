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
"""Tests for the routes describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.routes import test_resources


class RoutesDescribeTest(test_base.BaseTest,
                         completer_test_base.CompleterBase,
                         test_case.WithOutputCapture):

  def SetUp(self):
    self._routes = test_resources.ROUTES_V1

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [self._routes[0]],
    ])

    self.Run("""
        compute routes describe route-1
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Get',
          self.messages.ComputeRoutesGetRequest(
              route='route-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            destRange: 10.0.0.0/8
            name: route-1
            network: https://compute.googleapis.com/compute/{api}/projects/my-project/network/default
            nextHopIp: 10.240.0.0
            selfLink: https://compute.googleapis.com/compute/{api}/projects/my-project/global/routes/route-1
            """.format(api=self.api)))

  def testDescribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.ROUTES_V1)
    self.RunCompletion(
        'compute routes describe ',
        [
            'route-3',
            'route-4',
            'route-1',
            'route-2',
        ])

if __name__ == '__main__':
  test_case.main()
