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
"""E2E tests for `gcloud access-context-manager cloud-bindings` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.util.platforms import OperatingSystem
from tests.lib import cli_test_base
from tests.lib import e2e_base


class AccessContextManagerCloudBindingsE2eTests(e2e_base.WithServiceAuth,
                                                cli_test_base.CliTestBase):
  SHARDING_QUOTA_PROJECT = {
      # cloudsdk-gcp01.gen.atc-test.dev's billing project
      OperatingSystem.LINUX: {
          calliope_base.ReleaseTrack.ALPHA: '91031288370',
      },
      # cloudsdk-gcp03.gen.atc-test.dev's billing project
      OperatingSystem.MACOSX: {
          calliope_base.ReleaseTrack.ALPHA: '640425900154',
      },
      # cloudsdk-gcp04.gen.atc-test.dev's billing project
      OperatingSystem.WINDOWS: {
          calliope_base.ReleaseTrack.ALPHA: '211734836811',
      }
  }
  SHARDING_ORG = {
      # cloudsdk-gcp01.gen.atc-test.dev
      OperatingSystem.LINUX: {
          calliope_base.ReleaseTrack.ALPHA: '728931762798',
      },
      # cloudsdk-gcp03.gen.atc-test.dev
      OperatingSystem.MACOSX: {
          calliope_base.ReleaseTrack.ALPHA: '668581339188',
      },
      # cloudsdk-gcp04.gen.atc-test.dev
      OperatingSystem.WINDOWS: {
          calliope_base.ReleaseTrack.ALPHA: '385026945973',
      }
  }
  ACCESS_LEVEL_1 = {
      OperatingSystem.LINUX: {
          calliope_base.ReleaseTrack.ALPHA:
              'accessPolicies/659121542999/accessLevels/gcloud_test_level_1',
      },
      OperatingSystem.MACOSX: {
          calliope_base.ReleaseTrack.ALPHA:
              'accessPolicies/416104096791/accessLevels/gcloud_test_level_1',
      },
      OperatingSystem.WINDOWS: {
          calliope_base.ReleaseTrack.ALPHA:
              'accessPolicies/104765632324/accessLevels/gcloud_test_level_1',
      }
  }
  ACCESS_LEVEL_2 = {
      OperatingSystem.LINUX: {
          calliope_base.ReleaseTrack.ALPHA:
              'accessPolicies/659121542999/accessLevels/gcloud_test_level_2',
      },
      OperatingSystem.MACOSX: {
          calliope_base.ReleaseTrack.ALPHA:
              'accessPolicies/416104096791/accessLevels/gcloud_test_level_2',
      },
      OperatingSystem.WINDOWS: {
          calliope_base.ReleaseTrack.ALPHA:
              'accessPolicies/104765632324/accessLevels/gcloud_test_level_2',
      }
  }
  GROUP = {
      OperatingSystem.LINUX: {
          # group1@cloudsdk-gcp01.gen.atc-test.dev
          calliope_base.ReleaseTrack.ALPHA:
              '02afmg282e8gphx',
      },
      OperatingSystem.MACOSX: {
          # group1@cloudsdk-gcp04.gen.atc-test.dev
          calliope_base.ReleaseTrack.ALPHA:
              '00gjdgxs2tpop48',
      },
      OperatingSystem.WINDOWS: {
          # group1@cloudsdk-gcp04.gen.atc-test.dev
          calliope_base.ReleaseTrack.ALPHA:
              '01y810tw2x01afx',
      }
  }

  def _GetOperationResponseProperty(self, response, key):
    return next((p.value.string_value
                 for p in response.additionalProperties
                 if p.key == key), None)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SetUpSharding()
    self.SetUpAccessLevels()

  def SetUpSharding(self):
    self._current_org = self.SHARDING_ORG.get(OperatingSystem.Current(),
                                              {}).get(self.track, {})
    self._current_billing_project = self.SHARDING_QUOTA_PROJECT.get(
        OperatingSystem.Current(), {}).get(self.track, {})

  def SetUpAccessLevels(self):
    self._group = self.GROUP.get(OperatingSystem.Current(),
                                 {}).get(self.track, {})
    self._access_level_1 = self.ACCESS_LEVEL_1.get(OperatingSystem.Current(),
                                                   {}).get(self.track, {})
    self._access_level_2 = self.ACCESS_LEVEL_2.get(OperatingSystem.Current(),
                                                   {}).get(self.track, {})

  @contextlib.contextmanager
  def _SetBillingProject(self):
    properties.VALUES.billing.quota_project.Set(self._current_billing_project)
    try:
      yield
    finally:
      properties.VALUES.billing.quota_project.Set(None)

  @contextlib.contextmanager
  def _SetOrganizationProperty(self, org):
    properties.VALUES.access_context_manager.organization.Set(org)
    try:
      yield
    finally:
      properties.VALUES.access_context_manager.policy.Set(None)

  @contextlib.contextmanager
  def _CreateCloudAccessBinding(self, group_key, access_level):
    binding_name = None
    try:
      result = self.Run('access-context-manager cloud-bindings create '
                        '    --group-key {}'
                        '    --level {}'.format(group_key, access_level))
      binding_name = self._GetOperationResponseProperty(result, 'name')
      yield binding_name
    finally:
      self.Run('access-context-manager cloud-bindings delete '
               '    --quiet '
               '    --binding {}'.format(binding_name))

  def _DescribeCloudAccessBinding(self, binding_name):
    return self.Run('access-context-manager cloud-bindings describe '
                    '    --binding {}'.format(binding_name))

  def _UpdateCloudAccessBinding(self, binding_name, access_level):
    return self.Run('access-context-manager cloud-bindings update '
                    '    --binding {}'
                    '    --level {}'.format(binding_name, access_level))

  def _ListCloudAccessBinding(self):
    return list(
        self.Run('access-context-manager cloud-bindings list '
                 '    --format disable '
                 '    --organization {}'.format(self._current_org)))

  def testAccessContextManagerCloudBindings(self):
    org_id = self._current_org
    with self._SetOrganizationProperty(org_id):
      with self._SetBillingProject():
        with self._CreateCloudAccessBinding(
            self._group, self._access_level_1) as binding_name:
          binding = self._DescribeCloudAccessBinding(binding_name)
          self.assertEqual(binding.groupKey, self._group)
          self.assertEqual(binding.accessLevels, [self._access_level_1])
          self._UpdateCloudAccessBinding(binding_name, self._access_level_2)
          binding = self._DescribeCloudAccessBinding(binding_name)
          self.assertEqual(binding.groupKey, self._group)
          self.assertEqual(binding.accessLevels, [self._access_level_2])
          binding = self._ListCloudAccessBinding()
          self.assertEqual(binding[0].groupKey, self._group)
          self.assertEqual(binding[0].accessLevels, [self._access_level_2])
