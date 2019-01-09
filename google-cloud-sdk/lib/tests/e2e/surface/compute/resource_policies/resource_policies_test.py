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
"""Integration tests for resource policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class ResourcePoliciesTest(e2e_test_base.BaseTest):
  """Resource policies tests."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', 'alpha')

  @staticmethod
  def _GetResourceName():
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test'))

  def testCreateBackupSchedulePolicy(self):
    policy_name = self._GetResourceName()
    try:
      self.Run('compute resource-policies create-backup-schedule {0} '
               '--region {1} --start-time 04:00Z --hourly-schedule 2 '
               '--max-retention-days 1 '
               '--on-source-disk-delete apply-retention-policy'.format(
                   policy_name, self.region))
      self.Run('compute resource-policies describe {0} --region {1}'.format(
          policy_name, self.region))
      self.AssertNewOutputContains('APPLY_RETENTION_POLICY')
    finally:
      self.Run('compute resource-policies delete {0} --region {1} '
               '--quiet'.format(policy_name, self.region))
