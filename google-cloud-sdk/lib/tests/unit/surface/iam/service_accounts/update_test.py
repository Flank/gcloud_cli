# -*- coding: utf-8 -*- #
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
class UpdateTest(unit_test_base.BaseTest):

  def _DoUpdateServiceAccount(self,
                              command,
                              service_account,
                              track,
                              run_asserts=True):
    # For other tracks, '-' in {projectsId} is used as wildcard. This
    # would get clean up after the declarative update command promoted to other
    # tracks.
    service_account_name = 'projects/-/serviceAccounts/{}'.format(
        service_account)
    if track == calliope_base.ReleaseTrack.ALPHA:
      service_account_name = 'projects/{0}/serviceAccounts/{1}'.format(
          self.Project(), service_account)

    self.track = track
    self.client.projects_serviceAccounts.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetRequest(
            name=service_account_name),
        response=self.msgs.ServiceAccount(etag=b'etag'))

    self.client.projects_serviceAccounts.Update.Expect(
        request=self.msgs.ServiceAccount(
            name=service_account_name, etag=b'etag', displayName='New Name'),
        response=self.msgs.ServiceAccount(
            email=service_account,
            name=service_account_name,
            projectId='test-project',
            displayName='New Name'))

    self.Run(command)

    if run_asserts:
      self.AssertOutputContains('projectId: test-project')
      self.AssertOutputContains('displayName: New Name')
      self.AssertOutputContains('email: ' + service_account)
      self.AssertOutputContains('name: ' + service_account_name)
      self.AssertErrEquals('Updated serviceAccount [%s].\n' % service_account)

  def testUpdateServiceAccount(self, track):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    command = ('iam service-accounts update --display-name "New Name" '
               + service_account)
    self._DoUpdateServiceAccount(command, service_account, track=track)

  def testUpdateServiceAccountWithServiceAccount(self, track):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    command = ('iam service-accounts update --display-name "New Name" '
               '%s --account test2@test-project.iam.gserviceaccount.com'
               % service_account)
    self._DoUpdateServiceAccount(command, service_account, track=track)

  def testUpdateServiceAccountValidUniqueId(self, track):
    service_account = self.sample_unique_id
    command = ('iam service-accounts update --display-name "New Name" '
               + service_account)
    try:
      self._DoUpdateServiceAccount(
          command, service_account, track=track, run_asserts=False)
    except cli_test_base.MockArgumentError:
      self.fail('update should accept unique ids for service accounts.')

if __name__ == '__main__':
  test_case.main()
