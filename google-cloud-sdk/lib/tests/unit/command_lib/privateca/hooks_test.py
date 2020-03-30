# Lint as: python3
# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.hooks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.privateca import base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.command_lib.privateca import exceptions
from googlecloudsdk.command_lib.privateca import hooks
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import mock


def GetCertificateAuthorityRef(relative_name):
  return resources.REGISTRY.ParseRelativeName(
      relative_name=relative_name,
      collection='privateca.projects.locations.certificateAuthorities')


class HookTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.mock_client = api_mock.Client(
        base.GetClientClass(), real_client=base.GetClientInstance())
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = base.GetMessagesModule()

  def testInvalidResponseSubordinateType(self):
    response = self.messages.CertificateAuthority(
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidCertificateAuthorityTypeError, 'Root CA'):
      hooks.CheckResponseSubordinateTypeHook(response, None)

  def testInvalidResponseRootType(self):
    response = self.messages.CertificateAuthority(
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SUBORDINATE)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidCertificateAuthorityTypeError, 'Subordinate CA'):
      hooks.CheckResponseRootTypeHook(response, None)

  def testValidResponseRootType(self):
    response = self.messages.CertificateAuthority(
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED)
    hooks.CheckResponseRootTypeHook(response, None)

  @mock.patch.object(request_utils, 'GenerateRequestId')
  def testAddRequestIdHook(self, mock_request_utils):
    mock_request_utils.return_value = 'hooks_id'
    request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesDeleteRequest(
    )
    hooks.AddRequestIdHook(None, None, request)
    self.assertEqual(request.requestId, 'hooks_id')

  def testInvalidRequestRootType(self):
    ca_ref = GetCertificateAuthorityRef(
        'projects/projects/locations/europe-west1/certificateAuthorities/ca')
    request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesGetRequest(
        name=ca_ref.RelativeName())
    response = self.messages.CertificateAuthority(
        name=ca_ref.RelativeName(),
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SUBORDINATE)
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=request, response=response)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidCertificateAuthorityTypeError, 'Subordinate CA'):
      hooks.CheckRequestRootTypeHook(ca_ref, None, request)

  def testInvalidSubordinateRootType(self):
    ca_ref = GetCertificateAuthorityRef(
        'projects/projects/locations/europe-west1/certificateAuthorities/ca')
    request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesGetRequest(
        name=ca_ref.RelativeName())
    response = self.messages.CertificateAuthority(
        name=ca_ref.RelativeName(),
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED)
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=request, response=response)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidCertificateAuthorityTypeError, 'Root CA'):
      hooks.CheckRequestSubordinateTypeHook(ca_ref, None, request)

  def testValidRequestRootType(self):
    ca_ref = GetCertificateAuthorityRef(
        'projects/projects/locations/europe-west1/certificateAuthorities/ca')
    request = self.messages.PrivatecaProjectsLocationsCertificateAuthoritiesGetRequest(
        name=ca_ref.RelativeName())
    response = self.messages.CertificateAuthority(
        name=ca_ref.RelativeName(),
        type=self.messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED)
    self.mock_client.projects_locations_certificateAuthorities.Get.Expect(
        request=request, response=response)

    hooks.CheckRequestRootTypeHook(ca_ref, None, request)
