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


class DescribeTest(unit_test_base.BaseTest):

  def _SetUpGetIdentityBindingExpectations(self, service_account,
                                           identity_binding):
    self.client.projects_serviceAccounts_identityBindings.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsIdentityBindingsGetRequest(
            name=('projects/-/serviceAccounts/{0}/identityBindings/{1}'.format(
                service_account, identity_binding))),
        response=self.msgs.ServiceAccountIdentityBinding(
            acceptanceFilter='true',
            cel=None,
            name=(
                'projects/test-project/serviceAccounts/{0}/identityBindings/{1}'
                .format(service_account, identity_binding)),
            oidc=self.msgs.IDPReferenceOIDC(
                audience='1234567890',
                maxTokenLifetimeSeconds=3600,
                url='https://www.example.com/oidc-idp-config',
            ),
        ))

  def testDescribeIdentityBinding(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    identity_binding = 'd34db33fd34db33fd34db33fd34db33f'
    self._SetUpGetIdentityBindingExpectations(service_account, identity_binding)

    self.Run('alpha iam service-accounts identity-bindings describe '
             '{identity_binding} '
             '--service-account {service_account} '.format(
                 service_account=service_account,
                 identity_binding=identity_binding))

    self.AssertOutputContains(("""\
acceptanceFilter: 'true'
name: projects/test-project/serviceAccounts/{0}/identityBindings/{1}
oidc:
  audience: '1234567890'
  maxTokenLifetimeSeconds: '3600'
  url: https://www.example.com/oidc-idp-config
""").format(service_account, identity_binding))


if __name__ == '__main__':
  test_case.main()
