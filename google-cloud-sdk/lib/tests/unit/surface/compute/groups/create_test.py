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
"""Tests for the groups create subcommand."""
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GroupsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.batch_url = 'https://www.googleapis.com/batch/'

  def testBasic(self):
    self.Run("""
      compute groups create group1
      """)

    self.CheckRequests(
        [(self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group1',),
          ))],
    )

  def testWithDescription(self):
    self.Run("""
      compute groups create group1 --description 'this is a test'
      """)
    self.CheckRequests(
        [(self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group1',
                  description='this is a test'),
          ))],
    )

  def testMultiple(self):
    self.Run("""
      compute groups create group1 group2 group3 --description 'a few groups'
      """)

    self.CheckRequests(
        [(self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group1',
                  description='a few groups'),
          )),
         (self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group2',
                  description='a few groups'),
          )),
         (self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group3',
                  description='a few groups'),
          ))],
    )

  def testUriSupport(self):
    self.Run("""
        compute groups create
          https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group1
        """.format(api=self.accounts_api))

    self.CheckRequests(
        [(self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group1'),
          ))],
    )

  def testMultipleUriSupport(self):
    self.Run("""
        compute groups create
          https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group1
          https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group2
          https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group3
        """.format(api=self.accounts_api))

    self.CheckRequests(
        [(self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group1'),
          )),
         (self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group2'),
          )),
         (self.accounts.groups,
          'Insert',
          self.accounts_messages.ClouduseraccountsGroupsInsertRequest(
              project='my-project',
              group=self.accounts_messages.Group(
                  name='group3'),
          ))],
    )


if __name__ == '__main__':
  test_case.main()
