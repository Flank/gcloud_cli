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
"""Tests for the instances move subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class RoutersGetStatusTest(test_base.BaseTest):

  def testCall(self):
    self.make_requests.side_effect = [[self.messages.RouterStatus()]]

    self.Run("""
        compute routers get-status my-router --region us-central1
        """)

    self.CheckRequests([(self.compute.routers, 'GetRouterStatus',
                         self.messages.ComputeRoutersGetRouterStatusRequest(
                             project='my-project',
                             region='us-central1',
                             router='my-router'))])


if __name__ == '__main__':
  test_case.main()
