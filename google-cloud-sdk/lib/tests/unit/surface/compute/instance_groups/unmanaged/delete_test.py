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
"""Tests for the instance-groups unmanaged delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base

API_VERSION = 'v1'


class UnmanagedInstanceGroupsDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
    ])

  def testDefaultOptions(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute instance-groups unmanaged delete group-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Delete',
          self.messages.ComputeInstanceGroupsDeleteRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute instance-groups unmanaged delete group-1 group-2 group-3
          --zone central2-a
        """)
    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Delete',
          self.messages.ComputeInstanceGroupsDeleteRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a')),
         (self.compute.instanceGroups,
          'Delete',
          self.messages.ComputeInstanceGroupsDeleteRequest(
              instanceGroup='group-2',
              project='my-project',
              zone='central2-a')),
         (self.compute.instanceGroups,
          'Delete',
          self.messages.ComputeInstanceGroupsDeleteRequest(
              instanceGroup='group-3',
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertErrContains(
        r'The following instance groups will be deleted:\n'
        r' - [group-1] in [central2-a]\n'
        r' - [group-2] in [central2-a]\n'
        r' - [group-3] in [central2-a]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute instance-groups unmanaged delete group-1
            --zone central2-a
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
