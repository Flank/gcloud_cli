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
"""Tests for the groups add-members subcommand."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GroupsAddMembersTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.batch_url = 'https://www.googleapis.com/batch/'

  def UserToSelfLink(self, user):
    return ('https://www.googleapis.com/clouduseraccounts/{api}/'
            'projects/my-project/global/users/{user}'
            .format(api=self.accounts_api, user=user))

  def GroupAddMembersMessage(self, group, users):
    return (self.accounts.groups,
            'AddMember',
            self.accounts_messages.ClouduseraccountsGroupsAddMemberRequest(
                project='my-project',
                groupName=group,
                groupsAddMemberRequest=(
                    self.accounts_messages.GroupsAddMemberRequest(
                        users=[self.UserToSelfLink(user) for user in users]))))

  def testBasic(self):
    self.Run("""
      compute groups add-members group1 --members user1
      """)

    self.CheckRequests(
        [self.GroupAddMembersMessage('group1', ['user1'])])

  def testMultipleUsersMultipleGroups(self):
    self.Run("""
      compute groups add-members group1 group2 group3
       --members user1,user2,user3
      """)

    self.CheckRequests(
        [self.GroupAddMembersMessage('group1', ['user1', 'user2', 'user3']),
         self.GroupAddMembersMessage('group2', ['user1', 'user2', 'user3']),
         self.GroupAddMembersMessage('group3', ['user1', 'user2', 'user3'])])

  def testUriBasic(self):
    self.Run("""
      compute groups add-members
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group1
        --members https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/users/user1
      """.format(api=self.accounts_api))

    self.CheckRequests(
        [self.GroupAddMembersMessage('group1', ['user1'])])

  def testUriAndUserBasic(self):
    self.Run("""
      compute groups add-members
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group1
        --members https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/users/user1,user2
      """.format(api=self.accounts_api))

    self.CheckRequests(
        [self.GroupAddMembersMessage('group1', ['user1', 'user2'])])

  def testUriMultipleUsersMultipleGroups(self):
    self.Run("""
      compute groups add-members
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group1
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group2
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group3
        --members
        https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/users/user1,https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/users/user2,https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/users/user3
      """.format(api=self.accounts_api))

    self.CheckRequests(
        [self.GroupAddMembersMessage('group1', ['user1', 'user2', 'user3']),
         self.GroupAddMembersMessage('group2', ['user1', 'user2', 'user3']),
         self.GroupAddMembersMessage('group3', ['user1', 'user2', 'user3'])])

  def testLegacyProjectName(self):
    self.Run("""
      compute groups add-members group1
          --members user1
          --project google.com:my-legacy-project
      """)

    self.CheckRequests([
        (self.accounts.groups,
         'AddMember',
         self.accounts_messages.ClouduseraccountsGroupsAddMemberRequest(
             project='google.com:my-legacy-project',
             groupName='group1',
             groupsAddMemberRequest=(
                 self.accounts_messages.GroupsAddMemberRequest(
                     users=[('https://www.googleapis.com/clouduseraccounts/'
                             '{api}/projects/google.com:my-legacy-project/'
                             'global/users/user1'.format(
                                 api=self.accounts_api))]))))])


if __name__ == '__main__':
  test_case.main()
