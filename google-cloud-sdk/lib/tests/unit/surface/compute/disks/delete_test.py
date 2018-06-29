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
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class DisksDeleteTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def testWithSingleDisk(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute disks delete disk-1 --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.disks,
          'Delete',
          messages.ComputeDisksDeleteRequest(
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
        [(self.compute_v1.disks,
          'Delete',
          messages.ComputeDisksDeleteRequest(
              disk='disk-1',
              project='my-project',
              zone='central2-a')),

         (self.compute_v1.disks,
          'Delete',
          messages.ComputeDisksDeleteRequest(
              disk='disk-2',
              project='my-project',
              zone='central2-a')),

         (self.compute_v1.disks,
          'Delete',
          messages.ComputeDisksDeleteRequest(
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
        [(self.compute_v1.disks,
          'Delete',
          messages.ComputeDisksDeleteRequest(
              disk='disk-1',
              project='my-project',
              zone='central2-a')),

         (self.compute_v1.disks,
          'Delete',
          messages.ComputeDisksDeleteRequest(
              disk='disk-2',
              project='my-project',
              zone='central2-a')),

         (self.compute_v1.disks,
          'Delete',
          messages.ComputeDisksDeleteRequest(
              disk='disk-3',
              project='my-project',
              zone='central2-a'))],
    )
    # pylint: disable=line-too-long
    self.AssertErrContains(textwrap.dedent("""\
        The following disks will be deleted:
         - [disk-1] in [central2-a]
         - [disk-2] in [central2-a]
         - [disk-3] in [central2-a]


        Do you want to continue (Y/n)? """))

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute disks delete disk-1 disk-2 disk-3 --zone central2-a
          """)

    self.CheckRequests()

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.DISKS)
    self.RunCompletion('compute disks delete --zone zone-1 d',
                       ['disk-1', 'disk-2', 'disk-3'])


@parameterized.parameters((base.ReleaseTrack.ALPHA, 'alpha'),
                          (base.ReleaseTrack.BETA, 'beta'))
class RegionalDisksDeleteTest(test_base.BaseTest, parameterized.TestCase):

  def testDefaultOptionsWithSingleDisk(self, track, api_version):
    self.SelectApi(api_version)
    self.track = track

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


if __name__ == '__main__':
  test_case.main()
