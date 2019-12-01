# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Test of the 'autoscaling-policies describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import unit_base


class AutoscalingPoliciesDescribeUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc autoscaling-policies describe."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testDescribeAutoscalingPolicies(self):
    mocked_response = self.MakeAutoscalingPolicy('fake-project',
                                                 'antarctica-north42',
                                                 'policy-1')
    self.mock_client.projects_regions_autoscalingPolicies.Get.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesGetRequest(
            name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-1'
        ),
        response=mocked_response)

    result = self.RunDataproc('autoscaling-policies describe policy-1')
    self.AssertMessagesEqual(result, mocked_response)

  def testDescribeAutoscalingPolicies_regionFlag(self):
    mocked_response = self.MakeAutoscalingPolicy('fake-project', 'cool-region',
                                                 'policy-1')
    self.mock_client.projects_regions_autoscalingPolicies.Get.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesGetRequest(
            name='projects/fake-project/regions/cool-region/autoscalingPolicies/policy-1'
        ),
        response=mocked_response)

    result = self.RunDataproc(
        'autoscaling-policies describe policy-1 --region cool-region',
        set_region=False)
    self.AssertMessagesEqual(result, mocked_response)

  def testDescribeAutoscalingPolicies_uri(self):
    mocked_response = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                                 'policy-1')
    self.mock_client.projects_regions_autoscalingPolicies.Get.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesGetRequest(
            name='projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1'
        ),
        response=mocked_response)

    # Overrides default project and default region
    result = self.RunDataproc(
        'autoscaling-policies describe projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1',
        set_region=False)
    self.AssertMessagesEqual(result, mocked_response)


class AutoscalingPoliciesDescribeUnitTestAlpha(
    AutoscalingPoliciesDescribeUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class AutoscalingPoliciesDescribeUnitTestBeta(
    AutoscalingPoliciesDescribeUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  sdk_test_base.main()
