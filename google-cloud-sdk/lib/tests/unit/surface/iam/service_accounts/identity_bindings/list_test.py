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
"""Tests for `iam service-accounts identity-bindings list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class ListTest(unit_test_base.BaseTest):

  def _SetUpListIdentityBindingExpectations(self, service_account):
    self.client.projects_serviceAccounts_identityBindings.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsIdentityBindingsListRequest(
            name=('projects/-/serviceAccounts/{0}'.format(service_account))),
        response=self.msgs
        .ListServiceAccountIdentityBindingsResponse(identityBinding=[
            self.msgs.ServiceAccountIdentityBinding(
                acceptanceFilter='true',
                cel=None,
                name=
                ('projects/test-project/serviceAccounts/{0}/identityBindings/1'
                 .format(service_account)),
                oidc=self.msgs.IDPReferenceOIDC(
                    audience='1234567890',
                    maxTokenLifetimeSeconds=3600,
                    url='https://www.example.com/oidc-idp-config',
                ),
            ),
            self.msgs.ServiceAccountIdentityBinding(
                acceptanceFilter='true',
                cel=None,
                name=
                ('projects/test-project/serviceAccounts/{0}/identityBindings/2'
                 .format(service_account)),
                oidc=self.msgs.IDPReferenceOIDC(
                    audience='1234567890',
                    maxTokenLifetimeSeconds=7200,
                    url='https://www.example.test',
                ),
            )
        ]))

  def testListIdentityBinding(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    self._SetUpListIdentityBindingExpectations(service_account)

    self.Run('alpha iam service-accounts identity-bindings list '
             '--service-account {}'.format(service_account))

    self.AssertOutputContains(("""\
identityBinding:
- acceptanceFilter: 'true'
  name: projects/test-project/serviceAccounts/{0}/identityBindings/1
  oidc:
    audience: '1234567890'
    maxTokenLifetimeSeconds: '3600'
    url: https://www.example.com/oidc-idp-config
- acceptanceFilter: 'true'
  name: projects/test-project/serviceAccounts/{0}/identityBindings/2
  oidc:
    audience: '1234567890'
    maxTokenLifetimeSeconds: '7200'
    url: https://www.example.test
""").format(service_account))


if __name__ == '__main__':
  test_case.main()
