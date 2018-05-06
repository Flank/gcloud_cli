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
"""Tests for the SSL policies delete alpha command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import ssl_policies_test_base
from tests.lib.surface.compute import utils
from six.moves import range  # pylint: disable=redefined-builtin


class SslPolicyDeleteGATest(ssl_policies_test_base.SslPoliciesTestBase):

  def SetUp(self):
    self._SetUpReleaseTrack()
    self.api_mock = utils.ComputeApiMock(
        self._GetApiName(self.track), project=self.Project()).Start()
    self.addCleanup(self.api_mock.Stop)

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def _MakeOperationGetRequest(self, operation_ref):
    return (self.global_operations, 'Get',
            self.messages.ComputeGlobalOperationsGetRequest(
                **operation_ref.AsDict()))

  def testDeleteSingleSslPolicy(self):
    name = 'my-ssl-policy'
    ssl_policy_ref = self.GetSslPolicyRef(name)
    operation_ref = self.GetOperationRef('operation-1')
    pending_operation = self.MakeOperationMessage(
        operation_ref, self.messages.Operation.StatusValueValuesEnum.PENDING,
        ssl_policy_ref)
    done_operation = self.MakeOperationMessage(
        operation_ref, self.messages.Operation.StatusValueValuesEnum.DONE,
        ssl_policy_ref)

    self.ExpectDeleteRequest(ssl_policy_ref, pending_operation)

    self.api_mock.batch_responder.ExpectBatch(
        [(self._MakeOperationGetRequest(operation_ref), pending_operation)])
    self.api_mock.batch_responder.ExpectBatch(
        [(self._MakeOperationGetRequest(operation_ref), done_operation)])

    self.Run('compute ssl-policies delete {}'.format(name))

  def testDeleteMultipleSslPolicies(self):
    names = ['my-ssl-policy-{}'.format(n) for n in range(0, 3)]
    ssl_policy_refs = [self.GetSslPolicyRef(name) for name in names]
    operation_refs = [
        self.GetOperationRef('operation-{}'.format(n)) for n in range(0, 3)
    ]
    pending_operations = [
        self.MakeOperationMessage(
            operation_refs[n],
            self.messages.Operation.StatusValueValuesEnum.PENDING,
            ssl_policy_refs[n]) for n in range(0, 3)
    ]
    done_operations = [
        self.MakeOperationMessage(
            operation_refs[n],
            self.messages.Operation.StatusValueValuesEnum.DONE,
            ssl_policy_refs[n]) for n in range(0, 3)
    ]

    for n in range(0, 3):
      self.ExpectDeleteRequest(ssl_policy_refs[n], pending_operations[n])

    self.api_mock.batch_responder.ExpectBatch([(self._MakeOperationGetRequest(
        operation_refs[n]), pending_operations[n]) for n in range(0, 3)])
    self.api_mock.batch_responder.ExpectBatch([(self._MakeOperationGetRequest(
        operation_refs[n]), done_operations[n]) for n in range(0, 3)])

    self.Run('compute ssl-policies delete {}'.format(' '.join(names)))


class SslPolicyDeleteBetaTest(SslPolicyDeleteGATest):

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class SslPolicyDeleteAlphaTest(SslPolicyDeleteBetaTest):

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
