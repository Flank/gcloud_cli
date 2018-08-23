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

import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class ResourcePoliciesTest(e2e_test_base.BaseTest):
  """Resource policies tests."""

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', 'alpha')

  def _GetResourceName(self):
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test'))

  @contextlib.contextmanager
  def _CreateInstance(self):
    instance_name = self._GetResourceName()
    try:
      self.Run('compute instances create {0} --zone {1}'
               .format(instance_name, self.zone))
      self.Run('compute instances list')
      self.AssertNewOutputContains(instance_name)
      yield instance_name
    finally:
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))

  @contextlib.contextmanager
  def _CreateVmMaintenancePolicy(self):
    policy_name = self._GetResourceName()
    try:
      self.Run('compute resource-policies create-vm-maintenance {0} '
               '--region {1} --start-time 04:00Z --daily-window'.format(
                   policy_name, self.region))
      self.Run('compute resource-policies list')
      self.AssertNewOutputContains(policy_name)
      yield policy_name
    finally:
      self.Run('compute resource-policies delete {0} --region {1} '
               '--quiet'.format(policy_name, self.region))

  def _TestAddPolicyAndDescribeInstance(self, instance_name, policy_name):
    self.Run('compute instances add-resource-policies {0} --zone {1} '
             '--resource-policies {2}'.format(
                 instance_name, self.zone, policy_name))
    self.Run('compute instances describe {0} --zone {1}'
             .format(instance_name, self.zone))
    self.AssertNewOutputContains(
        'https://www.googleapis.com/compute/alpha/projects/{0}/regions/{1}/'
        'resourcePolicies/{2}'.format(self.Project(), self.region, policy_name))

  def testResourcePolicy(self):
    with self._CreateVmMaintenancePolicy() as policy_name:
      with self._CreateInstance() as instance_name:
        self._TestAddPolicyAndDescribeInstance(instance_name, policy_name)
