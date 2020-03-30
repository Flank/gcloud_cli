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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import unit_base


class AutoscalingPoliciesDeleteUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc autoscaling-policies list."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _testDeleteAutoscalingPolicies(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    self.mock_client.projects_regions_autoscalingPolicies.Delete.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesDeleteRequest(
            name='projects/fake-project/regions/{0}/autoscalingPolicies/policy-1'
            .format(region)),
        response=self.messages.Empty())
    self.WriteInput('Y\n')
    result = self.RunDataproc(
        'autoscaling-policies delete policy-1 {0}'.format(region_flag))
    self.AssertErrContains(
        "The autoscaling policy '[policy-1]' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(None, result)

  def testDeleteAutoscalingPolicies(self):
    self._testDeleteAutoscalingPolicies()

  def testDeleteAutoscalingPolicies_decline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.RunDataproc('autoscaling-policies delete policy-1')
      self.AssertErrContains(
          "The autoscaling policy '[policy-1]' will be deleted.")
      self.AssertErrContains('PROMPT_CONTINUE')

  def testDeleteAutoscalingPolicies_regionProperty(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testDeleteAutoscalingPolicies(region='us-central1')

  def testDeleteAutoscalingPolicies_regionFlag(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testDeleteAutoscalingPolicies(
        region='cool-region', region_flag='--region=cool-region')

  def testDeleteAutoscalingPolicies_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('autoscaling-policies delete policy-1', set_region=False)

  def testDeleteAutoscalingPolicies_uri(self):
    self.mock_client.projects_regions_autoscalingPolicies.Delete.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesDeleteRequest(
            name='projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1'
        ),
        response=self.messages.Empty())
    self.WriteInput('Y\n')
    # Overriding default project and region
    result = self.RunDataproc(
        'autoscaling-policies delete projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1',
        set_region=False)
    self.AssertErrContains(
        "The autoscaling policy '[policy-1]' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(None, result)


class AutoscalingPoliciesDeleteUnitTestAlpha(AutoscalingPoliciesDeleteUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class AutoscalingPoliciesDeleteUnitTestBeta(AutoscalingPoliciesDeleteUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  sdk_test_base.main()
