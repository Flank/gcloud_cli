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
"""Tests for the networks delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.networks import test_resources


class NetworksDeleteTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def testWithSingleNetwork(self):
    self.Run("""
        compute networks delete network-1 --quiet
        """)

    self.CheckRequests(
        [(self.compute.networks,
          'Delete',
          self.messages.ComputeNetworksDeleteRequest(
              network='network-1',
              project='my-project'))],
    )

  def testWithManyNetworks(self):
    self.Run("""
        compute networks delete network-1 network-2 network-3 --quiet
        """)

    self.CheckRequests(
        [(self.compute.networks,
          'Delete',
          self.messages.ComputeNetworksDeleteRequest(
              network='network-1',
              project='my-project')),

         (self.compute.networks,
          'Delete',
          self.messages.ComputeNetworksDeleteRequest(
              network='network-2',
              project='my-project')),

         (self.compute.networks,
          'Delete',
          self.messages.ComputeNetworksDeleteRequest(
              network='network-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute networks delete network-1 network-2 network-3
        """)

    self.CheckRequests(
        [(self.compute.networks,
          'Delete',
          self.messages.ComputeNetworksDeleteRequest(
              network='network-1',
              project='my-project')),

         (self.compute.networks,
          'Delete',
          self.messages.ComputeNetworksDeleteRequest(
              network='network-2',
              project='my-project')),

         (self.compute.networks,
          'Delete',
          self.messages.ComputeNetworksDeleteRequest(
              network='network-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute networks delete network-1 network-2 network-3
          """)

    self.CheckRequests()

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.NETWORKS_V1)
    self.RunCompletion(
        'compute networks delete n',
        [
            'network-2',
            'network-1',
            'network-3',
        ])


if __name__ == '__main__':
  test_case.main()
