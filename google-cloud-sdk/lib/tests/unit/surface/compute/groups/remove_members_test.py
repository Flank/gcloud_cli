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
"""Tests for the groups remove-members subcommand."""
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GroupsRemoveMembersTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.batch_url = 'https://www.googleapis.com/batch/'

  def UserToSelfLink(self, user):
    return ('https://www.googleapis.com/clouduseraccounts/{api}/'
            'projects/my-project/global/users/{user}'
            .format(api=self.accounts_api, user=user))

  def GroupRemoveMembersMessage(self, group, user):
    return (self.accounts.groups,
            'RemoveMember',
            self.accounts_messages.
            ClouduseraccountsGroupsRemoveMemberRequest(
                project='my-project',
                groupName=group,
                groupsRemoveMemberRequest=(
                    self.accounts_messages.GroupsRemoveMemberRequest(
                        users=[self.UserToSelfLink(user)]))))

  def testBasic(self):
    self.Run("""
      compute groups remove-members group1 --members user1
      """)

    self.CheckRequests(
        [self.GroupRemoveMembersMessage('group1', 'user1')])

  def testMultipleUsersMulipleGroups(self):
    self.Run("""
      compute groups remove-members group1 group2 group3
       --members user1,user2,user3
      """)

    self.CheckRequests(
        [self.GroupRemoveMembersMessage('group1', 'user1'),
         self.GroupRemoveMembersMessage('group1', 'user2'),
         self.GroupRemoveMembersMessage('group1', 'user3'),
         self.GroupRemoveMembersMessage('group2', 'user1'),
         self.GroupRemoveMembersMessage('group2', 'user2'),
         self.GroupRemoveMembersMessage('group2', 'user3'),
         self.GroupRemoveMembersMessage('group3', 'user1'),
         self.GroupRemoveMembersMessage('group3', 'user2'),
         self.GroupRemoveMembersMessage('group3', 'user3')],
    )

  def testUriBasic(self):
    self.Run("""
      compute groups remove-members
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group1
        --members https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/users/user1
      """.format(api=self.accounts_api))

    self.CheckRequests(
        [self.GroupRemoveMembersMessage('group1', 'user1')])

  def testLegacyProjectName(self):
    self.Run("""
      compute groups remove-members group1
          --members user1
          --project google.com:my-legacy-project
      """)

    self.CheckRequests([
        (self.accounts.groups,
         'RemoveMember',
         self.accounts_messages.ClouduseraccountsGroupsRemoveMemberRequest(
             project='google.com:my-legacy-project',
             groupName='group1',
             groupsRemoveMemberRequest=(
                 self.accounts_messages.GroupsRemoveMemberRequest(
                     users=[('https://www.googleapis.com/clouduseraccounts/'
                             '{api}/projects/google.com:my-legacy-project/'
                             'global/users/user1'.format(
                                 api=self.accounts_api))]))))])


if __name__ == '__main__':
  test_case.main()
