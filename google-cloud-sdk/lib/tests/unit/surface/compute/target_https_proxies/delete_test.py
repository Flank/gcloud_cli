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
"""Tests for the target-https-proxies delete subcommand."""

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetHttpsProxiesDeleteTest(test_base.BaseTest):

  def testWithSingleTargetHttpsProxy(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute target-https-proxies delete proxy-1
        """)

    self.CheckRequests(
        [(self.compute.targetHttpsProxies,
          'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-1',
              project='my-project'))],
    )

  def testWithManyTargetHttpsProxies(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute target-https-proxies delete proxy-1 proxy-2 proxy-3
        """)

    self.CheckRequests(
        [(self.compute.targetHttpsProxies,
          'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-1',
              project='my-project')),

         (self.compute.targetHttpsProxies,
          'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-2',
              project='my-project')),

         (self.compute.targetHttpsProxies,
          'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.Run("""
        compute target-https-proxies delete proxy-1 proxy-2 proxy-3
        """)

    self.CheckRequests(
        [(self.compute.targetHttpsProxies,
          'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-1',
              project='my-project')),

         (self.compute.targetHttpsProxies,
          'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-2',
              project='my-project')),

         (self.compute.targetHttpsProxies,
          'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute target-https-proxies delete proxy-1 proxy-2 proxy-3
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
