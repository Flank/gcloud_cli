# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager perimeters dry-run list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class DryRunListTestBeta(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectList(self, perimeters_to_return, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    request_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersListRequest)
    self.client.accessPolicies_servicePerimeters.List.Expect(
        request_type(parent=policy_name,),
        m.ListServicePerimetersResponse(servicePerimeters=perimeters_to_return))

  def testList(self):
    self.SetUpForAPI(self.api_version)
    perimeter1 = self._MakePerimeter(
        'MY_PERIMETER_1',
        title='Perimeter 1',
        resources=['projects/123', 'projects/456'],
        restricted_services=['storage.googleapis.com'],
        dry_run=True)
    perimeter2 = self._MakePerimeter(
        'MY_PERIMETER_2',
        title='Perimeter 2',
        resources=['projects/789', 'projects/901'],
        restricted_services=['bigquery.googleapis.com'])
    transformed_perimeter2 = self._MakePerimeter(
        'MY_PERIMETER_2',
        title='Perimeter 2',
        resources=['projects/789', 'projects/901'],
        restricted_services=['bigquery.googleapis.com'],
        dry_run=True)
    # The name should have an  appended to indicate it uses an inherited
    # dry-run config.
    transformed_perimeter2.name += '*'
    # The use_explicit_dry_run_spec field isn't touched by the list command.
    transformed_perimeter2.useExplicitDryRunSpec = None

    self._ExpectList([perimeter1, perimeter2], '123')

    output = self.Run('access-context-manager perimeters dry-run list'
                      '   --policy 123')

    self.AssertOutputEquals(
        """\
        Note: Perimeters marked with '*' do not have an explicit `spec`. \
        Instead, their `status` also acts as the `spec`.
        """,
        normalize_space=True)

    self.assertEqual(output[0], perimeter1)
    self.assertEqual(output[1], transformed_perimeter2)


class DryRunListTestAlpha(DryRunListTestBeta):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
