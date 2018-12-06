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
"""Tests for `iam service-accounts identity-bindings create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base

import six


class CreateTest(unit_test_base.BaseTest):

  def _SetUpCreateIdentityBindingExpectations(self,
                                              service_account,
                                              idp_url,
                                              translator_cel_map=None,
                                              acceptance_filter=None,
                                              audience=None,
                                              token_lifetime=None):
    cel = None
    if translator_cel_map:
      attribute_translator_cels = [
          self.msgs.AttributeTranslatorCEL.AttributesValue.AdditionalProperty(
              key=key, value=value)
          for key, value in six.iteritems(translator_cel_map)
      ]
      cel = self.msgs.AttributeTranslatorCEL(
          attributes=self.msgs.AttributeTranslatorCEL.AttributesValue(
              additionalProperties=attribute_translator_cels))

    oidc = self.msgs.IDPReferenceOIDC(
        audience=audience,
        maxTokenLifetimeSeconds=token_lifetime,
        url=idp_url,
    )
    req = self.msgs.CreateServiceAccountIdentityBindingRequest(
        acceptanceFilter=acceptance_filter,
        cel=cel,
        oidc=oidc,
    )

    self.client.projects_serviceAccounts_identityBindings.Create.Expect(
        request=self.msgs
        .IamProjectsServiceAccountsIdentityBindingsCreateRequest(
            createServiceAccountIdentityBindingRequest=req,
            name='projects/-/serviceAccounts/' + service_account),
        response=self.msgs.ServiceAccountIdentityBinding(
            acceptanceFilter=acceptance_filter,
            cel=cel,
            name=
            ('projects/test-project/serviceAccounts/{}/identityBindings/idb_id'
             .format(service_account)),
            oidc=oidc,
        ))

  def testCreateIdentityBinding_MinimumArgs(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    idp_url = 'https://www.example.com/oidc-idp-config'
    self._SetUpCreateIdentityBindingExpectations(service_account, idp_url)

    self.Run('alpha iam service-accounts identity-bindings create '
             '--service-account {0} --oidc-issuer-url {1}'.format(
                 service_account, idp_url))

    self.AssertErrContains(
        ('Created service account identity binding '
         '[projects/test-project/serviceAccounts/{}/identityBindings/idb_id]'
        ).format(service_account))

  def testCreateIdentityBinding(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    idp_url = 'https://www.example.com/oidc-idp-config'
    translator_cel_map = {
        'namespace': 'inclaim["kubernetes.io"]["namespace"]',
    }
    acceptance_filter = 'true'
    audience = '1234567890'
    token_lifetime = 3600
    self._SetUpCreateIdentityBindingExpectations(
        service_account, idp_url, translator_cel_map, acceptance_filter,
        audience, token_lifetime)

    self.Run('alpha iam service-accounts identity-bindings create '
             '--service-account {service_account} '
             '--acceptance-filter {acceptance_filter} '
             '--attribute-translator-cel '
             '\'namespace=inclaim["kubernetes.io"]["namespace"]\' '
             '--oidc-issuer-url {idp_url} '
             '--oidc-audience {audience} '
             '--oidc-max-token-lifetime {token_lifetime}'.format(
                 service_account=service_account,
                 acceptance_filter=acceptance_filter,
                 idp_url=idp_url,
                 audience=audience,
                 token_lifetime=token_lifetime))

    self.AssertErrContains(
        ('Created service account identity binding '
         '[projects/test-project/serviceAccounts/{}/identityBindings/idb_id]'
        ).format(service_account))


if __name__ == '__main__':
  test_case.main()
