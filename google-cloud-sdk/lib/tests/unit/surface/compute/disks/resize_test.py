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
"""Tests for the disks resize subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class DisksResizeTestGA(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.SelectApi(self.api_version)

    if self.api_version == 'v1':
      self._instances = test_resources.INSTANCES_V1
    elif self.api_version == 'alpha':
      self._instances = test_resources.INSTANCES_ALPHA
    elif self.api_version == 'beta':
      self._instances = test_resources.INSTANCES_BETA
    else:
      raise ValueError('api_version must be \'v1\', \'alpha\', or \'beta\'.'
                       'Got [{0}].'.format(self.api_version))

  def testWithDefaults(self):
    self.make_requests.side_effect = iter([
        []
    ])
    msg = self.messages
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run('compute disks resize disk1 --zone us-central1-a --size=6000GB')

    self.CheckRequests(
        ([(self.compute.disks,
           'Resize',
           msg.ComputeDisksResizeRequest(
               disk='disk1',
               disksResizeRequest=msg.DisksResizeRequest(
                   sizeGb=6000
               ),
               project='my-project',
               zone='us-central1-a'))
         ]))

  def testWithYes(self):
    self.make_requests.side_effect = iter([
        []
    ])
    msg = self.messages
    self.WriteInput('y\n')

    self.Run('compute disks resize disk2 --zone us-central1-b --size=6000GB')

    self.CheckRequests(
        ([(self.compute.disks,
           'Resize',
           msg.ComputeDisksResizeRequest(
               disk='disk2',
               disksResizeRequest=msg.DisksResizeRequest(
                   sizeGb=6000
               ),
               project='my-project',
               zone='us-central1-b'))
         ]))

  def testWithNo(self):
    self.make_requests.side_effect = iter([
        []
    ])
    self.WriteInput('n\n')

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(
          'compute disks resize disk3 --zone us-central1-c --size=6000GB')
    self.CheckRequests()

  def testRegionalDisks(self):
    self.make_requests.side_effect = iter([
        []
    ])
    msg = self.messages
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run('compute disks resize disk1 --region us-central1 --size=6000GB')

    self.CheckRequests(
        ([(self.compute.regionDisks,
           'Resize',
           msg.ComputeRegionDisksResizeRequest(
               disk='disk1',
               regionDisksResizeRequest=msg.RegionDisksResizeRequest(
                   sizeGb=6000
               ),
               project='my-project',
               region='us-central1'))
         ]))


class DisksResizeTestBeta(DisksResizeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class DisksResizeTestAlpha(DisksResizeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
