# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for the networks get-effective-firewalls subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GetEffectiveFirewallsTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')

  def testGetEffectiveFirewalls(self):

    self.make_requests.side_effect = iter([
        ['firewalls'],
    ])

    self.Run('alpha compute networks get-effective-firewalls my-network')

    self.CheckRequests(
        [(self.compute.networks, 'GetEffectiveFirewalls',
          self.messages.ComputeNetworksGetEffectiveFirewallsRequest(
              network='my-network', project=self.Project()))],)
    self.assertMultiLineEqual(self.GetOutput().strip(),
                              textwrap.dedent('firewalls'))


if __name__ == '__main__':
  test_case.main()
