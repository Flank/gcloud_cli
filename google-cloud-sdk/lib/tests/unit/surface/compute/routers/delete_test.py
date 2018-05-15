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
"""Tests for the routers delete subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class RoutersDeleteTest(test_base.BaseTest):

  def testSingle(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute routers delete router-1
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.routers,
          'Delete',
          self.messages.ComputeRoutersDeleteRequest(
              router='router-1',
              project='my-project',
              region='us-central2'))],
    )

  def testWithMany(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute routers delete router-1 router-2 router-3
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.routers,
          'Delete',
          self.messages.ComputeRoutersDeleteRequest(
              router='router-1',
              project='my-project',
              region='us-central2')),

         (self.compute.routers,
          'Delete',
          self.messages.ComputeRoutersDeleteRequest(
              router='router-2',
              project='my-project',
              region='us-central2')),

         (self.compute.routers,
          'Delete',
          self.messages.ComputeRoutersDeleteRequest(
              router='router-3',
              project='my-project',
              region='us-central2'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute routers delete router-1 router-2 router-3
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.routers,
          'Delete',
          self.messages.ComputeRoutersDeleteRequest(
              router='router-1',
              project='my-project',
              region='us-central2')),

         (self.compute.routers,
          'Delete',
          self.messages.ComputeRoutersDeleteRequest(
              router='router-2',
              project='my-project',
              region='us-central2')),

         (self.compute.routers,
          'Delete',
          self.messages.ComputeRoutersDeleteRequest(
              router='router-3',
              project='my-project',
              region='us-central2'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
        compute routers delete router-1 router-2 router-3
            --region us-central2
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
