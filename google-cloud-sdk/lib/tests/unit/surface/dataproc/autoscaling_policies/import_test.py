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
"""Test of the 'autoscaling-policies import' command."""

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
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import unit_base


class AutoscalingPoliciesImportUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc autoscaling-policies import."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  # N.B. this test suite assumes edge cases around reading the YAML files and
  # resolving duration fields is already taken care of in util_test.py.

  def _testImportAutoscalingPolicies_create(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION

    policy = self.MakeAutoscalingPolicy('fake-project', region, 'policy-1')

    self.WriteInput(export_util.Export(message=policy))

    expected_request_policy = copy.deepcopy(policy)
    expected_request_policy.name = None

    response_policy = copy.deepcopy(expected_request_policy)
    response_policy.name = ('projects/fake-project/regions/{0}/'
                            'autoscalingPolicies/policy-1'.format(region))

    self.mock_client.projects_regions_autoscalingPolicies.Create.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesCreateRequest(
            parent='projects/fake-project/regions/{0}'.format(region),
            autoscalingPolicy=expected_request_policy,
        ),
        response=response_policy)

    result = self.RunDataproc(
        'autoscaling-policies import policy-1 {0}'.format(region_flag))
    self.AssertMessagesEqual(response_policy, result)

  def testImportAutoscalingPolicies_create(self):
    self._testImportAutoscalingPolicies_create()

  def testImportAutoscalingPolicies_create_regionProperty(self):
    properties.VALUES.dataproc.region.Set('cool-region')
    self._testImportAutoscalingPolicies_create(region='cool-region')

  def testImportAutoscalingPolicies_create_regionFlag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testImportAutoscalingPolicies_create(
        region='cool-region', region_flag='--region=cool-region')

  def testImportAutoscalingPolicies_create_withoutRegionProperty(self):
    policy = self.MakeAutoscalingPolicy('fake-project', 'foobar', 'policy-1')

    self.WriteInput(export_util.Export(message=policy))

    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('autoscaling-policies import policy-1', set_region=False)

  def testImportAutoscalingPolicies_create_uri(self):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'policy-1')

    self.WriteInput(export_util.Export(message=policy))

    expected_request_policy = copy.deepcopy(policy)
    expected_request_policy.name = None

    response_policy = copy.deepcopy(expected_request_policy)
    response_policy.name = 'projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1'

    self.mock_client.projects_regions_autoscalingPolicies.Create.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesCreateRequest(
            parent='projects/cool-project/regions/cool-region',
            autoscalingPolicy=expected_request_policy,
        ),
        response=response_policy)

    result = self.RunDataproc(
        'autoscaling-policies import projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1'
    )
    self.AssertMessagesEqual(response_policy, result)

  def testImportAutoscalingPolicies_alreadyExists(self):
    policy = self.MakeAutoscalingPolicy('fake-project', 'antarctica-north42',
                                        'policy-1')

    self.WriteInput(export_util.Export(message=policy))

    expected_request_policy = copy.deepcopy(policy)
    expected_request_policy.name = None

    self.mock_client.projects_regions_autoscalingPolicies.Create.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesCreateRequest(
            parent='projects/fake-project/regions/antarctica-north42',
            autoscalingPolicy=expected_request_policy,
        ),
        exception=self.MakeHttpError(status_code=409))

    self.mock_client.projects_regions_autoscalingPolicies.Update.Expect(
        policy, response=policy)

    result = self.RunDataproc('autoscaling-policies import policy-1 --quiet')
    self.AssertMessagesEqual(policy, result)

  def testImportAutoscalingPolicies_alreadyExists_regionFlag(self):
    policy = self.MakeAutoscalingPolicy('fake-project', 'cool-region',
                                        'policy-1')

    self.WriteInput(export_util.Export(message=policy))

    expected_request_policy = copy.deepcopy(policy)
    expected_request_policy.name = None

    self.mock_client.projects_regions_autoscalingPolicies.Create.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesCreateRequest(
            parent='projects/fake-project/regions/cool-region',
            autoscalingPolicy=expected_request_policy,
        ),
        exception=self.MakeHttpError(status_code=409))

    self.mock_client.projects_regions_autoscalingPolicies.Update.Expect(
        policy, response=policy)

    result = self.RunDataproc(
        'autoscaling-policies import policy-1 --region cool-region  --quiet',
        set_region=False)
    self.AssertMessagesEqual(policy, result)

  def testImportAutoscalingPolicies_alreadyExists_uri(self):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'policy-1')

    self.WriteInput(export_util.Export(message=policy))

    expected_request_policy = copy.deepcopy(policy)
    expected_request_policy.name = None

    self.mock_client.projects_regions_autoscalingPolicies.Create.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesCreateRequest(
            parent='projects/cool-project/regions/cool-region',
            autoscalingPolicy=expected_request_policy,
        ),
        exception=self.MakeHttpError(status_code=409))

    self.mock_client.projects_regions_autoscalingPolicies.Update.Expect(
        policy, response=policy)

    result = self.RunDataproc(
        'autoscaling-policies import projects/cool-project/regions/cool-region/autoscalingPolicies/policy-1 --quiet',
        set_region=False)
    self.AssertMessagesEqual(policy, result)

  def testImportAutoscalingPolicies_unexpectedError(self):
    policy = self.MakeAutoscalingPolicy('fake-project', 'antarctica-north42',
                                        'policy-1')

    self.WriteInput(export_util.Export(message=policy))

    expected_request_policy = copy.deepcopy(policy)
    expected_request_policy.name = None

    self.mock_client.projects_regions_autoscalingPolicies.Create.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesCreateRequest(
            parent='projects/fake-project/regions/antarctica-north42',
            autoscalingPolicy=expected_request_policy,
        ),
        exception=self.MakeHttpError(status_code=403))

    # Should re-throw PERMISSION_DENIED, which is a fatal error
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('autoscaling-policies import policy-1 --quiet')

  def testImportAutoscalingPolicies_update_declineOverwrite(self):
    policy = self.MakeAutoscalingPolicy('fake-project', 'antarctica-north42',
                                        'policy-1')

    # Write to a file so that we can use stdin to decline the prompt. Otherwise,
    # we wouldn't have a way to demarcate where the policy ends and declining
    # the prompt starts.
    file_name = os.path.join(self.temp_path, 'policy.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(
          message=policy,
          stream=stream,
      )

    expected_request_policy = copy.deepcopy(policy)
    expected_request_policy.name = None

    self.mock_client.projects_regions_autoscalingPolicies.Create.Expect(
        self.messages.DataprocProjectsRegionsAutoscalingPoliciesCreateRequest(
            parent='projects/fake-project/regions/antarctica-north42',
            autoscalingPolicy=expected_request_policy,
        ),
        exception=self.MakeHttpError(status_code=409))

    # Don't pass --quiet, and decline the prompt
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.RunDataproc(
          'autoscaling-policies import policy-1 --source {}'.format(file_name))


class AutoscalingPoliciesImportUnitTestAlpha(AutoscalingPoliciesImportUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class AutoscalingPoliciesImportUnitTestBeta(AutoscalingPoliciesImportUnitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  sdk_test_base.main()
