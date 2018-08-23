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
"""Tests for the instance-templates delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class InstanceTemplatesDeleteTest(test_base.BaseTest):

  def testWithSingleInstanceTemplate(self):
    self.Run("""
        compute instance-templates delete template-1 --quiet
        """)

    self.CheckRequests(
        [(self.compute_v1.instanceTemplates,
          'Delete',
          messages.ComputeInstanceTemplatesDeleteRequest(
              instanceTemplate='template-1',
              project='my-project'))],
    )

  def testWithManyTemplates(self):
    self.Run("""
        compute instance-templates delete template-1 template-2 template-3
             --quiet
        """)

    self.CheckRequests(
        [(self.compute_v1.instanceTemplates,
          'Delete',
          messages.ComputeInstanceTemplatesDeleteRequest(
              instanceTemplate='template-1',
              project='my-project')),

         (self.compute_v1.instanceTemplates,
          'Delete',
          messages.ComputeInstanceTemplatesDeleteRequest(
              instanceTemplate='template-2',
              project='my-project')),

         (self.compute_v1.instanceTemplates,
          'Delete',
          messages.ComputeInstanceTemplatesDeleteRequest(
              instanceTemplate='template-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute instance-templates delete template-1 template-2 template-3
             --quiet
        """)

    self.CheckRequests(
        [(self.compute_v1.instanceTemplates,
          'Delete',
          messages.ComputeInstanceTemplatesDeleteRequest(
              instanceTemplate='template-1',
              project='my-project')),

         (self.compute_v1.instanceTemplates,
          'Delete',
          messages.ComputeInstanceTemplatesDeleteRequest(
              instanceTemplate='template-2',
              project='my-project')),

         (self.compute_v1.instanceTemplates,
          'Delete',
          messages.ComputeInstanceTemplatesDeleteRequest(
              instanceTemplate='template-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute instance-templates delete template-1 template-2 template-3
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
