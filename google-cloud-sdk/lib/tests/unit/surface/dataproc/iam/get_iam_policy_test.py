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

"""Tests for the dataproc * get-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class GetIamPolicyTestBeta(parameterized.TestCase,
                           unit_base.DataprocIAMUnitTestBase,
                           base.DataprocTestBaseBeta):
  """Tests for dataproc * get-iam-policy."""

  @parameterized.named_parameters(
      ('Cluster', 'clusters'),
      ('Job', 'jobs'),
      ('Operation', 'operations'),
      ('WorkflowTemplate', 'workflow-templates'),
      ('AutoscalingPolicy', 'autoscaling-policies'),
  )
  def testGetIAMPolicy(self, collection):
    self.GetIamPolicyNoError(collection)
    self.GetIamPolicyNoErrorFlagOverrideRegion(collection)
    self.GetIamPolicyNotFound(collection)

  def GetIamPolicyNoError(self, collection):
    properties.VALUES.dataproc.region.Set(self.REGION)
    expected_resource = self.RelativeName(collection)

    self.ExpectGetIamPolicy(collection, expected_resource)

    policy = self.RunDataproc('{0} get-iam-policy test-{0}'.format(collection))
    self.assertIsNotNone(policy)
    self.AssertMessagesEqual(policy, self.GetTestIamPolicy())

  def GetIamPolicyNoErrorFlagOverrideRegion(self, collection):
    properties.VALUES.dataproc.region.Set('other-default-region')
    expected_resource = self.RelativeName(collection)

    self.ExpectGetIamPolicy(collection, expected_resource)

    # The --region flag should override properties.VALUES.dataproc.region.
    policy = self.RunDataproc('{0} get-iam-policy --region {1} test-{0}'.format(
        collection, self.REGION))
    self.assertIsNotNone(policy)
    self.AssertMessagesEqual(policy, self.GetTestIamPolicy())

  def GetIamPolicyNotFound(self, collection):
    properties.VALUES.dataproc.region.Set(self.REGION)
    expected_resource = self.RelativeName(collection)
    exception = self.MakeHttpError(404)

    self.ExpectGetIamPolicy(collection, expected_resource, exception)

    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: Resource not found.'):
      self.RunDataproc('{0} get-iam-policy test-{0}'.format(collection))

  def ExpectGetIamPolicy(self, collection, resource, exception=None):
    response = None
    if not exception:
      response = self.GetTestIamPolicy()

    request_message_class = self.GetIAMPolicyMessageClass(collection)
    mocked_service = self.MockedService(collection)
    mocked_service.GetIamPolicy.Expect(
        request_message_class(resource=resource),
        response=response,
        exception=exception)


class GetIamPolicyTestGA(GetIamPolicyTestBeta, base.DataprocTestBaseGA):
  """Tests for GA dataproc * get-iam-policy."""


class GetIamPolicyTestAlpha(GetIamPolicyTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
