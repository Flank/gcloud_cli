# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Tests for the remove-interface subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import router_test_utils
from tests.lib.surface.compute import test_base


class RemoveInterfaceTest(test_base.BaseTest):

  def testSimple(self):
    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    expected = copy.deepcopy(orig)

    expected.interfaces.pop()

    self.make_requests.side_effect = iter([
        [orig],
        []
    ])

    self.Run("""
        compute routers remove-interface my-router --interface-name my-if
        --region us-central1
        """)

    self.CheckRequests(
        [(self.compute.routers, 'Get',
          self.messages.ComputeRoutersGetRequest(
              router='my-router', region='us-central1', project='my-project'))],
        [(self.compute.routers, 'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],
    )

  def testInterfaceNotFoundError(self):
    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    expected = copy.deepcopy(orig)

    expected.interfaces.pop()

    self.make_requests.side_effect = iter([[orig], []])

    self.make_requests.side_effect = iter([[orig]])
    with self.assertRaises(exceptions.Error):
      self.Run("""
          compute routers remove-interface my-router --interface-name my-if-not
          --region us-central1
          """)


class RemoveInterfaceAlpha(RemoveInterfaceTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testRemoveListOfInterfaces(self):
    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    orig.interfaces.append(
        self.messages.RouterInterface(
            name='my-if-2', linkedVpnTunnel='', ipRange='10.0.1.1/24'))

    expected = copy.deepcopy(orig)
    expected.interfaces.pop()
    expected.interfaces.pop()

    self.make_requests.side_effect = iter([[orig], []])

    self.Run("""
        compute routers remove-interface my-router
        --interface-names my-if,my-if-2 --region us-central1
        """)

    self.CheckRequests(
        [(self.compute.routers,
          'Get',
          self.messages.ComputeRoutersGetRequest(
              router='my-router',
              region='us-central1',
              project='my-project'))],
        [(self.compute.routers,
          'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],
    )

  def testSpecifyBothInterfaceNameAndInterfaceNameList(self):
    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    orig.interfaces.append(
        self.messages.RouterInterface(
            name='my-if-2', linkedVpnTunnel='', ipRange='10.0.1.1/24'))

    expected = copy.deepcopy(orig)
    expected.interfaces.pop()
    expected.interfaces.pop()

    self.make_requests.side_effect = iter([[orig], []])

    with self.AssertRaisesArgumentErrorMatches(
        'argument --interface-name: Exactly one of (--interface-name | '
        '--interface-names) must be specified.'):
      self.Run("""
        compute routers remove-interface my-router
        --interface-names my-if,my-if-2 --interface-name my-if
        --region us-central1
        """)


if __name__ == '__main__':
  test_case.main()
