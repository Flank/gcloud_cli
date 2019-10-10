# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the machine-images delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class MachineImagesDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testWithSingleMachineImage(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run('compute machine-images delete machine-image-1')

    self.CheckRequests(
        [(self.compute_alpha.machineImages,
          'Delete',
          self.messages.ComputeMachineImagesDeleteRequest(
              machineImage='machine-image-1',
              project='my-project'))],
    )

  def testWithManyMachineImages(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run('compute machine-images delete machine-image-1 machine-image-2 '
             'machine-image-3')

    self.CheckRequests(
        [(self.compute_alpha.machineImages,
          'Delete',
          self.messages.ComputeMachineImagesDeleteRequest(
              machineImage='machine-image-1',
              project='my-project')),

         (self.compute_alpha.machineImages,
          'Delete',
          self.messages.ComputeMachineImagesDeleteRequest(
              machineImage='machine-image-2',
              project='my-project')),

         (self.compute_alpha.machineImages,
          'Delete',
          self.messages.ComputeMachineImagesDeleteRequest(
              machineImage='machine-image-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run('compute machine-images delete machine-image-1 machine-image-2'
             ' machine-image-3')
    self.CheckRequests(
        [(self.compute_alpha.machineImages,
          'Delete',
          self.messages.ComputeMachineImagesDeleteRequest(
              machineImage='machine-image-1',
              project='my-project')),

         (self.compute_alpha.machineImages,
          'Delete',
          self.messages.ComputeMachineImagesDeleteRequest(
              machineImage='machine-image-2',
              project='my-project')),

         (self.compute_alpha.machineImages,
          'Delete',
          self.messages.ComputeMachineImagesDeleteRequest(
              machineImage='machine-image-3',
              project='my-project'))],
    )
    self.AssertErrContains(
        r'The following machine images will be deleted:\n'
        r' - [machine-image-1]\n'
        r' - [machine-image-2]\n'
        r' - [machine-image-3]\n')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run('compute machine-images delete machine-image-1 machine-image-2 '
               'machine-image-3')

    self.CheckRequests()

if __name__ == '__main__':
  test_case.main()
