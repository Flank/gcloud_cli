# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the remove-profile subcommand."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.oslogin import test_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA),
)
class RemoveProfileTest(test_base.OsloginBaseTest):

  def _RunSetUp(self, track):
    self.track = track
    self.SetUpMockApis(self.track)
    self.profiles = self.GetProfiles(self.messages)

  def testSimpleCaseWithAccountId(self, track):
    self._RunSetUp(track)
    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_account_id'])

    self.mock_oslogin_client.users_projects.Delete.Expect(
        request=self.messages.OsloginUsersProjectsDeleteRequest(
            name='users/user@google.com/projects/fake-project'),
        response={})

    self.Run("""
        compute os-login remove-profile
        """)

    self.AssertErrContains('Deleted [fake-project] posix account(s)')

  def testSimpleCaseWithoutAccountId(self, track):
    self._RunSetUp(track)
    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_without_account_id'])

    self.Run("""
        compute os-login remove-profile
        """)

    self.AssertErrContains('No profile found with accountId [fake-project]')

  def testSimpleCaseWithUnsetProject(self, track):
    self._RunSetUp(track)
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)

    with self.assertRaises(properties.RequiredPropertyError):
      self.Run("""
          compute os-login remove-profile
          """)

      self.AssertErrContains(
          'The required property [project] is not currently set.')


if __name__ == '__main__':
  test_case.main()
