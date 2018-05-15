# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the sole-tenancy hosts delete subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HostsDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testWithSingleHost(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run('compute sole-tenancy hosts delete host-1 --zone central2-a')

    self.CheckRequests(
        [(self.compute_alpha.hosts,
          'Delete',
          self.messages.ComputeHostsDeleteRequest(
              host='host-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithManyHosts(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute sole-tenancy hosts delete host-1 host-2 host-3 --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_alpha.hosts,
          'Delete',
          self.messages.ComputeHostsDeleteRequest(
              host='host-1',
              project='my-project',
              zone='central2-a')),

         (self.compute_alpha.hosts,
          'Delete',
          self.messages.ComputeHostsDeleteRequest(
              host='host-2',
              project='my-project',
              zone='central2-a')),

         (self.compute_alpha.hosts,
          'Delete',
          self.messages.ComputeHostsDeleteRequest(
              host='host-3',
              project='my-project',
              zone='central2-a'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute sole-tenancy hosts delete host-1 host-2 host-3 --zone central2-a
        """)
    self.CheckRequests(
        [(self.compute_alpha.hosts,
          'Delete',
          self.messages.ComputeHostsDeleteRequest(
              host='host-1',
              project='my-project',
              zone='central2-a')),

         (self.compute_alpha.hosts,
          'Delete',
          self.messages.ComputeHostsDeleteRequest(
              host='host-2',
              project='my-project',
              zone='central2-a')),

         (self.compute_alpha.hosts,
          'Delete',
          self.messages.ComputeHostsDeleteRequest(
              host='host-3',
              project='my-project',
              zone='central2-a'))],
    )
    # pylint: disable=line-too-long
    self.AssertErrContains(textwrap.dedent("""\
        The following hosts will be deleted. Deleting a host is irreversible and any data on the host will be lost.
         - [host-1] in [central2-a]
         - [host-2] in [central2-a]
         - [host-3] in [central2-a]


        Do you want to continue (Y/n)? """))

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute sole-tenancy hosts delete host-1 host-2 host-3 --zone central2-a
          """)

    self.CheckRequests()

if __name__ == '__main__':
  test_case.main()
