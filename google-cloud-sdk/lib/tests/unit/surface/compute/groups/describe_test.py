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
"""Tests for the groups describe subcommand."""
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class GroupsDescribeTest(test_base.BaseTest):

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [test_resources.GROUPS[0]],
    ])
    self.track = calliope_base.ReleaseTrack.BETA
    self.batch_url = 'https://www.googleapis.com/batch/'

  def testSimpleCase(self):
    self.Run("""
        compute groups describe group1
        """)

    self.CheckRequests(
        [(self.accounts.groups,
          'Get',
          self.accounts_messages.ClouduseraccountsGroupsGetRequest(
              project='my-project',
              groupName='group1'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
          ---
          creationTimestamp: '2015-03-10T13:05:29.819-07:00'
          id: '5296074615390662758'
          kind: clouduseraccounts#group
          members:
          - https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/users/u1
          name: group1
          """.format(api=self.accounts_api)))

  def testUri(self):
    self.Run("""
        compute groups describe https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/groups/group1
        """.format(api=self.accounts_api))

    self.CheckRequests(
        [(self.accounts.groups,
          'Get',
          self.accounts_messages.ClouduseraccountsGroupsGetRequest(
              project='my-project',
              groupName='group1'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
          ---
          creationTimestamp: '2015-03-10T13:05:29.819-07:00'
          id: '5296074615390662758'
          kind: clouduseraccounts#group
          members:
          - https://www.googleapis.com/clouduseraccounts/{api}/projects/my-project/global/users/u1
          name: group1
          """.format(api=self.accounts_api)))


if __name__ == '__main__':
  test_case.main()
