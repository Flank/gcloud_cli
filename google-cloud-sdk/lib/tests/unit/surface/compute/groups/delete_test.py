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
"""Tests for the groups delete subcommand."""
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GroupsDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.batch_url = 'https://www.googleapis.com/batch/'

  def testBasic(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
      compute groups delete group1
      """)

    self.CheckRequests(
        [(self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group1'))]
    )

  def testManyGroups(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
      compute groups delete group1 group2 group3
      """)

    self.CheckRequests(
        [(self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group1')),
         (self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group2')),
         (self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group3'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
      compute groups delete group1 group2 group3
      """)

    self.CheckRequests(
        [(self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group1')),
         (self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group2')),
         (self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group3'))],
    )

    self.AssertErrContains(textwrap.dedent("""\
        The following groups will be deleted:
         - [group1]
         - [group2]
         - [group3]


        Do you want to continue (Y/n)? """))

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
        compute groups delete group1 group2 group3
        """)

  def testManyUriGroups(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
      compute groups delete
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group1
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group2
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group3
      """.format(api=self.accounts_api))

    self.CheckRequests(
        [(self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group1')),
         (self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group2')),
         (self.accounts.groups,
          'Delete',
          self.accounts_messages.ClouduseraccountsGroupsDeleteRequest(
              project='my-project',
              groupName='group3'))],
    )


if __name__ == '__main__':
  test_case.main()
