# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the interconnects delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InterconnectsDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.message_version = self.compute_v1

  def testWithSingleInterconnect(self):
    properties.VALUES.core.disable_prompts.Set(True)
    messages = self.messages
    self.Run("""
        compute interconnects delete my-interconnect
        """)

    self.CheckRequests(
        [(self.message_version.interconnects, 'Delete',
          messages.ComputeInterconnectsDeleteRequest(
              project='my-project', interconnect='my-interconnect'))],)

  def testWithManyInterconnects(self):
    properties.VALUES.core.disable_prompts.Set(True)
    messages = self.messages
    self.Run("""
        compute interconnects delete my-interconnect my-interconnect2
        my-interconnect3
        """)

    self.CheckRequests(
        [(self.message_version.interconnects, 'Delete',
          messages.ComputeInterconnectsDeleteRequest(
              project='my-project', interconnect='my-interconnect')),
         (self.message_version.interconnects, 'Delete',
          messages.ComputeInterconnectsDeleteRequest(
              project='my-project', interconnect='my-interconnect2')),
         (self.message_version.interconnects, 'Delete',
          messages.ComputeInterconnectsDeleteRequest(
              project='my-project', interconnect='my-interconnect3'))],)

  def testPromptingWithYes(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.Run("""
        compute interconnects delete my-interconnect1 my-interconnect2
        my-interconnect3
        """)

    self.CheckRequests(
        [(self.message_version.interconnects, 'Delete',
          messages.ComputeInterconnectsDeleteRequest(
              project='my-project', interconnect='my-interconnect1')),
         (self.message_version.interconnects, 'Delete',
          messages.ComputeInterconnectsDeleteRequest(
              project='my-project', interconnect='my-interconnect2')),
         (self.message_version.interconnects, 'Delete',
          messages.ComputeInterconnectsDeleteRequest(
              project='my-project', interconnect='my-interconnect3'))],)
    self.AssertErrContains(
        r'The following interconnects will be deleted:\n'
        r' - [my-interconnect1]\n'
        r' - [my-interconnect2]\n'
        r' - [my-interconnect3]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
            compute interconnects delete my-interconnect1 my-interconnect2
            my-interconnect3
            """)

    self.CheckRequests()

  def testWithUri(self):
    properties.VALUES.core.disable_prompts.Set(True)
    messages = self.messages
    self.Run(
        'compute interconnects delete https://www.googleapis.com/compute/v1/'
        'projects/my-project/global/interconnects/my-interconnect')

    self.CheckRequests(
        [(self.message_version.interconnects, 'Delete',
          messages.ComputeInterconnectsDeleteRequest(
              project='my-project', interconnect='my-interconnect'))],)

  if __name__ == '__main__':
    test_case.main()


class InterconnectsBetaDeleteTest(InterconnectsDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self.message_version = self.compute_beta


class InterconnectsAlphaDeleteTest(InterconnectsDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self.message_version = self.compute_alpha
