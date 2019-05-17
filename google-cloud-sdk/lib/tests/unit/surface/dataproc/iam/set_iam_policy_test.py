# -*- coding: utf-8 -*- #
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

"""Test of the 'dataproc * set-iam-policy' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class SetIamPolicyTestBeta(parameterized.TestCase,
                           unit_base.DataprocIAMUnitTestBase,
                           base.DataprocTestBaseBeta):
  """Tests for dataproc * set-iam-policy."""

  @parameterized.named_parameters(
      ('Cluster', 'clusters'),
      ('Job', 'jobs'),
      ('Operation', 'operations'),
      ('WorkflowTemplate', 'workflow-templates'),
      ('AutoscalingPolicy', 'autoscaling-policies'),
  )
  def testSetIAMPolicy(self, collection):
    self.SetIamPolicyNoError(collection)
    self.SetIamPolicyNotFound(collection)

  def SetIamPolicyNoError(self, collection):
    new_policy = self.GetTestIamPolicy()
    temp_file = self.GetFileForPolicy(new_policy)
    properties.VALUES.dataproc.region.Set(self.REGION)
    expected_resource = self.RelativeName(collection)

    self.ExpectSetIamPolicy(collection, expected_resource, new_policy)

    policy = self.RunDataproc('{0} set-iam-policy test-{0} {1}'.format(
        collection, temp_file))
    self.assertIsNotNone(policy)
    self.AssertMessagesEqual(policy, new_policy)

  def SetIamPolicyNotFound(self, collection):
    new_policy = self.GetTestIamPolicy()
    temp_file = self.GetFileForPolicy(new_policy)
    expected_resource = self.RelativeName(collection)
    exception = self.MakeHttpError(404)

    self.ExpectSetIamPolicy(collection, expected_resource,
                            new_policy, exception=exception)

    properties.VALUES.dataproc.region.Set(self.REGION)
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: Resource not found.'):
      self.RunDataproc('{0} set-iam-policy test-{0} {1}'.format(
          collection, temp_file))

  def GetFileForPolicy(self, policy):
    json = encoding.MessageToJson(policy)
    return self.Touch(self.temp_path, 'good.json', contents=json)

  def ExpectSetIamPolicy(self, collection, resource, policy, exception=None):
    response = None
    if not exception:
      response = policy

    request_message_class = self.SetIAMPolicyMessageClass(collection)
    mocked_service = self.MockedService(collection)
    set_iam_policy_message = self.messages.SetIamPolicyRequest(policy=policy)
    mocked_service.SetIamPolicy.Expect(
        request_message_class(resource=resource,
                              setIamPolicyRequest=set_iam_policy_message),
        response=response,
        exception=exception)


class SetIamPolicyTestGA(SetIamPolicyTestBeta, base.DataprocTestBaseGA):
  """Tests for beta dataproc * set-iam-policy."""


class SetIamPolicyTestAlpha(SetIamPolicyTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
