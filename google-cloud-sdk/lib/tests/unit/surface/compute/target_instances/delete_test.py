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
"""Tests for the target-instances delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetInstancesDeleteTest(test_base.BaseTest):

  def testWithSingleTargetInstance(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute target-instances delete target-instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.targetInstances,
          'Delete',
          messages.ComputeTargetInstancesDeleteRequest(
              targetInstance='target-instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithManyTargetInstances(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute target-instances delete
          target-instance-1 target-instance-2 target-instance-3
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.targetInstances,
          'Delete',
          messages.ComputeTargetInstancesDeleteRequest(
              targetInstance='target-instance-1',
              project='my-project',
              zone='central2-a')),

         (self.compute_v1.targetInstances,
          'Delete',
          messages.ComputeTargetInstancesDeleteRequest(
              targetInstance='target-instance-2',
              project='my-project',
              zone='central2-a')),

         (self.compute_v1.targetInstances,
          'Delete',
          messages.ComputeTargetInstancesDeleteRequest(
              targetInstance='target-instance-3',
              project='my-project',
              zone='central2-a'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute target-instances delete
          target-instance-1 target-instance-2 target-instance-3
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.targetInstances,
          'Delete',
          messages.ComputeTargetInstancesDeleteRequest(
              targetInstance='target-instance-1',
              project='my-project',
              zone='central2-a')),

         (self.compute_v1.targetInstances,
          'Delete',
          messages.ComputeTargetInstancesDeleteRequest(
              targetInstance='target-instance-2',
              project='my-project',
              zone='central2-a')),

         (self.compute_v1.targetInstances,
          'Delete',
          messages.ComputeTargetInstancesDeleteRequest(
              targetInstance='target-instance-3',
              project='my-project',
              zone='central2-a'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute target-instances delete
            target-instance-1 target-instance-2 target-instance-3
            --zone central2-a
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
