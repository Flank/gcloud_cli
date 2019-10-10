# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the backend services delete-signed-url-key alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import backend_services_test_base


class BackendServiceDeleteSignedUrlKeyTestGA(
    backend_services_test_base.BackendServicesTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def testWithKeyNameArg(self):
    """Tests deleting a key is successful."""
    backend_service_ref = self.GetBackendServiceRef('backend-service-1')
    updated_backend_service = self.MakeBackendServiceMessage(
        backend_service_ref=backend_service_ref,
        enable_cdn=True,
        signed_url_key_names=['key1', 'key3'])
    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(operation_ref, backend_service_ref)

    self.ExpectDeleteSignedUrlKeyRequest(backend_service_ref, 'key2', operation)
    self.ExpectOperationGetRequest(operation_ref, operation)
    self.ExpectGetRequest(backend_service_ref, updated_backend_service)

    response = self.RunBackendServices('delete-signed-url-key ' +
                                       backend_service_ref.Name() +
                                       ' --key-name key2')
    self.assertEqual(response, updated_backend_service)

  def testWithoutKeyNameArg(self):
    """Tests failure when the key name argument is not specified."""
    backend_service_ref = self.GetBackendServiceRef('backend-service-1')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --key-name: Must be specified.'):
      self.RunBackendServices('delete-signed-url-key ' +
                              backend_service_ref.Name())


class BackendServiceDeleteSignedUrlKeyTestBeta(
    BackendServiceDeleteSignedUrlKeyTestGA):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class BackendServiceDeleteSignedUrlKeyTestAlpha(
    BackendServiceDeleteSignedUrlKeyTestBeta):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
