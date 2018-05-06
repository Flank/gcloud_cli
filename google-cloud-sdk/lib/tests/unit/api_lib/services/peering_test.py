# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests of the peering module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.services import peering
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class PeeringTest(unit_test_base.SNV1alphaUnitTestBase):
  """Unit tests for peering module."""

  OPERATION_NAME = 'operations/abc.0000000000'
  NETWORK = 'hello'
  RANGES = ['10.0.1.0/30', '10.0.3.0/30']

  def testPeerApiCall_Success(self):
    """Test PeerApiCall returns operation when successful."""
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectPeerApiCall(self.NETWORK, self.RANGES, self.OPERATION_NAME)

    got = peering.PeerApiCall(self.PROJECT_NUMBER, self.DEFAULT_SERVICE_NAME,
                              self.NETWORK, self.RANGES)

    self.assertEqual(got, want)

  def testPeerApiCall_PermissionDenied(self):
    """Test PeerApiCall raises correctly when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectPeerApiCall(self.NETWORK, self.RANGES, None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.PeerServicePermissionDeniedException, r'Error.'):
      peering.PeerApiCall(self.PROJECT_NUMBER, self.DEFAULT_SERVICE_NAME,
                          self.NETWORK, self.RANGES)

  def testGetOperation_Success(self):
    """Test GetOperation returns operation when successful."""
    want = self.services_messages.Operation(name=self.OPERATION_NAME, done=True)
    self.ExpectOperation(self.OPERATION_NAME, 0)

    got = peering.GetOperation(self.OPERATION_NAME)

    self.assertEqual(got, want)

  def testGetOperation_PermissionDenied(self):
    """Test GetOperation returns operation when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectOperation(self.OPERATION_NAME, 0, error=server_error)

    with self.assertRaisesRegex(exceptions.OperationErrorException, r'Error.'):
      peering.GetOperation(self.OPERATION_NAME)

  def testWaitOperation_Success(self):
    """Test WaitOperation returns operation when successful."""
    want = self.services_messages.Operation(name=self.OPERATION_NAME, done=True)
    self.ExpectOperation(self.OPERATION_NAME, 3)

    got = peering.WaitOperation(self.OPERATION_NAME)

    self.assertEqual(got, want)
