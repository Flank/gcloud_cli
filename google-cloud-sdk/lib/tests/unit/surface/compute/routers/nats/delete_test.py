# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for the delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import router_test_utils
from tests.lib.surface.compute import test_base


class AlphaDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

    self.orig = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='alpha')
    self.orig.nats = [
        self.messages.RouterNat(name='nat1'),
        self.messages.RouterNat(name='nat2')
    ]
    self.make_requests.side_effect = iter([[self.orig], []])

  def testDeleteOne(self):
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run("""
        compute routers nats delete nat1 --router my-router
        --region us-central1
        """)

    expected = copy.deepcopy(self.orig)
    del expected.nats[0]

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

  def testDeleteMultiple(self):
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run("""
        compute routers nats delete nat1 nat2 --router my-router
        --region us-central1
        """)

    expected = copy.deepcopy(self.orig)
    expected.nats = []

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

  def testNatNotFound(self):
    properties.VALUES.core.disable_prompts.Set(True)

    with self.AssertRaisesExceptionRegexp(nats_utils.NatNotFoundError,
                                          'NAT `invalid-nat` not found'):
      self.Run("""
        compute routers nats delete invalid-nat --router my-router
        --region us-central1
          """)

    self.CheckRequests([(self.compute.routers, 'Get',
                         self.messages.ComputeRoutersGetRequest(
                             router='my-router',
                             region='us-central1',
                             project='my-project'))])

  def testPromptWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
        compute routers nats delete nat1 --router my-router
        --region us-central1
          """)

    self.CheckRequests([(self.compute.routers, 'Get',
                         self.messages.ComputeRoutersGetRequest(
                             router='my-router',
                             region='us-central1',
                             project='my-project'))])


if __name__ == '__main__':
  test_case.main()
