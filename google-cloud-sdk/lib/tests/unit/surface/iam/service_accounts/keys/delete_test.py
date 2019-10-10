# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tests that ensure deserialization of server responses work properly."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class DeleteTest(unit_test_base.BaseTest):

  def testDeleteServiceAccountKey(self, track):
    self.track = track
    self.client.projects_serviceAccounts_keys.Delete.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysDeleteRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'
                  '/keys/deadbeefdeafbeef')),
        response=self.msgs.Empty())

    self.Run('iam service-accounts keys delete '
             '--iam-account test@test-project.iam.gserviceaccount.com '
             'deadbeefdeafbeef')

    self.AssertErrContains(
        'You are about to delete key [deadbeefdeafbeef] for service account '
        '[test@test-project.iam.gserviceaccount.com]'
    )

    self.AssertErrContains('deleted key [deadbeefdeafbeef] for service account '
                           '[test@test-project.iam.gserviceaccount.com]')
    self.AssertErrNotContains(
        'Not found: key [deadbeefdeafbeef] for service account '
        '[test@test-project.iam.gserviceaccount.com]')

  def testDeleteServiceAccountKeyWithName(self, track):
    self.track = track
    key_name = ('projects/-/serviceAccounts/'
                'test@test-project.iam.gserviceaccount.com'
                '/keys/deadbeefdeafbeef')
    self.client.projects_serviceAccounts_keys.Delete.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysDeleteRequest(
            name=key_name),
        response=self.msgs.Empty())

    self.Run('iam service-accounts keys delete '
             '--iam-account test@test-project.iam.gserviceaccount.com '
             '%s' % key_name)

    self.AssertErrContains(
        'You are about to delete key [{}] for service account '
        '[test@test-project.iam.gserviceaccount.com]'.format(key_name))

    self.AssertErrContains('deleted key [deadbeefdeafbeef] for service account '
                           '[test@test-project.iam.gserviceaccount.com]')
    self.AssertErrNotContains(
        'Not found: key [deadbeefdeafbeef] for service account '
        '[test@test-project.iam.gserviceaccount.com]')

  def testDeleteServiceAccountKeyInvalidAccount(self, track):
    self.track = track
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'Not a valid service account identifier. It should be either a '
        r'numeric string representing the unique_id or an email of the form: '
        r'my-iam-account@somedomain.com or '
        r'my-iam-account@PROJECT_ID.iam.gserviceaccount.com'):
      self.Run('iam service-accounts keys delete --iam-account testfoo '
               'deadbeefdeafbeef')

  def testDeleteServiceAccountKeyValidUniqueId(self, track):
    self.track = track
    self.client.projects_serviceAccounts_keys.Delete.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysDeleteRequest(
            name=('projects/-/serviceAccounts/%s/keys/deadbeefdeafbeef' %
                  self.sample_unique_id)),
        response=self.msgs.Empty())

    try:
      self.Run('iam service-accounts keys delete --iam-account %s '
               'deadbeefdeafbeef' % self.sample_unique_id)
    except cli_test_base.MockArgumentError:
      self.fail('delete should accept unique ids for service accounts.')

if __name__ == '__main__':
  test_case.main()
