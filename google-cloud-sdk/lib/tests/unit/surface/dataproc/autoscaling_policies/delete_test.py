# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import unit_base


class AutoscalingPoliciesDeleteUnitTestBeta(unit_base.DataprocUnitTestBase):
  """Tests for dataproc autoscaling-policies list."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testDeleteAutoscalingPolicies(self):
    self.mock_client.projects_regions_autoscalingPolicies.Delete.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesDeleteRequest(
            name='projects/fake-project/regions/global/autoscalingPolicies/policy-1'
        ),
        response=self.messages.Empty())
    self.WriteInput('Y\n')
    result = self.RunDataproc('autoscaling-policies delete policy-1')
    self.AssertErrContains(
        "The autoscaling policy '[policy-1]' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(None, result)

  def testDeleteAutoscalingPolicies_decline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.RunDataproc('autoscaling-policies delete policy-1')
      self.AssertErrContains(
          "The autoscaling policy '[policy-1]' will be deleted.")
      self.AssertErrContains('PROMPT_CONTINUE')

  def testDeleteAutoscalingPolicies_regionFlag(self):
    self.mock_client.projects_regions_autoscalingPolicies.Delete.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesDeleteRequest(
            name='projects/fake-project/regions/cool-region/autoscalingPolicies/policy-1'
        ),
        response=self.messages.Empty())
    self.WriteInput('Y\n')
    result = self.RunDataproc(
        'autoscaling-policies delete policy-1 --region cool-region')
    self.AssertErrContains(
        "The autoscaling policy '[policy-1]' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(None, result)

  def testDeleteAutoscalingPolicies_uri(self):
    self.mock_client.projects_regions_autoscalingPolicies.Delete.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesDeleteRequest(
            name='projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1'
        ),
        response=self.messages.Empty())
    self.WriteInput('Y\n')
    # Overriding default project and region
    result = self.RunDataproc(
        'autoscaling-policies delete projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1'
    )
    self.AssertErrContains(
        "The autoscaling policy '[policy-1]' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(None, result)


class AutoscalingPoliciesDeleteUnitTestAlpha(
    AutoscalingPoliciesDeleteUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  sdk_test_base.main()
