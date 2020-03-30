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
"""Test of the 'autoscaling-policies export' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import unit_base


class AutoscalingPoliciesExportUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc autoscaling-policies export."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _testExportAutoscalingPolicies(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION

    mocked_response = self.MakeAutoscalingPolicy('fake-project', region,
                                                 'policy-1')
    self.mock_client.projects_regions_autoscalingPolicies.Get.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesGetRequest(
            name='projects/fake-project/regions/{0}/autoscalingPolicies/policy-1'
            .format(region)),
        response=mocked_response)

    # Export clears id/name, since they cannot be set in import
    expected_policy = copy.deepcopy(mocked_response)
    expected_policy.id = None
    expected_policy.name = None

    self.RunDataproc(
        'autoscaling-policies export policy-1 {0}'.format(region_flag))
    self.AssertOutputEquals(export_util.Export(expected_policy))

  def testExportAutoscalingPolicies(self):
    self._testExportAutoscalingPolicies()

  def testExportAutoscalingPolicies_regionProperty(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testExportAutoscalingPolicies(region='global')

  def testExportAutoscalingPolicies_regionFlag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testExportAutoscalingPolicies(
        region='cool-region', region_flag='--region=cool-region')

  def testExportAutoscalingPolicies_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('autoscaling-policies export policy-1', set_region=False)

  def testExportAutoscalingPolicies_uri(self):
    mocked_response = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                                 'policy-1')
    self.mock_client.projects_regions_autoscalingPolicies.Get.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesGetRequest(
            name='projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1'
        ),
        response=mocked_response)

    # Export clears id/name, since they cannot be set in import
    expected_policy = copy.deepcopy(mocked_response)
    expected_policy.id = None
    expected_policy.name = None

    # Overrides default project and default region
    self.RunDataproc(
        'autoscaling-policies export projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1',
        set_region=False)
    self.AssertOutputEquals(export_util.Export(expected_policy))

  def testExportAutoscalingPolicies_destinationFile(self):
    mocked_response = self.MakeAutoscalingPolicy('fake-project',
                                                 'antarctica-north42',
                                                 'policy-1')
    self.mock_client.projects_regions_autoscalingPolicies.Get.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesGetRequest(
            name='projects/fake-project/regions/antarctica-north42/autoscalingPolicies/policy-1'
        ),
        response=mocked_response)

    # Export clears id/name, since they cannot be set in import
    expected_policy = copy.deepcopy(mocked_response)
    expected_policy.id = None
    expected_policy.name = None

    file_name = os.path.join(self.temp_path, 'template.yaml')
    self.RunDataproc(
        'autoscaling-policies export policy-1 --destination {}'.format(
            file_name))
    contents = console_io.ReadFromFileOrStdin(file_name, binary=False)
    exported_message = export_util.Import(
        message_type=self.messages.AutoscalingPolicy, stream=contents)
    self.AssertMessagesEqual(expected_policy, exported_message)


class AutoscalingPoliciesExportUnitTestAlpha(AutoscalingPoliciesExportUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class AutoscalingPoliciesExportUnitTestBeta(AutoscalingPoliciesExportUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  sdk_test_base.main()
