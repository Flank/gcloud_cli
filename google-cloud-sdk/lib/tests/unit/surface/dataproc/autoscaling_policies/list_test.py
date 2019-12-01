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
"""Test of the 'autoscaling-policies list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import unit_base


class AutoscalingPoliciesListUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc autoscaling-policies list."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testListAutoscalingPolicies(self):
    policy_1 = self.messages.AutoscalingPolicy(
        id='policy-1',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-1'
    )
    policy_2 = self.messages.AutoscalingPolicy(
        id='policy-2',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-2'
    )
    policy_3 = self.messages.AutoscalingPolicy(
        id='policy-3',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-3'
    )
    mocked_response = self.messages.ListAutoscalingPoliciesResponse(
        policies=[policy_1, policy_2, policy_3])
    self.mock_client.projects_regions_autoscalingPolicies.List.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesListRequest(
            pageSize=100,
            parent='projects/fake-project/regions/antarctica-north42'),
        response=mocked_response)

    self.RunDataproc('autoscaling-policies list', output_format='')
    self.AssertOutputEquals(
        textwrap.dedent("""\
ID
policy-1
policy-2
policy-3
"""))

  def testListAutoscalingPolicies_regionFlag(self):
    policy_1 = self.messages.AutoscalingPolicy(
        id='policy-1',
        name='projects/fake-project/regions/cool-region/autoscalingPolicies/policy-1'
    )
    policy_2 = self.messages.AutoscalingPolicy(
        id='policy-2',
        name='projects/fake-project/regions/cool-region/autoscalingPolicies/policy-2'
    )
    policy_3 = self.messages.AutoscalingPolicy(
        id='policy-3',
        name='projects/fake-project/regions/cool-region/autoscalingPolicies/policy-3'
    )
    mocked_response = self.messages.ListAutoscalingPoliciesResponse(
        policies=[policy_1, policy_2, policy_3])
    self.mock_client.projects_regions_autoscalingPolicies.List.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesListRequest(
            pageSize=100, parent='projects/fake-project/regions/cool-region'),
        response=mocked_response)

    self.RunDataproc(
        'autoscaling-policies list --region cool-region', output_format='')
    self.AssertOutputEquals(
        textwrap.dedent("""\
ID
policy-1
policy-2
policy-3
"""))

  def testListAutoscalingPolicies_pagination(self):
    policy_1 = self.messages.AutoscalingPolicy(
        id='policy-1',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-1'
    )
    policy_2 = self.messages.AutoscalingPolicy(
        id='policy-2',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-2'
    )
    policy_3 = self.messages.AutoscalingPolicy(
        id='policy-3',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-3'
    )
    self.mock_client.projects_regions_autoscalingPolicies.List.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesListRequest(
            pageSize=2,
            parent='projects/fake-project/regions/antarctica-north42'),
        response=self.messages.ListAutoscalingPoliciesResponse(
            policies=[policy_1, policy_2], nextPageToken='cool-token'))
    self.mock_client.projects_regions_autoscalingPolicies.List.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesListRequest(
            pageSize=2,
            parent='projects/fake-project/regions/antarctica-north42',
            pageToken='cool-token'),
        response=self.messages.ListAutoscalingPoliciesResponse(
            policies=[policy_3]))

    self.RunDataproc(
        'autoscaling-policies list --page-size=2', output_format='')
    self.AssertOutputEquals(
        textwrap.dedent("""\
ID
policy-1
policy-2

ID
policy-3
"""))

  def testListAutoscalingPolicies_uriListing(self):
    policy_1 = self.messages.AutoscalingPolicy(
        id='policy-1',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-1'
    )
    policy_2 = self.messages.AutoscalingPolicy(
        id='policy-2',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-2'
    )
    policy_3 = self.messages.AutoscalingPolicy(
        id='policy-3',
        name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-3'
    )
    mocked_response = self.messages.ListAutoscalingPoliciesResponse(
        policies=[policy_1, policy_2, policy_3])
    self.mock_client.projects_regions_autoscalingPolicies.List.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesListRequest(
            pageSize=100,
            parent='projects/fake-project/regions/antarctica-north42'),
        response=mocked_response)

    self.RunDataproc('autoscaling-policies list --uri', output_format='')
    # Note that there's no header
    self.AssertOutputEquals(
        textwrap.dedent("""\
projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-1
projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-2
projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-3
"""))


class AutoscalingPoliciesListUnitTestAlpha(AutoscalingPoliciesListUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class AutoscalingPoliciesListUnitTestBeta(AutoscalingPoliciesListUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  sdk_test_base.main()
