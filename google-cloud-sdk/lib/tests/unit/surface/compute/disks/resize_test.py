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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  if api_version == 'v1':
    test_obj._instances = test_resources.INSTANCES_V1
  elif api_version == 'alpha':
    test_obj._instances = test_resources.INSTANCES_ALPHA
  elif api_version == 'beta':
    test_obj._instances = test_resources.INSTANCES_BETA
  else:
    raise ValueError('api_version must be \'v1\', \'alpha\', or \'beta\'.'
                     'Got [{0}].'.format(api_version))


def TestWithDefaults(test_obj, compute_interface):
  test_obj.make_requests.side_effect = iter([
      []
  ])
  msg = test_obj.messages
  properties.VALUES.core.disable_prompts.Set(True)

  test_obj.Run('compute disks resize disk1 --zone us-central1-a --size=6000GB')

  test_obj.CheckRequests(
      ([(compute_interface.disks,
         'Resize',
         msg.ComputeDisksResizeRequest(
             disk='disk1',
             disksResizeRequest=msg.DisksResizeRequest(
                 sizeGb=6000
             ),
             project='my-project',
             zone='us-central1-a'))
       ]))


def TestWithYes(test_obj, compute_interface):
  test_obj.make_requests.side_effect = iter([
      []
  ])
  msg = test_obj.messages
  test_obj.WriteInput('y\n')

  test_obj.Run('compute disks resize disk2 --zone us-central1-b --size=6000GB')

  test_obj.CheckRequests(
      ([(compute_interface.disks,
         'Resize',
         msg.ComputeDisksResizeRequest(
             disk='disk2',
             disksResizeRequest=msg.DisksResizeRequest(
                 sizeGb=6000
             ),
             project='my-project',
             zone='us-central1-b'))
       ]))


def TestWithNo(test_obj):
  test_obj.make_requests.side_effect = iter([
      []
  ])
  test_obj.WriteInput('n\n')

  with test_obj.assertRaises(console_io.OperationCancelledError):
    test_obj.Run(
        'compute disks resize disk3 --zone us-central1-c --size=6000GB')
  test_obj.CheckRequests()


class DisksResizeTestAlpha(test_base.BaseTest):

  def SetUp(self):
    self.version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA
    SetUp(self, self.version)

  def testWithDefaults(self):
    TestWithDefaults(self, self.compute_alpha)

  def testWithYes(self):
    TestWithYes(self, self.compute_alpha)

  def testWithNo(self):
    TestWithNo(self)

  def testRegionalDisks(self):
    self.make_requests.side_effect = iter([
        []
    ])
    msg = self.messages
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run('compute disks resize disk1 --region us-central1 --size=6000GB')

    self.CheckRequests(
        ([(self.compute_alpha.regionDisks,
           'Resize',
           msg.ComputeRegionDisksResizeRequest(
               disk='disk1',
               regionDisksResizeRequest=msg.RegionDisksResizeRequest(
                   sizeGb=6000
               ),
               project='my-project',
               region='us-central1'))
         ]))


class DisksResizeTestBeta(test_base.BaseTest):

  def SetUp(self):
    self.version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA
    SetUp(self, self.version)

  def testWithDefaults(self):
    TestWithDefaults(self, self.compute_beta)

  def testWithYes(self):
    TestWithYes(self, self.compute_beta)

  def testWithNo(self):
    TestWithNo(self)


class DisksResizeTestGA(test_base.BaseTest):

  def SetUp(self):
    self.version = 'v1'
    SetUp(self, self.version)

  def testWithDefaults(self):
    TestWithDefaults(self, self.compute_v1)

  def testWithYes(self):
    TestWithYes(self, self.compute_v1)

  def testWithNo(self):
    TestWithNo(self)


if __name__ == '__main__':
  test_case.main()
