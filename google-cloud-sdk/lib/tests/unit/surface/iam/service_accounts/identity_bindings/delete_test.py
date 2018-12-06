# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for `iam service-accounts identity-bindings describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class DeleteTest(unit_test_base.BaseTest):

  def _SetUpDeleteIdentityBindingExpectations(self, service_account,
                                              identity_binding):
    self.client.projects_serviceAccounts_identityBindings.Delete.Expect(
        request=self.msgs
        .IamProjectsServiceAccountsIdentityBindingsDeleteRequest(
            name=('projects/-/serviceAccounts/{0}/identityBindings/{1}'.format(
                service_account, identity_binding))),
        response=self.msgs.Empty())

  def testDeleteIdentityBinding(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    identity_binding = 'd34db33fd34db33fd34db33fd34db33f'
    self._SetUpDeleteIdentityBindingExpectations(service_account,
                                                 identity_binding)

    self.Run('alpha iam service-accounts identity-bindings delete '
             '{identity_binding} '
             '--service-account {service_account}'.format(
                 identity_binding=identity_binding,
                 service_account=service_account))

    self.AssertErrContains(
        'You are about to delete identity binding [{0}] on service account '
        '[{1}]'.format(identity_binding, service_account))

    self.AssertErrContains(
        ('Deleted identity binding [{0}] on service account [{1}]').format(
            identity_binding, service_account))


if __name__ == '__main__':
  test_case.main()
