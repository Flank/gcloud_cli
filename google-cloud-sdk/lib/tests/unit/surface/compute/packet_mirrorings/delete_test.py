# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the packet mirrorings delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class DeleteTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.compute = self.compute_v1

  def testSingle(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute packet-mirrorings delete pm-1 --region us-central1
        """)

    self.CheckRequests([(self.compute.packetMirrorings, 'Delete',
                         self.messages.ComputePacketMirroringsDeleteRequest(
                             packetMirroring='pm-1',
                             project='my-project',
                             region='us-central1'))])

  def testMultiple(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute packet-mirrorings delete pm-1 pm-2 pm-3 --region us-central1
        """)

    self.CheckRequests([(self.compute.packetMirrorings, 'Delete',
                         self.messages.ComputePacketMirroringsDeleteRequest(
                             packetMirroring='pm-1',
                             project='my-project',
                             region='us-central1')),
                        (self.compute.packetMirrorings, 'Delete',
                         self.messages.ComputePacketMirroringsDeleteRequest(
                             packetMirroring='pm-2',
                             project='my-project',
                             region='us-central1')),
                        (self.compute.packetMirrorings, 'Delete',
                         self.messages.ComputePacketMirroringsDeleteRequest(
                             packetMirroring='pm-3',
                             project='my-project',
                             region='us-central1'))])

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute packet-mirrorings delete pm-1 --region us-central1
          """)
    self.CheckRequests()

  def testPromptingWithYes(self):
    self.WriteInput('y\n')

    self.Run("""
        compute packet-mirrorings delete pm-1 --region us-central1
        """)

    self.CheckRequests([(self.compute.packetMirrorings, 'Delete',
                         self.messages.ComputePacketMirroringsDeleteRequest(
                             packetMirroring='pm-1',
                             project='my-project',
                             region='us-central1'))])


class DeleteTestBeta(DeleteTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.compute = self.compute_beta


class DeleteTestAlpha(DeleteTestBeta):

  def SetUp(self):
    self.SelectApi('alpha')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.compute = self.compute_alpha


if __name__ == '__main__':
  test_case.main()
