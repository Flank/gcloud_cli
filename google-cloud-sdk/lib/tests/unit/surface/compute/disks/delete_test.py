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
"""Tests for the disks delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class DisksDeleteTestGA(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.SelectApi(self.api_version)
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)

  def testWithSingleDisk(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute disks delete disk-1 --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.disks,
          'Delete',
          self.messages.ComputeDisksDeleteRequest(
              disk='disk-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithManyDisks(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute disks delete disk-1 disk-2 disk-3 --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.disks,
          'Delete',
          self.messages.ComputeDisksDeleteRequest(
              disk='disk-1',
              project='my-project',
              zone='central2-a')),

         (self.compute.disks,
          'Delete',
          self.messages.ComputeDisksDeleteRequest(
              disk='disk-2',
              project='my-project',
              zone='central2-a')),

         (self.compute.disks,
          'Delete',
          self.messages.ComputeDisksDeleteRequest(
              disk='disk-3',
              project='my-project',
              zone='central2-a'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute disks delete disk-1 disk-2 disk-3 --zone central2-a
        """)
    self.CheckRequests(
        [(self.compute.disks,
          'Delete',
          self.messages.ComputeDisksDeleteRequest(
              disk='disk-1',
              project='my-project',
              zone='central2-a')),

         (self.compute.disks,
          'Delete',
          self.messages.ComputeDisksDeleteRequest(
              disk='disk-2',
              project='my-project',
              zone='central2-a')),

         (self.compute.disks,
          'Delete',
          self.messages.ComputeDisksDeleteRequest(
              disk='disk-3',
              project='my-project',
              zone='central2-a'))],
    )
    # pylint: disable=line-too-long
    self.AssertErrContains(
        r'The following disks will be deleted:\n'
        r' - [disk-1] in [central2-a]\n'
        r' - [disk-2] in [central2-a]\n'
        r' - [disk-3] in [central2-a]\n')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute disks delete disk-1 disk-2 disk-3 --zone central2-a
          """)

    self.CheckRequests()

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.MultiScopeLister',
        autospec=True)
    lister_mock.return_value.return_value = resource_projector.MakeSerializable(
        test_resources.DISKS)
    self.RunCompletion('compute disks delete --zone zone-1 d',
                       ['disk-1', 'disk-2', 'disk-3'])

  def testDefaultOptionsWithSingleDisk(self):
    self.Run("""
        compute disks delete disk-1 --region central2
        """)

    self.CheckRequests(
        [(self.compute.regionDisks,
          'Delete',
          self.messages.ComputeRegionDisksDeleteRequest(
              disk='disk-1',
              project='my-project',
              region='central2'))],
    )


class DisksDeleteTestBeta(DisksDeleteTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class DisksDeleteTestAlpha(DisksDeleteTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
